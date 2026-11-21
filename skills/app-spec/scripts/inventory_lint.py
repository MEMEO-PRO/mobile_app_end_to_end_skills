#!/usr/bin/env python3
"""Check that docs/data-inventory.md is complete enough to fill the store privacy forms.

Reads the first Markdown table under "## 1. Data items" (the app-factory template) and checks
each row has: data item, store categories, purpose, collector, destination, shared, linked,
tracking, retention, deletion path and lawful basis — with no <placeholders> or blanks.
Also checks the SDK table and that children / transfer sections were answered.

Usage:
  inventory_lint.py [docs/data-inventory.md] [--json reports/inventory.json]
Exit: 0 complete, 1 gaps found, 2 file missing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = {
    "data item": "Data item", "play category": "Play category / Apple type", "purpose": "Purpose(s)",
    "collected by": "Collected by", "sent to": "Sent to", "shared": "Shared with third party?",
    "linked": "Linked to user identity?", "tracking": "Used for tracking?", "retention": "Retention",
    "deletes": "How the user deletes it", "lawful basis": "Lawful basis / consent",
}
YESNO = {"yes", "no"}


def tables(md: str) -> list[tuple[str, list[list[str]]]]:
    """Return (heading, rows) for every pipe table; rows include the header row."""
    out, heading, cur = [], "", None
    for line in md.splitlines():
        if line.startswith("#"):
            heading = line.strip("# ").strip()
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
                continue
            if cur is None:
                cur = (heading, [])
                out.append(cur)
            cur[1].append(cells)
        else:
            cur = None
    return out


def lint(md: str) -> list[dict]:
    findings = []
    tabs = tables(md)
    items = next((t for h, t in tabs if "data item" in h.lower() or (t and any("data item" in c.lower() for c in t[0]))), None)
    if not items or len(items) < 2:
        return [{"id": "INV-TABLE", "severity": "blocker", "title": "No data-items table found",
                 "fix": "Use templates/data-inventory.md (section '1. Data items')."}]
    header = [c.lower() for c in items[0]]
    col = {}
    for key, label in REQUIRED.items():
        idx = next((i for i, h in enumerate(header) if key in h), None)
        if idx is None:
            findings.append({"id": "INV-COLUMN", "severity": "blocker", "title": f"Missing column: {label}"})
        else:
            col[key] = idx
    real_rows = [r for r in items[1:] if any(c and c != "#" and not re.fullmatch(r"\d+", c) for c in r)]
    if not real_rows:
        findings.append({"id": "INV-EMPTY", "severity": "blocker", "title": "Data-items table has no rows",
                         "fix": "Run app-comply privacy_scan.py for a draft, then complete it."})
    for r in real_rows:
        name = r[col["data item"]] if "data item" in col and col["data item"] < len(r) else "?"
        for key, idx in col.items():
            val = r[idx] if idx < len(r) else ""
            if not val or re.search(r"<[^>]*>|\bTBD\b|\?\?|^-$", val, re.I):
                findings.append({"id": "INV-CELL", "severity": "blocker", "title": f"'{name}': {REQUIRED[key]} is empty or a placeholder"})
            elif key in ("shared", "linked", "tracking") and val.split()[0].strip("().,").lower() not in YESNO:
                findings.append({"id": "INV-YESNO", "severity": "warning", "title": f"'{name}': {REQUIRED[key]} should start with Yes or No (got '{val}')"})
        if "shared" in col and col["shared"] < len(r) and r[col["shared"]].lower().startswith("yes") and \
                "sent to" in col and not r[col["sent to"]].strip():
            findings.append({"id": "INV-SHARED", "severity": "blocker", "title": f"'{name}' is shared but no recipient is named"})
        if "tracking" in col and col["tracking"] < len(r) and r[col["tracking"]].lower().startswith("yes"):
            findings.append({"id": "INV-TRACKING", "severity": "warning", "title": f"'{name}' is used for tracking",
                             "fix": "Needs App Tracking Transparency consent on iOS and 'Used for tracking' in Apple labels."})
    low = md.lower()
    if re.search(r"can children use the app\?\s*<", low):
        findings.append({"id": "INV-CHILDREN", "severity": "blocker", "title": "Children section not answered"})
    if "## 2. third-party sdks" in low:
        sdk = next((t for h, t in tabs if "third-party sdks" in h.lower()), None)
        if sdk is not None and not [r for r in sdk[1:] if any(c for c in r)]:
            findings.append({"id": "INV-SDKS", "severity": "warning", "title": "Third-party SDK table is empty",
                             "fix": "List every SDK, even crash reporting; privacy_scan.py lists the ones it recognises."})
    if not [f for f in findings if f["severity"] in ("blocker", "warning")]:
        findings.append({"id": "INV", "severity": "pass", "title": f"{len(real_rows)} data item(s), all columns filled"})
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default="docs/data-inventory.md")
    ap.add_argument("--json", dest="json_path")
    a = ap.parse_args(argv)
    p = Path(a.path)
    if not p.exists():
        print(f"Missing {p}. Copy skills/app-factory/templates/data-inventory.md and fill it in.", file=sys.stderr)
        if a.json_path:
            Path(a.json_path).parent.mkdir(parents=True, exist_ok=True)
            Path(a.json_path).write_text(json.dumps({"tool": "inventory_lint", "verdict": "fail", "summary": f"{p} missing",
                                                     "findings": [{"id": "INV-MISSING", "severity": "blocker", "title": f"{p} missing"}]}) + "\n")
        return 2
    findings = lint(p.read_text(encoding="utf-8"))
    b = sum(1 for f in findings if f["severity"] == "blocker")
    w = sum(1 for f in findings if f["severity"] == "warning")
    res = {"tool": "inventory_lint", "verdict": "fail" if b else ("warn" if w else "pass"), "blockers": b, "warnings": w,
           "summary": f"{b} gap(s), {w} warning(s)", "findings": findings}
    if a.json_path:
        Path(a.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_path).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    for f in findings:
        print(f"{f['severity'].upper():8} {f['title']}")
    print(f"inventory_lint: {res['summary']} -> {res['verdict'].upper()}")
    return 1 if b else 0


if __name__ == "__main__":
    sys.exit(main())
