"""app-comply: privacy_scan.py, store_policy_check.py, ota_check.py."""
from __future__ import annotations

import io
import struct
import subprocess
import unittest
import zipfile

from util import TempCase, run, run_py


class PrivacyScan(TempCase):
    def scan(self, project):
        out = self.tmp / "privacy.json"
        p = run_py("app-comply", "privacy_scan.py", project, "--json", out, "--out", self.tmp / "drafts")
        return p, self.load(out)

    def test_good_app_passes_and_writes_drafts(self):
        p, res = self.scan(self.fixture("good-app"))
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(res["blockers"], 0)
        names = {s["name"] for s in res["scan"]["sdks"]}
        self.assertTrue({"Sentry", "Supabase", "RevenueCat"} <= names)
        ds = (self.tmp / "drafts" / "data-safety-draft.md").read_text()
        self.assertIn("App info and performance / Crash logs", ds)
        self.assertIn("Financial info / Purchase history", ds)
        labels = (self.tmp / "drafts" / "privacy-labels-draft.md").read_text()
        self.assertIn("Diagnostics / Crash Data", labels)
        self.assertIn("Purchases / Purchase History", labels)

    def test_legal_page_links_are_not_data_destinations(self):
        _, res = self.scan(self.fixture("good-app"))
        hosts = {h["host"] for h in res["scan"]["hosts"]}
        self.assertNotIn("goodbudget.memeo.in", hosts)
        self.assertIn("abcd.supabase.co", hosts)

    def test_bad_app_blocks_on_att_ai_manifest_inventory(self):
        p, res = self.scan(self.fixture("bad-app"))
        self.assertEqual(p.returncode, 1)
        self.assertTrue({"INV-MISSING", "ATT", "AI-CONSENT", "PM-MISSING"} <= self.ids(res, "blocker"))

    def test_undeclared_sdk_and_host_are_flagged(self):
        app = self.fixture("good-app")
        pkg = self.load(app / "package.json")
        pkg["dependencies"]["mixpanel-react-native"] = "^3.0.0"
        (app / "package.json").write_text(__import__("json").dumps(pkg))
        (app / "src" / "track.ts").write_text('fetch("https://events.mystery-cdn.net/v1/e")\n')
        p, res = self.scan(app)
        self.assertEqual(p.returncode, 1)
        titles = " ".join(f["title"] for f in res["findings"])
        self.assertIn("Mixpanel", titles)
        self.assertIn("events.mystery-cdn.net", titles)

    def test_permissions_feed_the_inventory_draft(self):
        _, res = self.scan(self.fixture("bad-app"))
        items = {i["item"] for i in res["scan"]["items"]}
        self.assertIn("Precise location", items)      # ACCESS_BACKGROUND_LOCATION
        self.assertIn("SMS or MMS", items)            # READ_SMS


def elf64(p_align: int) -> bytes:
    """Minimal little-endian ELF64 shared object with one PT_LOAD segment."""
    ident = b"\x7fELF" + bytes([2, 1, 1]) + bytes(9)
    header = ident + struct.pack("<HHIQQQIHHHHHH", 3, 183, 1, 0, 64, 0, 0, 64, 56, 1, 64, 0, 0)
    phdr = struct.pack("<IIQQQQQQ", 1, 5, 0, 0, 0, 0x1000, 0x1000, p_align)
    return header + phdr


