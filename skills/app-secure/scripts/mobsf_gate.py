#!/usr/bin/env python3
"""Security gate: run a MobSF static scan and map findings to OWASP MASVS groups.

Online mode uploads the release .aab/.apk/.ipa to a MobSF server (REST API v1),
scans it, downloads the JSON report and gates on severity. Offline mode reads a
report you already have.

  # start MobSF:  docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest
  export MOBSF_API_KEY=...            # shown on the MobSF API docs page
  mobsf_gate.py --file app.aab [--server http://127.0.0.1:8000] [--max-high 0] [--min-score 50]
  mobsf_gate.py --report mobsf-report.json            # offline

Writes reports/security.json and reports/security.md (use --json / --md to change).
Exit: 0 pass, 1 gate failed, 2 usage / connection error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

GROUPS = ["STORAGE", "CRYPTO", "AUTH", "NETWORK", "PLATFORM", "CODE", "RESILIENCE", "PRIVACY"]
KEYWORDS = [
    ("NETWORK", r"cleartext|ssl|tls|certificate|pinning|trustmanager|hostname|http\b|network security|insecure connection|ats\b|arbitrary loads"),
    ("CRYPTO", r"crypt|cipher|ecb|md5|sha-?1|random|key ?store|hardcoded key|iv\b|keychain access"),
    ("STORAGE", r"storage|shared ?pref|sqlite|log(ging)?\b|backup|clipboard|external storage|world readable|cache|temp file|nsuserdefaults"),
    ("AUTH", r"auth|biometric|password|session|credential|token"),
    ("PLATFORM", r"exported|intent|webview|javascript ?interface|deep ?link|content provider|broadcast|activity|service|taskaffinity|url scheme|pasteboard|screenshot|flag_secure"),
    ("RESILIENCE", r"root|jailbreak|debugg|tamper|obfuscat|emulator|frida|anti-?debug|pie\b|stack canary|nx\b|rpath|stripped"),
    ("PRIVACY", r"tracker|privacy|personal data|pii|location|contacts|camera|microphone|advertising id|permission"),
    ("CODE", r".*"),
]
SEV_ORDER = {"high": 3, "warning": 2, "medium": 2, "info": 1, "low": 1, "secure": 0, "good": 0, "hotspot": 1}


def masvs_group(text: str, explicit: str | None = None) -> str:
    if explicit:
        m = re.search(r"(?:MASVS|MSTG)-([A-Z]+)", explicit.upper())
        if m:
            g = {"ARCH": "CODE", "RESILIENCE": "RESILIENCE"}.get(m.group(1), m.group(1))
            if g in GROUPS:
                return g
    for g, rx in KEYWORDS:
        if re.search(rx, text, re.I):
            return g
    return "CODE"


def normalise(report: dict) -> list[dict]:
    """Collect findings from the parts of a MobSF report that carry severities."""
    found = []

    def add(title, severity, desc="", section="", masvs=None):
        sev = str(severity or "info").lower()
        sev = {"error": "high", "critical": "high", "medium": "warning", "low": "info"}.get(sev, sev)
        if sev in ("secure", "good"):
            return
        found.append({"title": str(title).strip()[:200], "severity": sev, "section": section,
                      "masvs": masvs_group(f"{title} {desc} {section}", masvs), "description": str(desc).strip()[:400]})

    appsec = report.get("appsec") or {}
    if appsec:
        for sev in ("high", "warning", "info", "hotspot"):
            for item in appsec.get(sev, []) or []:
                add(item.get("title", ""), sev, item.get("description", ""), item.get("section", ""))
        return dedupe(found)
    code = (report.get("code_analysis") or {}).get("findings") or {}
    for rule, data in code.items():
        meta = data.get("metadata", {})
        add(meta.get("description", rule), meta.get("severity"), meta.get("description", ""), "code",
            meta.get("masvs") or meta.get("owasp-masvs"))
    for item in (report.get("manifest_analysis") or {}).get("manifest_findings", []) or []:
        add(item.get("title") or item.get("rule", ""), item.get("severity"), item.get("description", ""), "manifest")
    for item in (report.get("network_security") or {}).get("network_findings", []) or []:
        add(item.get("description", "")[:120], item.get("severity"), item.get("description", ""), "network")
    for item in (report.get("certificate_analysis") or {}).get("certificate_findings", []) or []:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            add(item[2], item[0], item[1], "certificate")
    binary = report.get("binary_analysis") or []
    if isinstance(binary, list):
        for item in binary:
            for key, val in (item.items() if isinstance(item, dict) else []):
                if isinstance(val, dict) and "severity" in val:
                    add(f"{key}: {val.get('description', '')[:80]}", val["severity"], val.get("description", ""), "binary")
    for t in (report.get("trackers") or {}).get("trackers", []) or []:
        add(f"Tracker: {t.get('name')}", "info", ", ".join(t.get("categories", [])) if isinstance(t.get("categories"), list) else t.get("categories", ""), "privacy", "MASVS-PRIVACY")
    return dedupe(found)


def dedupe(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for i in items:
        k = (i["title"], i["severity"])
        if k not in seen:
            seen.add(k)
            out.append(i)
    return sorted(out, key=lambda x: -SEV_ORDER.get(x["severity"], 0))


def score_of(report: dict) -> int | None:
    v = (report.get("appsec") or {}).get("security_score", report.get("security_score"))
    return int(v) if isinstance(v, (int, float)) else None


# ---------- MobSF REST client ----------
class MobSF:
    def __init__(self, server: str, key: str):
        self.server, self.key = server.rstrip("/"), key

    def _post(self, path: str, data: bytes, ctype: str, timeout=900) -> dict:
        req = urllib.request.Request(self.server + path, data=data, method="POST",
                                     headers={"Authorization": self.key, "X-Mobsf-Api-Key": self.key, "Content-Type": ctype})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8") or "{}")

    def form(self, path: str, fields: dict) -> dict:
        body = urllib.parse.urlencode(fields).encode()
        return self._post(path, body, "application/x-www-form-urlencoded")

    def upload(self, file: Path) -> dict:
        boundary = uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{file.name}\"\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n").encode() + file.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        return self._post("/api/v1/upload", body, f"multipart/form-data; boundary={boundary}")

    def scan_and_report(self, file: Path) -> dict:
        up = self.upload(file)
        h = up.get("hash")
        if not h:
            raise RuntimeError(f"upload failed: {up}")
        self.form("/api/v1/scan", {"hash": h, "scan_type": up.get("scan_type", ""), "file_name": up.get("file_name", file.name)})
        rep = self.form("/api/v1/report_json", {"hash": h})
        try:
            sc = self.form("/api/v1/scorecard", {"hash": h})
            if isinstance(sc, dict) and sc:
                rep.setdefault("appsec", sc)
        except urllib.error.HTTPError:
            pass
        return rep



def to_markdown(findings: list[dict], score, verdict: str, limits: dict) -> str:
    by = {g: [f for f in findings if f["masvs"] == g] for g in GROUPS}
    rows = ["| MASVS group | High | Warning | Info |", "|---|---|---|---|"]
    for g in GROUPS:
        c = lambda s: sum(1 for f in by[g] if f["severity"] == s)
        rows.append(f"| MASVS-{g} | {c('high')} | {c('warning')} | {c('info') + c('hotspot')} |")
    lines = [f"# Security gate: {verdict.upper()}", "",
             f"MobSF security score: {score if score is not None else 'n/a'} · limits: max high {limits['max_high']}, "
             f"min score {limits['min_score']}", "", *rows, "", "## High and warning findings", ""]
    for f in findings:
        if f["severity"] in ("high", "warning"):
            lines.append(f"- **{f['severity'].upper()}** [MASVS-{f['masvs']}] {f['title']}")
    if lines[-1] == "":
        lines.append("- none")
    lines += ["", "Fix highs, re-scan the same release build, and record accepted warnings with a reason in the release report."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="release .apk/.aab/.ipa to scan")
    src.add_argument("--report", help="existing MobSF JSON report (offline)")
    ap.add_argument("--server", default=os.environ.get("MOBSF_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--api-key", default=os.environ.get("MOBSF_API_KEY"))
    ap.add_argument("--max-high", type=int, default=0)
    ap.add_argument("--min-score", type=int, default=0, help="minimum MobSF security score (0-100); 0 disables")
    ap.add_argument("--json", dest="json_path", default="reports/security.json")
    ap.add_argument("--md", dest="md_path", default="reports/security.md")
    ap.add_argument("--save-report", help="also save the raw MobSF report here")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)

    try:
        if a.report:
            report = json.loads(Path(a.report).read_text(encoding="utf-8"))
        else:
            if not a.api_key:
                print("Set MOBSF_API_KEY or pass --api-key", file=sys.stderr)
                return 2
            if not Path(a.file).exists():
                print(f"File not found: {a.file}", file=sys.stderr)
                return 2
            report = MobSF(a.server, a.api_key).scan_and_report(Path(a.file))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, RuntimeError) as e:
        print(f"MobSF error: {e}", file=sys.stderr)
        return 2
    if a.save_report:
        Path(a.save_report).write_text(json.dumps(report, indent=2), encoding="utf-8")

    findings = normalise(report)
    score = score_of(report)
    highs = sum(1 for f in findings if f["severity"] == "high")
    reasons = []
    if highs > a.max_high:
        reasons.append(f"{highs} high finding(s) > {a.max_high}")
    if a.min_score and score is not None and score < a.min_score:
        reasons.append(f"score {score} < {a.min_score}")
    verdict = "fail" if reasons else ("warn" if any(f["severity"] == "warning" for f in findings) else "pass")
    limits = {"max_high": a.max_high, "min_score": a.min_score}
    out = {"tool": "mobsf_gate", "verdict": verdict, "score": score, "blockers": highs if reasons else 0,
           "warnings": sum(1 for f in findings if f["severity"] == "warning"),
           "summary": "; ".join(reasons) or f"{highs} high, score {score if score is not None else 'n/a'}",
           "by_masvs": {g: sum(1 for f in findings if f["masvs"] == g and f["severity"] in ("high", "warning")) for g in GROUPS},
           "findings": [{"id": f"MASVS-{f['masvs']}", "severity": {"high": "blocker" if reasons else "warning"}.get(f["severity"], "warning" if f["severity"] == "warning" else "info"),
                         "title": f["title"], "mobsf_severity": f["severity"], "section": f["section"]} for f in findings]}
    for path, text in ((a.json_path, json.dumps(out, indent=2) + "\n"), (a.md_path, to_markdown(findings, score, verdict, limits))):
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(text, encoding="utf-8")
    if not a.quiet:
        print(to_markdown(findings, score, verdict, limits))
    return 1 if verdict == "fail" else 0


if __name__ == "__main__":
    sys.exit(main())
