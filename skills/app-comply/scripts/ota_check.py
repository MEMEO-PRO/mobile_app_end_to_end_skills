#!/usr/bin/env python3
"""OTA-update compliance check.

Decides whether the changes since the last store build may ship as an
over-the-air update (EAS Update / CodePush) or need a new store build and review.

Apple (DPLA 3.3(b), guideline 2.5.2) allows downloaded interpreted code only if it
does not change the app's primary purpose, add a storefront, or bypass OS security.
Google Play allows JS run in an interpreter but not downloaded native code.
Native changes also crash on binaries that don't contain them.

Usage:
  ota_check.py PROJECT --base <git ref of the last store build> [--head HEAD] [--json reports/ota.json]
Exit: 0 OTA allowed (possibly with warnings), 1 store build required, 2 usage / git error.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _project import emit, result  # noqa: E402

NATIVE_PATH = re.compile(r"^(android|ios)/|(^|/)(Podfile(\.lock)?|build\.gradle(\.kts)?|settings\.gradle(\.kts)?|gradle\.properties|"
                         r"AndroidManifest\.xml|Info\.plist|.*\.xcprivacy|.*\.entitlements)$|\.(kt|java|swift|m|mm|c|cpp|h|so)$")
CONFIG_PATH = re.compile(r"^app\.(json|config\.(js|ts))$")
NATIVE_PKG = re.compile(r"^(expo-|react-native|@react-native|@react-native-|@stripe/|@sentry/react-native|@shopify/react-native|"
                        r"@react-native-firebase/|@notifee/|@op-engineering/)|native")
PERMISSION = re.compile(r"permission|UsageDescription|blockedPermissions|entitlement", re.I)
PAYMENT = re.compile(r"purchase|paywall|subscription|price|checkout|billing|stripe|razorpay|revenuecat|in[-_ ]?app", re.I)
SECURITY = re.compile(r"(eval\(|new Function\(|codeSigning|certificate|pinning|jailbreak|root(ed)? detection)", re.I)


def git(project: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(project), *args], check=True, capture_output=True, text=True).stdout


def changed_deps(project: Path, base: str, head: str) -> tuple[list[str], list[str]]:
    import json
    def deps(ref):
        try:
            data = json.loads(git(project, "show", f"{ref}:package.json"))
        except (subprocess.CalledProcessError, ValueError):
            return {}
        return data.get("dependencies", {})
    a, b = deps(base), deps(head)
    native = [n for n in sorted(set(a) ^ set(b) | {n for n in a.keys() & b.keys() if a[n] != b[n]}) if NATIVE_PKG.search(n)]
    js = [n for n in sorted(set(a) ^ set(b) | {n for n in a.keys() & b.keys() if a[n] != b[n]}) if not NATIVE_PKG.search(n)]
    return native, js


def analyse(project: Path, base: str, head: str, new_screen_limit: int) -> list[dict]:
    files = [x for x in git(project, "diff", "--name-only", f"{base}..{head}").splitlines() if x]
    status = git(project, "diff", "--name-status", f"{base}..{head}").splitlines()
    out = []
    if not files:
        return [{"id": "OTA-EMPTY", "severity": "pass", "title": f"No changes between {base} and {head}"}]
    native = [x for x in files if NATIVE_PATH.search(x)]
    if native:
        out.append({"id": "OTA-NATIVE", "severity": "blocker", "title": f"Native files changed: {', '.join(native[:6])}",
                    "fix": "Ship a new store build. An OTA bundle would reach binaries without this native code and crash."})
    cfg = [x for x in files if CONFIG_PATH.search(x)]
    if cfg:
        diff = git(project, "diff", f"{base}..{head}", "--", *cfg)
        changed = [l for l in diff.splitlines() if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        if any(PERMISSION.search(l) for l in changed):
            out.append({"id": "OTA-PERMISSION", "severity": "blocker", "title": "Permissions or usage strings changed in app config",
                        "fix": "Permission changes need a store build, updated declarations and privacy forms."})
        if any(re.search(r"plugins|ios\s*:|android\s*:|runtimeVersion|bundleIdentifier|package|sdkVersion", l) for l in changed):
            out.append({"id": "OTA-CONFIG", "severity": "blocker", "title": "Native app config changed (plugins / ios / android / runtimeVersion)",
                        "fix": "Rebuild with eas build; the fingerprint runtime version will change."})
        elif not any(PERMISSION.search(l) for l in changed):
            out.append({"id": "OTA-CONFIG-JS", "severity": "warning", "title": f"App config changed ({', '.join(cfg)})",
                        "fix": "Confirm only JS-side fields (e.g. extra) changed; run `npx expo-updates fingerprint:generate` against the store build."})
    if "package.json" in files:
        nat, js = changed_deps(project, base, head)
        if nat:
            out.append({"id": "OTA-DEPS", "severity": "blocker", "title": f"Native dependencies added, removed or upgraded: {', '.join(nat[:8])}",
                        "fix": "Ship a store build; then check privacy forms for any new SDK."})
        if js:
            out.append({"id": "OTA-JSDEPS", "severity": "warning", "title": f"JS dependencies changed: {', '.join(js[:8])}",
                        "fix": "Fine for OTA if they contain no native code and collect no new data; re-run privacy_scan."})
    code = [x for x in files if re.search(r"\.(t|j)sx?$", x) and not x.startswith(("__tests__", "tests/", "e2e/"))]
    if code:
        diff = git(project, "diff", f"{base}..{head}", "--", *code)
        added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
        if any(PAYMENT.search(l) for l in added):
            out.append({"id": "OTA-PAYMENT", "severity": "blocker", "title": "Payment / purchase code changed",
                        "fix": "Payment flows change what the reviewer approved: ship through store review (Apple 3.1, 2.5.2)."})
        if any(SECURITY.search(l) for l in added):
            out.append({"id": "OTA-SECURITY", "severity": "blocker", "title": "Code that touches dynamic code execution, signing or security checks changed",
                        "fix": "OTA must not bypass OS security (Apple 2.5.2); ship through review."})
    new_screens = [l.split("\t")[-1] for l in status if l.startswith("A") and re.search(r"^(app|src/screens|src/app)/.*\.(t|j)sx$", l.split("\t")[-1])]
    if len(new_screens) > new_screen_limit:
        out.append({"id": "OTA-PURPOSE", "severity": "blocker", "title": f"{len(new_screens)} new screens: {', '.join(new_screens[:5])}",
                    "fix": "New features that change what the app does need review (Apple DPLA 3.3(b), 2.5.2). Ship a store build."})
    elif new_screens:
        out.append({"id": "OTA-SCREENS", "severity": "warning", "title": f"New screens: {', '.join(new_screens)}",
                    "fix": "OK for OTA only if they fix or extend an existing feature without changing the app's purpose."})
    if not [x for x in out if x["severity"] == "blocker"]:
        out.append({"id": "OTA-OK", "severity": "pass", "title": f"{len(files)} changed file(s) are JS/asset-only",
                    "fix": "Publish with code signing to a small rollout first: eas update --channel production --rollout-percentage 10"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--base", required=True, help="git ref of the last store build (tag or commit)")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--new-screen-limit", type=int, default=1)
    ap.add_argument("--json", dest="json_path")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    try:
        findings = analyse(project, a.base, a.head, a.new_screen_limit)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"git error: {getattr(e, 'stderr', e)}", file=sys.stderr)
        return 2
    blockers = [x for x in findings if x["severity"] == "blocker"]
    res = result("ota_check", findings, summary=("STORE BUILD REQUIRED" if blockers else "OTA ALLOWED"),
                 extra={"base": a.base, "head": a.head, "route": "store" if blockers else "ota"})
    return emit(res, a.json_path, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
