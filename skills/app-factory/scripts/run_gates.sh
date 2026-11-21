#!/usr/bin/env bash
# app-factory: run every automated gate on a project and build the release evidence pack.
#
# Usage:
#   run_gates.sh PROJECT [--skills DIR] [--base GIT_REF] [--artifact app.aab|app.apk]
#                [--mobsf-file app.aab | --mobsf-report report.json] [--explore-log log.json]
#                [--testers testers.csv] [--version 1.0.0]
#
# Writes PROJECT/reports/*.json, drafts, and reports/release-report.md.
# Exit: 0 every required gate passed, 1 a gate failed, 2 usage.
set -u

usage() { sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
[ $# -ge 1 ] || usage
PROJECT="$1"; shift
[ -d "$PROJECT" ] || { echo "Not a directory: $PROJECT" >&2; exit 2; }
SKILLS="$(cd "$(dirname "$0")/../.." && pwd)"
BASE=""; ARTIFACT=""; MOBSF_FILE=""; MOBSF_REPORT=""; EXPLORE=""; TESTERS=""; VERSION="n/a"
while [ $# -gt 0 ]; do
  case "$1" in
    --skills) SKILLS="$(cd "$2" && pwd)"; shift 2 ;;
    --base) BASE="$2"; shift 2 ;;
    --artifact) ARTIFACT="$2"; shift 2 ;;
    --mobsf-file) MOBSF_FILE="$2"; shift 2 ;;
    --mobsf-report) MOBSF_REPORT="$2"; shift 2 ;;
    --explore-log) EXPLORE="$2"; shift 2 ;;
    --testers) TESTERS="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null || { echo "python3 is required" >&2; exit 2; }
PROJECT="$(cd "$PROJECT" && pwd)"
abspath() { [ -z "$1" ] && return 0; [ -e "$1" ] || { echo "Not found: $1" >&2; exit 2; }; echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; }
ARTIFACT="$(abspath "$ARTIFACT")"; MOBSF_FILE="$(abspath "$MOBSF_FILE")"; MOBSF_REPORT="$(abspath "$MOBSF_REPORT")"
EXPLORE="$(abspath "$EXPLORE")"; TESTERS="$(abspath "$TESTERS")"
cd "$PROJECT" || exit 2   # run from the project so reports show project-relative paths
R="reports"; mkdir -p "$R"
rm -f "$R"/*.json
hr() { printf '\n=== %s ===\n' "$1"; }

hr "Gate 1 · data inventory"
"$PY" "$SKILLS/app-spec/scripts/inventory_lint.py" docs/data-inventory.md --json "$R/inventory.json"

hr "Gate 3 · preflight"
bash "$SKILLS/app-factory/scripts/preflight.sh" . > "$R/preflight.txt" 2>&1; PF=$?
cat "$R/preflight.txt"
"$PY" - "$R/preflight.txt" "$PF" "$R/preflight.json" <<'EOF'
import json, re, sys
text = open(sys.argv[1], encoding="utf-8").read()
text = re.sub(r"\x1b\[[0-9;]*m", "", text)
findings, cur = [], None
for line in text.splitlines():
    m = re.match(r"(BLOCKER|WARNING)\s+(.*)", line)
    if m:
        cur = {"id": "PREFLIGHT", "severity": m.group(1).lower(), "title": m.group(2).strip()}
        findings.append(cur)
    elif cur and line.strip().startswith("fix:"):
        cur["fix"] = line.strip()[4:].strip()
b = sum(f["severity"] == "blocker" for f in findings); w = len(findings) - b
verdict = "fail" if sys.argv[2] != "0" else ("warn" if w else "pass")
json.dump({"tool": "preflight", "verdict": verdict, "blockers": b, "warnings": w,
           "summary": f"{b} blocker(s), {w} warning(s)", "findings": findings}, open(sys.argv[3], "w"), indent=2)
EOF

hr "Gate 6 · privacy forms vs code"
"$PY" "$SKILLS/app-comply/scripts/privacy_scan.py" . --out "$R" --json "$R/privacy.json"

hr "Gate 6 · store policy"
if [ -n "$ARTIFACT" ]; then
  "$PY" "$SKILLS/app-comply/scripts/store_policy_check.py" . --artifact "$ARTIFACT" --json "$R/store-policy.json"
else
  "$PY" "$SKILLS/app-comply/scripts/store_policy_check.py" . --json "$R/store-policy.json"
fi

if [ -n "$BASE" ]; then
  hr "Gate 8 · OTA or store build (since $BASE)"
  "$PY" "$SKILLS/app-comply/scripts/ota_check.py" . --base "$BASE" --json "$R/ota.json"
fi

if [ -n "$MOBSF_FILE$MOBSF_REPORT" ]; then
  hr "Gate 5 · security (MobSF / MASVS)"
  if [ -n "$MOBSF_REPORT" ]; then
    "$PY" "$SKILLS/app-secure/scripts/mobsf_gate.py" --report "$MOBSF_REPORT" --json "$R/security.json" --md "$R/security.md" --quiet
  else
    "$PY" "$SKILLS/app-secure/scripts/mobsf_gate.py" --file "$MOBSF_FILE" --json "$R/security.json" --md "$R/security.md" --quiet
  fi
  head -14 "$R/security.md" 2>/dev/null
fi

if [ -n "$EXPLORE" ]; then
  hr "Gate 4 · exploratory test"
  "$PY" "$SKILLS/app-test/scripts/explore_to_maestro.py" "$EXPLORE" --out .maestro/repro \
    --report "$R/bug-report.md" --json "$R/explore.json"
fi

if [ -n "$TESTERS" ]; then
  hr "Gate 7 · Play closed test"
  "$PY" "$SKILLS/app-release/scripts/testers.py" "$TESTERS" --json "$R/testers.json"
fi

hr "Release report"
"$PY" "$SKILLS/app-release/scripts/release_report.py" --reports "$R" --app "$(basename "$PROJECT")" --version "$VERSION" --json "$R/release.json"
