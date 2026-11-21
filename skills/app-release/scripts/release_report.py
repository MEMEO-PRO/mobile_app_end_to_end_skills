#!/usr/bin/env python3
"""Release evidence pack: merge every gate's JSON result into one release-report.md.

Each app-factory tool writes a JSON result ({tool, verdict, summary, findings}) into
reports/. This script maps them to the eight gates, adds the manual checklist the
tools cannot see, and writes reports/release-report.md.

Usage:
  release_report.py [--reports reports] [--out reports/release-report.md] [--version 1.2.0]
                    [--commit SHA] [--manual docs/manual-checks.json] [--json reports/release.json]
Exit: 0 every automated gate passed (warnings allowed), 1 a gate failed or is missing, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

# tool name -> (gate number, gate label, required?)
GATES = {
    "inventory_lint": (1, "Plan: data inventory complete", True),
    "preflight": (3, "Build: preflight scan", True),
    "unit_tests": (4, "Quality: unit + E2E tests", False),
    "explore": (4, "Quality: exploratory test", False),
    "mobsf_gate": (5, "Security: MobSF / MASVS", False),
    "privacy_scan": (6, "Compliance: privacy forms vs code", True),
    "store_policy_check": (6, "Compliance: Play + App Store policy", True),
    "ota_check": (8, "Operate: OTA vs store route", False),
    "testers": (7, "Ship: Play closed test (12 testers × 14 days)", False),
}
MANUAL = [
    (1, "Developer accounts Active; agreements, tax and banking done (Play + Apple)"),
    (2, "Per-country legal table complete; registrations / representatives done (docs/legal.md)"),
    (4, "Release build tested on the device matrix; Play pre-launch report clean"),
    (6, "Play Data safety form and Apple privacy labels entered exactly as reports/*-draft.md"),
    (6, "Privacy policy, terms, account-deletion page and support page live"),
    (6, "Content rating, target audience, ads, permission and category declarations filed"),
    (6, "Demo account works on the live backend; review notes filled"),
    (7, "Store listing text and screenshots final"),
    (8, "Staged rollout plan and vitals alerts set (crash < 1.09%, ANR < 0.47%)"),
]
ICON = {"pass": "PASS", "warn": "PASS (warnings)", "fail": "FAIL", "missing": "NOT RUN"}


def load(reports: Path) -> dict[str, dict]:
    out = {}
    for p in sorted(reports.glob("*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(d, dict) and d.get("tool") in GATES:
            d["_file"] = p.name
            out[d["tool"]] = d
    return out


def git_sha(cwd: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(cwd), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "n/a"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--out", default=None)
    ap.add_argument("--version", default="n/a")
    ap.add_argument("--commit", default=None)
    ap.add_argument("--app", default=None)
    ap.add_argument("--manual", help="JSON {\"<manual item text>\": true} for items already ticked")
    ap.add_argument("--json", dest="json_path")
    a = ap.parse_args(argv)
    reports = Path(a.reports)
    if not reports.is_dir():
        print(f"No reports directory: {reports}", file=sys.stderr)
        return 2
    results = load(reports)
    ticked = json.loads(Path(a.manual).read_text()) if a.manual and Path(a.manual).exists() else {}
    rows, failed = [], []
    for tool, (gate, label, required) in sorted(GATES.items(), key=lambda kv: kv[1][0]):
        r = results.get(tool)
        verdict = r["verdict"] if r else "missing"
        if verdict == "fail" or (verdict == "missing" and required):
            failed.append(label)
        rows.append((gate, label, verdict, r.get("summary", "") if r else ("required" if required else "optional"), r.get("_file", "") if r else ""))
    overall = "BLOCKED" if failed else "READY FOR SUBMISSION (after manual items)"
    app = a.app or reports.resolve().parent.name
    lines = [f"# Release report — {app} {a.version}", "",
             f"Commit: {a.commit or git_sha(reports.resolve().parent)} · Generated: {date.today().isoformat()} · **{overall}**", "",
             "## Automated gates", "", "| Gate | Check | Result | Summary | Evidence |", "|---|---|---|---|---|"]
    for gate, label, verdict, summary, ev in rows:
        lines.append(f"| {gate} | {label} | {ICON[verdict]} | {summary} | {('reports/' + ev) if ev else ''} |")
    lines += ["", "## Blockers", ""]
    blk = [(t, f) for t, r in results.items() for f in r.get("findings", []) if f.get("severity") == "blocker"]
    lines += [f"- [{t}] {f.get('title')}" + (f" — fix: {f['fix']}" if f.get("fix") else "") for t, f in blk] or ["- none"]
    lines += ["", "## Manual checks (store consoles and the real world)", ""]
    lines += [f"- [{'x' if ticked.get(text) else ' '}] Gate {g}: {text}" for g, text in MANUAL]
    manual_items = [f for r in results.values() for f in r.get("findings", []) if f.get("severity") == "manual"]
    lines += [f"- [ ] {f.get('title')}" for f in manual_items]
    lines += ["", "## Warnings accepted for this release", ""]
    warns = [(t, f) for t, r in results.items() for f in r.get("findings", []) if f.get("severity") == "warning"]
    lines += [f"- [{t}] {f.get('title')} — reason: ____" for t, f in warns] or ["- none"]
    out_path = Path(a.out) if a.out else reports / "release-report.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {"tool": "release_report", "verdict": "fail" if failed else "pass", "failed_gates": failed,
               "summary": overall, "report": str(out_path)}
    if a.json_path:
        Path(a.json_path).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"{overall}\n{len(blk)} blocker(s), {len(warns)} warning(s), {len(MANUAL) + len(manual_items)} manual item(s)\nreport: {out_path}")
    for f in failed:
        print(f"  failed or missing: {f}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
