#!/usr/bin/env python3
"""Two-store policy pre-review: Google Play + Apple App Store.

Checks what code and config can show before a human reviewer sees the app:
target API, 16 KB page support of native libraries (when an .apk/.aab is given),
sensitive-permission declarations, account deletion, billing, login options,
export compliance, privacy manifest, WebView-wrapper risk, and store-listing
metadata (from store/listing.json or fastlane/metadata).

Usage:
  store_policy_check.py PROJECT [--artifact app.aab|app.apk] [--listing store/listing.json]
                        [--min-target-sdk 36] [--json reports/store-policy.json]
Exit: 0 pass/warn, 1 blockers found, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _project import Project, emit, read, result  # noqa: E402

PAGE_16K = 16384
PLAY_DECLARATIONS = {
    "READ_SMS": "SMS and Call Log permissions declaration", "RECEIVE_SMS": "SMS and Call Log permissions declaration",
    "SEND_SMS": "SMS and Call Log permissions declaration", "READ_CALL_LOG": "SMS and Call Log permissions declaration",
    "WRITE_CALL_LOG": "SMS and Call Log permissions declaration", "PROCESS_OUTGOING_CALLS": "SMS and Call Log permissions declaration",
    "MANAGE_EXTERNAL_STORAGE": "All files access declaration", "ACCESS_BACKGROUND_LOCATION": "Location permissions declaration (background)",
    "BIND_ACCESSIBILITY_SERVICE": "Accessibility API declaration", "QUERY_ALL_PACKAGES": "Package visibility (QUERY_ALL_PACKAGES) declaration",
    "REQUEST_INSTALL_PACKAGES": "Request install packages declaration", "SCHEDULE_EXACT_ALARM": "Exact alarm declaration",
    "USE_EXACT_ALARM": "Exact alarm declaration", "USE_FULL_SCREEN_INTENT": "Full-screen intent declaration",
    "READ_MEDIA_IMAGES": "Photo and video permissions declaration (or use the Photo Picker)",
    "READ_MEDIA_VIDEO": "Photo and video permissions declaration (or use the Photo Picker)",
    "FOREGROUND_SERVICE": "Foreground service types declaration (with video)", "READ_CONTACTS": "Contacts: prefer the Contact Picker (policy from 27 Jan 2027)",
    "ACCESS_LOCAL_NETWORK": "Local network permission declaration (from 25 Aug 2027)",
}
PROMO_WORDS = re.compile(r"(#\s?1\b|\bbest\b|\btop\b|\bno\.?\s?1\b|\bnumber one\b|\bfree\b|\bsale\b|\bdiscount\b|\bcheapest\b|\bapp of the year\b)", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def f(id_, sev, title, fix="", ref=""):
    return {"id": id_, "severity": sev, "title": title, "fix": fix, "ref": ref}


# ---------- native library page size ----------
def elf_load_alignments(data: bytes) -> list[int] | None:
    """Return p_align of every PT_LOAD segment of a 64-bit little-endian ELF, or None if not ELF64."""
    if len(data) < 64 or data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
        return None
    phoff = struct.unpack_from("<Q", data, 0x20)[0]
    phentsize, phnum = struct.unpack_from("<HH", data, 0x36)
    aligns = []
    for i in range(phnum):
        off = phoff + i * phentsize
        if off + 56 > len(data):
            break
        p_type = struct.unpack_from("<I", data, off)[0]
        if p_type == 1:  # PT_LOAD
            aligns.append(struct.unpack_from("<Q", data, off + 48)[0])
    return aligns


def check_artifact(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return [f("P-ARTIFACT", "blocker", f"Artifact not found: {path}")]
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return [f("P-ARTIFACT", "blocker", f"Not a valid .apk/.aab: {path}")]
    raw = path.read_bytes()
    libs = [i for i in zf.infolist() if re.search(r"(^|/)lib/(arm64-v8a|x86_64)/[^/]+\.so$", i.filename)]
    bad_align, bad_zip = [], []
    for info in libs:
        aligns = elf_load_alignments(zf.read(info))
        if aligns is None:
            continue
        if any(a < PAGE_16K for a in aligns):
            bad_align.append(f"{info.filename} (p_align {min(aligns)})")
        if path.suffix == ".apk" and info.compress_type == zipfile.ZIP_STORED:
            h = info.header_offset
            name_len, extra_len = struct.unpack_from("<HH", raw, h + 26)
            if (h + 30 + name_len + extra_len) % PAGE_16K:
                bad_zip.append(info.filename)
    if not libs:
        out.append(f("P-16KB", "pass", "No 64-bit native libraries in the artifact"))
    elif bad_align:
        out.append(f("P-16KB", "blocker", f"Native libraries not 16 KB page aligned: {', '.join(bad_align[:5])}",
                     "Rebuild with NDK r28+ / AGP 8.5.1+ (or -Wl,-z,max-page-size=16384) and update every SDK that ships .so files.",
                     "https://developer.android.com/guide/practices/page-sizes"))
    else:
        out.append(f("P-16KB", "pass", f"{len(libs)} native libraries are 16 KB page aligned"))
    if bad_zip:
        out.append(f("P-16KB-ZIP", "blocker", f"Uncompressed .so not 16 KB aligned inside the APK: {', '.join(bad_zip[:5])}",
                     "Use zipalign -P 16 (AGP 8.5.1+ does this automatically)."))
    return out


# ---------- listing metadata ----------
def load_listing(project: Project, listing_arg: str | None) -> dict:
    listing = {"android": {}, "ios": {}}
    p = Path(listing_arg) if listing_arg else project.root / "store" / "listing.json"
    if p.exists():
        try:
            data = json.loads(read(p))
            listing["android"].update(data.get("android", {}))
            listing["ios"].update(data.get("ios", {}))
        except json.JSONDecodeError:
            listing["_error"] = f"{p} is not valid JSON"
    fl = project.root / "fastlane" / "metadata"
    for loc in sorted((fl / "android").glob("*")) if (fl / "android").is_dir() else []:
        for key, fn in (("title", "title.txt"), ("short_description", "short_description.txt"), ("full_description", "full_description.txt")):
            if (loc / fn).exists():
                listing["android"].setdefault(key, read(loc / fn).strip())
        break
    for loc in sorted(fl.glob("*")) if fl.is_dir() else []:
        if loc.name in ("android", "review_information") or not loc.is_dir():
            continue
        for key, fn in (("name", "name.txt"), ("subtitle", "subtitle.txt"), ("description", "description.txt"),
                        ("keywords", "keywords.txt"), ("promotional_text", "promotional_text.txt"), ("privacy_url", "privacy_url.txt")):
            if (loc / fn).exists():
                listing["ios"].setdefault(key, read(loc / fn).strip())
        break
    return listing


def check_listing(listing: dict) -> list[dict]:
    out = []
    if listing.get("_error"):
        out.append(f("LISTING", "blocker", listing["_error"]))
    a, i = listing["android"], listing["ios"]
    if not a and not i:
        return out + [f("LISTING", "manual", "No store listing found (store/listing.json or fastlane/metadata)",
                        "Add store/listing.json so listing text is checked automatically; until then review it by hand.")]
    limits = [("android", "title", 30, "P-TITLE"), ("android", "short_description", 80, "P-SHORT"),
              ("android", "full_description", 4000, "P-FULL"), ("ios", "name", 30, "A-NAME"),
              ("ios", "subtitle", 30, "A-SUBTITLE"), ("ios", "promotional_text", 170, "A-PROMO"),
              ("ios", "description", 4000, "A-DESC")]
    for store, key, limit, id_ in limits:
        val = listing[store].get(key)
        if val and len(val) > limit:
            out.append(f(id_, "blocker", f"{store} {key} is {len(val)} characters (limit {limit})", f"Shorten to {limit}."))
    kw = i.get("keywords")
    if kw and len(kw.encode("utf-8")) > 100:
        out.append(f("A-KEYWORDS", "blocker", f"iOS keywords are {len(kw.encode('utf-8'))} bytes (limit 100)", "Shorten the keyword list."))
    for store, key in (("android", "title"), ("android", "short_description"), ("ios", "name"), ("ios", "subtitle")):
        val = listing[store].get(key, "")
        m = PROMO_WORDS.search(val)
        if m:
            out.append(f("META-PROMO", "blocker", f"{store} {key} contains a ranking/price claim: '{m.group(0)}'",
                         "Play metadata policy and Apple 2.3.7 forbid performance, ranking and price words in titles.", "Play Metadata policy; Apple 2.3.7"))
        if EMOJI.search(val):
            out.append(f("META-EMOJI", "blocker", f"{store} {key} contains emoji", "Remove emoji and decorative symbols from the title/name."))
        if val and len(val) > 4 and val.isupper():
            out.append(f("META-CAPS", "warning", f"{store} {key} is ALL CAPS", "Use normal capitalisation (Play metadata policy)."))
    ios_text = " ".join(str(v) for v in i.values()).lower()
    if re.search(r"\bandroid\b|google play|play store", ios_text):
        out.append(f("A-OTHERPLATFORM", "blocker", "iOS listing mentions Android / Google Play",
                     "Remove references to other platforms (Apple 2.3.10).", "Apple 2.3.10"))
    if i and not i.get("privacy_url"):
        out.append(f("A-PRIVACYURL", "blocker", "No privacy policy URL in the iOS listing", "Set privacy_url."))
    if a and not a.get("privacy_url"):
        out.append(f("P-PRIVACYURL", "blocker", "No privacy policy URL in the Play listing", "Set privacy_url."))
    if not [x for x in out if x["severity"] in ("blocker", "warning")]:
        out.append(f("LISTING", "pass", "Listing text within limits and free of banned claims"))
    return out


# ---------- project checks ----------
def check_project(p: Project, min_sdk: int, listing: dict) -> list[dict]:
    out = []
    # Target API
    t = p.target_sdk()
    if t is None:
        out.append(f("P-TARGET", "warning" if p.is_expo else "blocker",
                     "Android targetSdkVersion not set explicitly",
                     f"Pin it with expo-build-properties or build.gradle: targetSdkVersion {min_sdk}."))
    elif t < min_sdk:
        out.append(f("P-TARGET", "blocker", f"targetSdkVersion {t} < {min_sdk}",
                     f"Raise targetSdkVersion and compileSdkVersion to {min_sdk}.", "Play target API policy"))
    else:
        out.append(f("P-TARGET", "pass", f"targetSdkVersion {t}"))
    # Native code without artifact
    native_dirs = [x for x in ("android/app/src/main/jniLibs", "android/app/src/main/cpp") if (p.root / x).exists()]
    if native_dirs:
        out.append(f("P-16KB", "manual", f"Project has native code ({', '.join(native_dirs)})",
                     "Run this check with --artifact on the release .aab/.apk to verify 16 KB page alignment."))
    # Declarations
    perms = p.permissions()
    decl = sorted({PLAY_DECLARATIONS[x] for x in perms if x in PLAY_DECLARATIONS})
    if any(x.startswith("FOREGROUND_SERVICE") for x in perms):
        decl = sorted(set(decl) | {PLAY_DECLARATIONS["FOREGROUND_SERVICE"]})
    for d in decl:
        out.append(f("P-DECLARE", "manual", f"Play Console: {d}", "Justify it as core functionality and attach a demo video, or remove the permission."))
    # Accounts
    auth = any(k in p.deps for k in ("@supabase/supabase-js", "firebase", "@react-native-firebase/auth", "expo-auth-session",
                                      "@clerk/clerk-expo", "aws-amplify", "react-native-app-auth")) or bool(p.grep(r"signUp|createUserWithEmailAndPassword|registerUser"))
    if auth:
        if not p.grep(r"delete[ _-]?(my[ _-]?)?account|deleteAccount|deleteUser|account[ _-]?deletion"):
            out.append(f("ACCOUNT-DELETE", "blocker", "Accounts can be created but there is no in-app account deletion",
                         "Add Settings → Delete account.", "Apple 5.1.1(v); Play User Data policy"))
        if not listing["android"].get("account_deletion_url"):
            out.append(f("P-DELETE-URL", "manual", "Play needs a public account-deletion web URL",
                         "Publish the page and add account_deletion_url to store/listing.json and Play Console (Data safety)."))
        third_party = [k for k in ("@react-native-google-signin/google-signin", "react-native-fbsdk-next") if k in p.deps] or \
            (["expo-auth-session"] if "expo-auth-session" in p.deps and p.grep(r"google|facebook") else [])
        if third_party and "expo-apple-authentication" not in p.deps:
            out.append(f("A-LOGIN", "blocker", f"Third-party login ({', '.join(third_party)}) without Sign in with Apple or an equivalent",
                         "Offer Sign in with Apple (or another login that limits data to name + email and allows hiding the email).", "Apple 4.8"))
    # Billing
    iap = [k for k in ("react-native-purchases", "react-native-iap", "expo-iap") if k in p.deps]
    ext = [k for k in ("@stripe/stripe-react-native", "react-native-razorpay", "react-native-paypal") if k in p.deps]
    if iap and not p.grep(r"restorePurchases|restoreTransactions|getAvailablePurchases|restore[ _-]?purchase"):
        out.append(f("A-RESTORE", "blocker", "In-app purchases without Restore Purchases", "Add a Restore Purchases button.", "Apple 3.1.1"))
    if iap and not p.grep(r"terms[ -]?of[ -]?(use|service)|EULA|/terms"):
        out.append(f("SUB-TERMS", "blocker", "Purchases without a Terms of Use / EULA link",
                     "Show price, period, renewal and cancel terms plus a working Terms link on the paywall.", "Apple 3.1.2; Play Subscriptions policy"))
    if ext:
        out.append(f("BILLING", "manual", f"External payment SDK ({', '.join(ext)})",
                     "Allowed for physical goods/services. Digital content and subscriptions need store billing unless a regional exception applies (see compliance.md)."))
    # Export compliance
    if p.is_expo or p.plists:
        if "usesNonExemptEncryption" not in p.config_text and "ITSAppUsesNonExemptEncryption" not in p.native_text:
            out.append(f("A-EXPORT", "warning", "Export compliance not declared",
                         "Set ios.config.usesNonExemptEncryption (false for HTTPS/OS crypto only)."))
    # WebView wrapper
    if "react-native-webview" in p.deps:
        screens = [x for x in p.sources if "app" in x.relative_to(p.root).parts[:1] or "screens" in x.parts]
        if len(screens) <= 3:
            out.append(f("A-WRAPPER", "warning", "App looks like a thin WebView wrapper",
                         "Add native features and offline value; Apple rejects repackaged websites.", "Apple 4.2"))
    # UGC
    if p.grep(r"createPost|uploadPost|sendMessage|addComment|postComment") and not p.grep(r"report(User|Post|Content|Abuse)|blockUser|block[ _-]user|flagContent"):
        out.append(f("UGC", "blocker", "User-generated content without report and block",
                     "Add content filtering, report, block and a published contact.", "Apple 1.2; Play UGC policy"))
    # Kids
    if re.search(r"\bkids?\b|children", " ".join(str(v) for v in listing["android"].values()) + " ".join(str(v) for v in listing["ios"].values()), re.I):
        out.append(f("KIDS", "manual", "Listing mentions kids / children",
                     "Complete Play Target audience + Families policy and Apple Kids Category rules; no third-party ads or analytics without parental gate."))
    out.append(f("REVIEW-KIT", "manual", "Demo account on the live backend and review notes", "Fill templates/review-notes.md and test the login today."))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--artifact", help="release .aab or .apk for the 16 KB page-size check")
    ap.add_argument("--listing", help="listing JSON (default PROJECT/store/listing.json)")
    ap.add_argument("--min-target-sdk", type=int, default=36)
    ap.add_argument("--json", dest="json_path")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if not Path(a.project).is_dir():
        print(f"Not a directory: {a.project}", file=sys.stderr)
        return 2
    p = Project(a.project)
    listing = load_listing(p, a.listing)
    findings = check_project(p, a.min_target_sdk, listing) + check_listing(listing)
    if a.artifact:
        findings += check_artifact(Path(a.artifact))
    return emit(result("store_policy_check", findings), a.json_path, a.quiet)


if __name__ == "__main__":
    sys.exit(main())
