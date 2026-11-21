#!/usr/bin/env python3
"""Turn an agent's exploratory-testing log into Maestro repro flows and a bug report.

An agent drives the app through mobile-mcp (or adb / simctl) and records every step
in a JSON log (format in skills/app-test/SKILL.md). This script writes:
  - one Maestro flow per issue, replaying the steps from the last app launch up to the issue
  - bug-report.md with severity, steps, device and evidence
  - coverage: screens visited vs. the screens you expected

Usage:
  explore_to_maestro.py LOG.json [--out .maestro/repro] [--report reports/bug-report.md]
                        [--expect-screens Home,Settings,...] [--json reports/explore.json]
Exit: 0 no crash/ANR, 1 crash or ANR found (or expected screens never reached), 2 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY = {"crash": "P0", "anr": "P0", "data_loss": "P0", "error": "P1", "security": "P1",
            "accessibility": "P2", "ui": "P2", "copy": "P3"}


def yq(s: str) -> str:
    return json.dumps(str(s), ensure_ascii=False)


def step_to_maestro(step: dict) -> list[str]:
    a = step.get("action")
    if a == "launch":
        return ["- launchApp:", "    clearState: true"] if step.get("clear_state", True) else ["- launchApp"]
    if a == "tap":
        if step.get("id"):
            return ["- tapOn:", f"    id: {yq(step['id'])}"]
        if step.get("text"):
            return [f"- tapOn: {yq(step['text'])}"]
        if step.get("point"):
            x, y = step["point"]
            return ["- tapOn:", f"    point: {yq(f'{x},{y}')}"]
    if a == "long_press":
        target = f"    id: {yq(step['id'])}" if step.get("id") else f"    text: {yq(step.get('text', ''))}"
        return ["- longPressOn:", target]
    if a == "type":
        return [f"- inputText: {yq(step.get('text', ''))}"]
    if a == "erase":
        return [f"- eraseText: {int(step.get('count', 50))}"]
    if a == "swipe":
        return ["- swipe:", f"    direction: {step.get('direction', 'UP').upper()}"]
    if a == "scroll":
        return ["- scroll"]
    if a == "back":
        return ["- back"]
    if a == "hide_keyboard":
        return ["- hideKeyboard"]
    if a == "wait":
        return [f"- waitForAnimationToEnd:", f"    timeout: {int(step.get('ms', 3000))}"]
    if a == "assert":
        return [f"- assertVisible: {yq(step.get('text', ''))}"]
    if a == "open_link":
        return [f"- openLink: {yq(step.get('url', ''))}"]
    if a in ("screenshot", "observe"):
        return []
    return [f"# unsupported action: {a}"]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "issue"


def build(log: dict, out_dir: Path, expect: list[str]) -> dict:
    app_id = log.get("app_id") or log.get("appId")
    if not app_id:
        raise ValueError("log needs app_id")
    steps = log.get("steps", [])
    issues, screens, last_launch = [], [], 0
    for idx, st in enumerate(steps):
        if st.get("action") == "launch":
            last_launch = idx
        if st.get("screen") and st["screen"] not in screens:
            screens.append(st["screen"])
        ev = st.get("event")
        if not ev:
            continue
        kind = ev.get("type", "error").lower()
        replay = steps[last_launch: idx + 1] if steps and steps[last_launch].get("action") == "launch" \
            else [{"action": "launch"}] + steps[: idx + 1]
        n = len(issues) + 1
        name = f"{n:02d}-{kind}-{slug(ev.get('message', kind))}"
        lines = [f"appId: {app_id}", f"name: {yq('Repro ' + str(n) + ': ' + ev.get('message', kind))}",
                 f"tags:\n  - repro\n  - {kind}", "---"]
        for s in replay:
            lines += step_to_maestro(s)
        if ev.get("expected_text"):
            lines.append(f"- assertVisible: {yq(ev['expected_text'])}   # expected; fails while the bug exists")
        elif kind in ("crash", "anr"):
            lines.append("- assertVisible:\n    id: \".*\"   # app must still be on screen; fails while it crashes")
        out_dir.mkdir(parents=True, exist_ok=True)
        flow = out_dir / f"{name}.yaml"
        flow.write_text("\n".join(lines) + "\n", encoding="utf-8")
        issues.append({"n": n, "type": kind, "severity": SEVERITY.get(kind, "P2"), "message": ev.get("message", ""),
                       "screen": st.get("screen") or (screens[-1] if screens else ""), "step": idx,
                       "evidence": ev.get("screenshot") or ev.get("log"), "flow": str(flow),
                       "steps": [describe(s) for s in replay]})
    missing = [s for s in expect if s not in screens]
    return {"app_id": app_id, "platform": log.get("platform", ""), "device": log.get("device", ""),
            "build": log.get("build", ""), "issues": issues, "screens": screens, "missing_screens": missing,
            "steps": len(steps)}


def describe(s: dict) -> str:
    a = s.get("action")
    target = s.get("text") or s.get("id") or s.get("url") or s.get("direction") or (f"{s['point']}" if s.get("point") else "")
    return f"{a} {target}".strip()


def report_md(r: dict) -> str:
    lines = [f"# Exploratory test report — {r['app_id']}", "",
             f"Platform: {r['platform'] or 'n/a'} · Device: {r['device'] or 'n/a'} · Build: {r['build'] or 'n/a'} · "
             f"Steps: {r['steps']} · Screens visited: {len(r['screens'])}", ""]
    if r["missing_screens"]:
        lines += [f"**Not reached:** {', '.join(r['missing_screens'])}", ""]
    lines += ["| # | Severity | Type | Screen | Summary | Repro flow |", "|---|---|---|---|---|---|"]
    for i in r["issues"]:
        lines.append(f"| {i['n']} | {i['severity']} | {i['type']} | {i['screen']} | {i['message']} | `{i['flow']}` |")
    if not r["issues"]:
        lines.append("| – | – | – | – | No issues found | – |")
    for i in r["issues"]:
        lines += ["", f"## {i['n']}. {i['message'] or i['type']} ({i['severity']})", "", "Steps:", ""]
        lines += [f"{k}. {s}" for k, s in enumerate(i["steps"], 1)]
        if i["evidence"]:
            lines += ["", f"Evidence: {i['evidence']}"]
        lines += ["", f"Reproduce: `maestro test {i['flow']}`"]
    lines += ["", "## Screens visited", "", ", ".join(r["screens"]) or "none recorded"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("--out", default=".maestro/repro")
    ap.add_argument("--report", default="reports/bug-report.md")
    ap.add_argument("--expect-screens", default="")
    ap.add_argument("--json", dest="json_path")
    a = ap.parse_args(argv)
    try:
        log = json.loads(Path(a.log).read_text(encoding="utf-8"))
        r = build(log, Path(a.out), [s.strip() for s in a.expect_screens.split(",") if s.strip()])
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(report_md(r), encoding="utf-8")
    p0 = [i for i in r["issues"] if i["severity"] == "P0"]
    verdict = "fail" if p0 or r["missing_screens"] else ("warn" if r["issues"] else "pass")
    out = {"tool": "explore", "verdict": verdict, "blockers": len(p0) + len(r["missing_screens"]),
           "warnings": len(r["issues"]) - len(p0),
           "summary": f"{len(r['issues'])} issue(s), {len(p0)} crash/ANR, {len(r['screens'])} screens"
                      + (f", not reached: {', '.join(r['missing_screens'])}" if r["missing_screens"] else ""),
           "findings": [{"id": f"EXPLORE-{i['n']}", "severity": "blocker" if i["severity"] == "P0" else "warning",
                         "title": f"{i['type']}: {i['message']}", "fix": f"maestro test {i['flow']}"} for i in r["issues"]],
           "report": r}
    if a.json_path:
        Path(a.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_path).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"{out['summary']} -> {verdict.upper()}\nreport: {a.report}\nflows: {a.out}")
    return 1 if verdict == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