class StorePolicy(TempCase):
    def check(self, project, *extra):
        out = self.tmp / "sp.json"
        p = run_py("app-comply", "store_policy_check.py", project, "--json", out, *extra)
        return p, self.load(out)

    def test_good_app_passes(self):
        p, res = self.check(self.fixture("good-app"))
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("P-TARGET", self.ids(res, "pass"))

    def test_bad_app_policy_blockers(self):
        p, res = self.check(self.fixture("bad-app"))
        self.assertEqual(p.returncode, 1)
        expected = {"P-TARGET", "ACCOUNT-DELETE", "A-LOGIN", "A-RESTORE", "SUB-TERMS", "UGC", "A-NAME",
                    "A-KEYWORDS", "META-PROMO", "META-EMOJI", "A-OTHERPLATFORM", "A-PRIVACYURL", "P-PRIVACYURL"}
        self.assertTrue(expected <= self.ids(res, "blocker"), expected - self.ids(res, "blocker"))
        self.assertIn("P-DECLARE", self.ids(res, "manual"))

    def test_min_target_sdk_override(self):
        app = self.fixture("good-app")
        _, res = self.check(app, "--min-target-sdk", "37")
        self.assertIn("P-TARGET", self.ids(res, "blocker"))

    def write_zip(self, name, align, stored=False, pad=0):
        path = self.tmp / name
        with zipfile.ZipFile(path, "w") as z:
            if pad:
                z.writestr("assets/pad.bin", b"x" * pad, compress_type=zipfile.ZIP_STORED)
            z.writestr("lib/arm64-v8a/libapp.so", elf64(align),
                       compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
            z.writestr("lib/armeabi-v7a/libold.so", b"\x7fELF\x01\x01")  # 32-bit: not checked
        return path

    def test_16kb_misaligned_library_blocks(self):
        aab = self.write_zip("app.aab", 4096)
        p, res = self.check(self.fixture("good-app"), "--artifact", aab)
        self.assertEqual(p.returncode, 1)
        self.assertIn("P-16KB", self.ids(res, "blocker"))

    def test_16kb_aligned_library_passes(self):
        aab = self.write_zip("app.aab", 16384)
        p, res = self.check(self.fixture("good-app"), "--artifact", aab)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("P-16KB", self.ids(res, "pass"))

    def test_apk_stored_lib_must_be_zip_aligned(self):
        apk = self.write_zip("app.apk", 16384, stored=True, pad=100)
        _, res = self.check(self.fixture("good-app"), "--artifact", apk)
        self.assertIn("P-16KB-ZIP", self.ids(res, "blocker"))

    def test_fastlane_metadata_is_read(self):
        app = self.fixture("good-app")
        (app / "store" / "listing.json").unlink()
        d = app / "fastlane" / "metadata" / "en-US"
        d.mkdir(parents=True)
        (d / "name.txt").write_text("Top Budget App")
        (d / "privacy_url.txt").write_text("https://goodbudget.memeo.in/privacy")
        _, res = self.check(app)
        self.assertIn("META-PROMO", self.ids(res, "blocker"))


class OtaCheck(TempCase):
    def git(self, repo, *args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                       env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})

    def repo(self):
        app = self.fixture("good-app")
        self.git(app, "init", "-q", "-b", "main")
        self.git(app, "add", "-A")
        self.git(app, "commit", "-qm", "store build 1.0.0")
        self.git(app, "tag", "v1.0.0")
        return app

    def commit(self, app, msg="change"):
        self.git(app, "add", "-A")
        self.git(app, "commit", "-qm", msg)

    def ota(self, app):
        out = self.tmp / "ota.json"
        p = run_py("app-comply", "ota_check.py", app, "--base", "v1.0.0", "--json", out)
        return p, self.load(out)

    def test_js_only_change_is_ota(self):
        app = self.repo()
        (app / "src" / "api.ts").write_text((app / "src" / "api.ts").read_text() + "\nexport const greeting = 'Hi';\n")
        self.commit(app)
        p, res = self.ota(app)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(res["route"], "ota")

    def test_native_file_needs_store(self):
        app = self.repo()
        (app / "ios").mkdir()
        (app / "ios" / "Podfile").write_text("platform :ios, '16.0'\n")
        self.commit(app)
        p, res = self.ota(app)
        self.assertEqual(p.returncode, 1)
        self.assertIn("OTA-NATIVE", self.ids(res, "blocker"))

    def test_permission_change_needs_store(self):
        app = self.repo()
        cfg = app / "app.config.ts"
        cfg.write_text(cfg.read_text().replace('permissions: ["CAMERA"]', 'permissions: ["CAMERA", "RECORD_AUDIO"]'))
        self.commit(app)
        p, res = self.ota(app)
        self.assertEqual(p.returncode, 1)
        self.assertIn("OTA-PERMISSION", self.ids(res, "blocker"))

    def test_payment_change_needs_store(self):
        app = self.repo()
        (app / "src" / "paywall.ts").write_text("export const price = '4.99'; export function purchase() {}\n")
        self.commit(app)
        _, res = self.ota(app)
        self.assertIn("OTA-PAYMENT", self.ids(res, "blocker"))

    def test_native_dependency_needs_store(self):
        app = self.repo()
        pkg = self.load(app / "package.json")
        pkg["dependencies"]["expo-camera"] = "~17.0.0"
        (app / "package.json").write_text(__import__("json").dumps(pkg))
        self.commit(app)
        _, res = self.ota(app)
        self.assertIn("OTA-DEPS", self.ids(res, "blocker"))

    def test_many_new_screens_change_purpose(self):
        app = self.repo()
        for n in ("chat", "marketplace"):
            (app / "app" / f"{n}.tsx").write_text("export default function S() { return null; }\n")
        self.commit(app)
        _, res = self.ota(app)
        self.assertIn("OTA-PURPOSE", self.ids(res, "blocker"))

    def test_bad_ref_is_usage_error(self):
        app = self.repo()
        p = run_py("app-comply", "ota_check.py", app, "--base", "does-not-exist")
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
