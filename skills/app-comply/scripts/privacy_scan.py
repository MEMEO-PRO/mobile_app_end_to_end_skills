#!/usr/bin/env python3
"""Two-store privacy pre-review.

Scans a project's dependencies, permissions and network hosts, then drafts:
  - docs/data-inventory draft rows
  - the Google Play Data safety form answers
  - Apple App Store privacy nutrition labels
  - the iOS privacy-manifest required-reason API list
and compares them with the project's own docs/data-inventory.md, flagging every
SDK, data item or host the inventory does not mention.

Usage:
  privacy_scan.py PROJECT [--out reports/] [--json reports/privacy-scan.json] [--inventory docs/data-inventory.md]
Exit: 0 pass/warn, 1 fail (missing inventory or undeclared SDK / data / host), 2 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _project import Project, emit, read, result  # noqa: E402

CATALOG = Path(__file__).resolve().parent.parent / "data" / "sdk-catalog.json"
ATT_KEY = "NSUserTrackingUsageDescription"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def resolve(sdks: dict, name: str) -> dict | None:
    entry = sdks.get(name)
    if entry and "alias" in entry:
        entry = sdks.get(entry["alias"])
    return entry


def scan(project: Project, catalog: dict) -> dict:
    sdks = catalog["sdks"]
    found_sdks, items = [], {}
    required_reason = set()
    known_domains: dict[str, str] = {}
    for dep in sorted(project.runtime_deps):
        entry = resolve(sdks, dep)
        if not entry:
            continue
        found_sdks.append({"package": dep, "name": entry["name"], "tracking": entry.get("tracking", False),
                           "ai": entry.get("ai", False), "on_device": entry.get("on_device", False),
                           "ships_privacy_manifest": entry.get("privacy_manifest", False)})
        required_reason.update(entry.get("required_reason", []))
        for d in entry.get("domains", []):
            known_domains[d] = entry["name"]
        for d in entry.get("data", []):
            key = d["item"]
            it = items.setdefault(key, {"item": key, "play": d["play"], "apple": d["apple"], "purposes": set(),
                                        "shared": False, "linked": False, "tracking": False, "sources": [],
                                        "notes": set()})
            it["purposes"].update(d["purposes"])
            it["shared"] |= d.get("shared", False)
            it["linked"] |= d.get("linked", False)
            it["tracking"] |= entry.get("tracking", False)
            it["sources"].append(entry["name"])
            if d.get("note"):
                it["notes"].add(d["note"])
    # Permissions imply data the app can reach.
    for perm in sorted(project.permissions()):
        label = catalog["permissions"].get(perm)
        if not label:
            continue
        meta = catalog["items"][label]
        it = items.setdefault(label, {"item": label, "play": meta["play"], "apple": meta["apple"],
                                      "purposes": {"App functionality"}, "shared": False, "linked": True,
                                      "tracking": False, "sources": [], "notes": set()})
        it["sources"].append(f"permission {perm}")
        it["notes"].add("Reachable through a permission: declare it only if it leaves the device")
    # Hosts
    hosts = project.hosts()
    host_rows = []
    for h, files in sorted(hosts.items()):
        owner = next((name for dom, name in known_domains.items() if h == dom or h.endswith("." + dom)), None)
        host_rows.append({"host": h, "sdk": owner, "files": files})
    for it in items.values():
        it["purposes"] = sorted(it["purposes"])
        it["notes"] = sorted(it["notes"])
        it["sources"] = sorted(set(it["sources"]))
    return {"sdks": found_sdks, "items": sorted(items.values(), key=lambda x: x["play"]),
            "hosts": host_rows, "required_reason_apis": sorted(required_reason)}


def compare(scan_res: dict, project: Project, inventory: Path | None) -> list[dict]:
    findings = []
    if inventory is None or not inventory.exists():
        findings.append({"id": "INV-MISSING", "severity": "blocker",
                         "title": "No data inventory (docs/data-inventory.md)",
                         "fix": "Start from reports/data-inventory-draft.md, complete it, save it as docs/data-inventory.md."})
        inv = ""
    else:
        inv = read(inventory).lower()
    if inv:
        for s in scan_res["sdks"]:
            if s["on_device"]:
                continue
            names = {s["name"].lower(), s["package"].lower(), s["name"].split(" (")[0].lower()}
            if not any(n in inv for n in names):
                findings.append({"id": "INV-SDK", "severity": "blocker",
                                 "title": f"SDK {s['name']} ({s['package']}) is not in the data inventory",
                                 "fix": "Add its data items, purposes and destination, then update Data safety and privacy labels."})
        for it in scan_res["items"]:
            if all(src.startswith("permission ") for src in it["sources"]):
                continue
            if it["item"].lower() not in inv:
                findings.append({"id": "INV-ITEM", "severity": "blocker",
                                 "title": f"Data item '{it['item']}' (from {', '.join(it['sources'])}) is not in the data inventory",
                                 "fix": f"Add a row: Play '{it['play']}', Apple '{it['apple']}'."})
        for h in scan_res["hosts"]:
            if h["host"] not in inv and not (h["sdk"] and h["sdk"].lower() in inv):
                findings.append({"id": "INV-HOST", "severity": "blocker",
                                 "title": f"Host {h['host']} is called from {', '.join(h['files'][:3])} but not listed in the inventory",
                                 "fix": "List the host under 'Sent to', or remove the call."})
    # Tracking / ATT
    trackers = [s["name"] for s in scan_res["sdks"] if s["tracking"]]
    if trackers:
        has_att = ATT_KEY in project.all_config() or "expo-tracking-transparency" in project.deps
        findings.append({"id": "ATT", "severity": "pass" if has_att else "blocker",
                         "title": f"Tracking SDKs ({', '.join(trackers)}) {'with' if has_att else 'without'} App Tracking Transparency",
                         "fix": "Add expo-tracking-transparency, request permission before the SDK starts, mark the data 'Used for tracking' in Apple labels."})
    # AI providers
    ai = [s["name"] for s in scan_res["sdks"] if s["ai"]]
    if ai:
        consent = project.grep(r"ai[ _-]?consent|aiConsent|AI disclosure|share.{0,40}with.{0,40}(openai|anthropic|gemini|ai provider)")
        findings.append({"id": "AI-CONSENT", "severity": "pass" if consent else "blocker",
                         "title": f"AI provider SDK ({', '.join(ai)}) {'with' if consent else 'without'} a consent screen",
                         "fix": "Show a screen naming the provider and data types and ask before sending (Apple 5.1.2(i)); prefer calling the AI from your server."})
    # Privacy manifest
    if project.is_expo or project.plists:
        cfg = project.all_config()
        manifest_files = [p for p in project.root.rglob("PrivacyInfo.xcprivacy") if "node_modules" not in p.parts]
        text = cfg + "".join(read(p) for p in manifest_files)
        if "NSPrivacyAccessedAPITypes" not in text and "privacyManifests" not in text:
            findings.append({"id": "PM-MISSING", "severity": "blocker", "title": "No iOS privacy manifest",
                             "fix": "Add ios.privacyManifests (Expo) or PrivacyInfo.xcprivacy with the APIs listed in reports/privacy-labels-draft.md."})
        else:
            missing = [r for r in scan_res["required_reason_apis"] if r not in text]
            for r in missing:
                findings.append({"id": "PM-REASON", "severity": "warning",
                                 "title": f"{r} not declared in your privacy manifest",
                                 "fix": "Usually covered by the SDK's own manifest; declare it yourself if your code calls the API directly."})
        for s in scan_res["sdks"]:
            if not s["ships_privacy_manifest"] and not s["on_device"]:
                findings.append({"id": "PM-SDK", "severity": "warning",
                                 "title": f"{s['name']} may not ship its own iOS privacy manifest",
                                 "fix": "Check the SDK release notes; declare its data and APIs in your app's manifest if it doesn't."})
    if not [f for f in findings if f["severity"] in ("blocker", "warning")]:
        findings.append({"id": "PRIVACY", "severity": "pass", "title": "Inventory, SDKs and hosts agree"})
    return findings


def md_inventory(s: dict) -> str:
    rows = ["| # | Data item | Play category / Apple type | Purpose(s) | Collected by | Shared with third party? | Linked to user? | Used for tracking? | Notes |",
            "|---|---|---|---|---|---|---|---|---|"]
    for i, it in enumerate(s["items"], 1):
        rows.append(f"| {i} | {it['item']} | {it['play']} / {it['apple']} | {', '.join(it['purposes'])} | "
                    f"{', '.join(it['sources'])} | {'Yes' if it['shared'] else 'No'} | {'Yes' if it['linked'] else 'No'} | "
                    f"{'Yes' if it['tracking'] else 'No'} | {'; '.join(it['notes'])} |")
    hosts = ["| Host | SDK | Called from |", "|---|---|---|"] + [
        f"| {h['host']} | {h['sdk'] or 'your code / unknown'} | {', '.join(h['files'][:3])} |" for h in s["hosts"]]
    return ("# Data inventory draft (generated)\n\nGenerated by app-comply privacy_scan.py. Fill in retention, deletion path and "
            "lawful basis, check every row against your real configuration, then save as docs/data-inventory.md.\n\n"
            "## Data items\n\n" + "\n".join(rows) + "\n\n## Network destinations\n\n" + "\n".join(hosts) + "\n")


def md_data_safety(s: dict) -> str:
    out = ["# Google Play Data safety draft (generated)", "",
           "Play Console → App content → Data safety. Answer per data type. 'Shared' means transferred to a third party that is not your service provider.", "",
           "| Data type | Collected | Shared | Optional? | Purposes | Source |", "|---|---|---|---|---|---|"]
    for it in s["items"]:
        out.append(f"| {it['play']} | Yes | {'Yes' if it['shared'] else 'No'} | decide | {', '.join(it['purposes'])} | {', '.join(it['sources'])} |")
    out += ["", "Security practices: data encrypted in transit — Yes if every host above is HTTPS. "
            "Users can request deletion — must be Yes if accounts exist (in-app + web URL)."]
    return "\n".join(out) + "\n"


def md_labels(s: dict) -> str:
    apple_purpose = {"Advertising or marketing": "Third-Party Advertising", "Analytics": "Analytics",
                     "App functionality": "App Functionality", "Account management": "App Functionality",
                     "Developer communications": "Developer's Advertising or Marketing",
                     "Fraud prevention, security, and compliance": "App Functionality",
                     "Personalization": "Product Personalization"}
    out = ["# Apple privacy nutrition labels draft (generated)", "",
           "App Store Connect → App Privacy. One entry per data type.", "",
           "| Data type | Purposes | Linked to user | Used for tracking | Source |", "|---|---|---|---|---|"]
    for it in s["items"]:
        purposes = sorted({apple_purpose.get(p, "Other Purposes") for p in it["purposes"]})
        out.append(f"| {it['apple']} | {', '.join(purposes)} | {'Yes' if it['linked'] else 'No'} | "
                   f"{'Yes' if it['tracking'] else 'No'} | {', '.join(it['sources'])} |")
    out += ["", "## Privacy manifest (PrivacyInfo.xcprivacy / ios.privacyManifests)", "",
            "Required-reason API categories used by your SDKs (most ship their own manifest; declare any your own code calls):", ""]
    out += [f"- {r}" for r in s["required_reason_apis"]] or ["- none detected"]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--out", default=None, help="directory for the Markdown drafts (default PROJECT/reports)")
    ap.add_argument("--json", dest="json_path", default=None)
    ap.add_argument("--inventory", default=None, help="default PROJECT/docs/data-inventory.md")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if not Path(a.project).is_dir():
        print(f"Not a directory: {a.project}", file=sys.stderr)
        return 2
    project = Project(a.project)
    s = scan(project, load_catalog())
    inv = Path(a.inventory) if a.inventory else project.root / "docs" / "data-inventory.md"
    findings = compare(s, project, inv)
    out = Path(a.out) if a.out else project.root / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "data-inventory-draft.md").write_text(md_inventory(s), encoding="utf-8")
    (out / "data-safety-draft.md").write_text(md_data_safety(s), encoding="utf-8")
    (out / "privacy-labels-draft.md").write_text(md_labels(s), encoding="utf-8")
    res = result("privacy_scan", findings, extra={"scan": s, "drafts": [str(out / n) for n in (
        "data-inventory-draft.md", "data-safety-draft.md", "privacy-labels-draft.md")]})
    if not a.quiet:
        print(f"SDKs: {', '.join(x['name'] for x in s['sdks']) or 'none recognised'}")
        print(f"Data items: {len(s['items'])} · hosts: {len(s['hosts'])} · drafts written to {out}\n")
    return emit(res, a.json_path, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
