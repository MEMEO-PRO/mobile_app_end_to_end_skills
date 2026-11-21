"""app-spec: inventory_lint.py · app-build: scaffold.py · app-factory: preflight.sh, run_gates.sh · skill integrity."""
from __future__ import annotations

import json
import re
import unittest

from util import ROOT, SKILLS, TempCase, run, run_py, script

TEMPLATE = SKILLS / "app-factory" / "templates" / "data-inventory.md"


class InventoryLint(TempCase):
    def lint(self, path):
        out = self.tmp / "inv.json"
        p = run_py("app-spec", "inventory_lint.py", path, "--json", out)
        return p, (self.load(out) if out.exists() else None)

    def test_complete_inventory_passes(self):
        app = self.fixture("good-app")
        p, res = self.lint(app / "docs" / "data-inventory.md")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(res["verdict"], "pass")

    def test_untouched_template_fails(self):
        p, res = self.lint(TEMPLATE)
        self.assertEqual(p.returncode, 1)
        self.assertIn("INV-CHILDREN", self.ids(res, "blocker"))

    def test_partial_rows_and_placeholders_fail(self):
        md = TEMPLATE.read_text().replace(
            "| 3 | | | | | | | | | | | | | |",
            "| 3 | Phone number | Personal info / Phone number | <purpose> | Required | Your code | api.x.com | No | Yes | No | Yes | TBD | | Contract |")
        path = self.tmp / "inv.md"
        path.write_text(md)
        _, res = self.lint(path)
        titles = " ".join(f["title"] for f in res["findings"] if f["id"] == "INV-CELL")
        self.assertIn("'Phone number': Purpose(s)", titles)
        self.assertIn("'Phone number': Retention", titles)
        self.assertIn("'Phone number': How the user deletes it", titles)

    def test_missing_column_and_yes_no(self):
        md = ("## 1. Data items\n\n| # | Data item | Play category | Purpose | Collected by | Sent to | Shared | Linked | Tracking | Retention | Lawful basis |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|\n| 1 | Email | Personal info | Account | Us | api.x.com | Maybe | Yes | No | 1y | Contract |\n")
        path = self.tmp / "inv.md"
        path.write_text(md)
        p, res = self.lint(path)
        self.assertEqual(p.returncode, 1)
        self.assertIn("INV-COLUMN", self.ids(res, "blocker"))   # "How the user deletes it" missing
        self.assertIn("INV-YESNO", self.ids(res, "warning"))

    def test_missing_file(self):
        p, res = self.lint(self.tmp / "nope.md")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(res["verdict"], "fail")


class Scaffold(TempCase):
    def scaffold(self, *extra, d=None):
        d = d or self.tmp / "app"
        return run_py("app-build", "scaffold.py", "--name", "Memo Pad", "--package", "in.memeo.memopad",
                      "--website", "https://memopad.memeo.in", "--dir", d, *extra), d

    def test_writes_all_files(self):
        p, d = self.scaffold()
        self.assertEqual(p.returncode, 0, p.stderr)
        for rel in ("app.config.ts", "eas.json", ".maestro/smoke.yaml", "src/config/legal.ts", "docs/data-inventory.md",
                    "docs/threat-model.md", "docs/legal.md", "store/listing.json", ".github/workflows/app-gates.yml"):
            self.assertTrue((d / rel).exists(), rel)
        cfg = (d / "app.config.ts").read_text()
        for needle in ('policy: "fingerprint"', "targetSdkVersion: 36", "usesNonExemptEncryption: false",
                       "privacyManifests", "codeSigningCertificate", 'package: "in.memeo.memopad"'):
            self.assertIn(needle, cfg)
        eas = json.loads((d / "eas.json").read_text())
        self.assertEqual(set(eas["build"]), {"development", "preview", "production"})
        self.assertTrue(eas["build"]["production"]["autoIncrement"])
        self.assertIn("appId: in.memeo.memopad", (d / ".maestro/smoke.yaml").read_text())
        self.assertIn("# Data inventory — Memo Pad", (d / "docs/data-inventory.md").read_text())

    def test_refuses_to_overwrite(self):
        _, d = self.scaffold()
        p, _ = self.scaffold(d=d)
        self.assertEqual(p.returncode, 1)
        p, _ = self.scaffold("--force", d=d)
        self.assertEqual(p.returncode, 0)

    def test_rejects_placeholder_and_invalid_ids(self):
        for bad in ("com.example.app", "MyApp", "com.Acme.app", "1abc.def"):
            p = run_py("app-build", "scaffold.py", "--name", "X", "--package", bad, "--dir", self.tmp / "x")
            self.assertEqual(p.returncode, 2, bad)

    def test_scaffolded_project_passes_preflight_and_policy(self):
        _, d = self.scaffold()
        (d / "package.json").write_text(json.dumps({"dependencies": {"expo": "~58.0.0", "expo-secure-store": "~15.0.0"}}))
        p = run(["bash", script("app-factory", "preflight.sh"), d])
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("CLEAR.", p.stdout)
        p = run_py("app-comply", "store_policy_check.py", d, "--quiet")
        self.assertEqual(p.returncode, 0, p.stdout)


class Preflight(TempCase):
    def test_bad_app_blocked_with_every_planted_problem(self):
        p = run(["bash", script("app-factory", "preflight.sh"), self.fixture("bad-app")])
        self.assertEqual(p.returncode, 1)
        out = p.stdout
        self.assertIn("BLOCKED.", out)
        for needle in ("Placeholder package", "Possible secret keys", "Cleartext HTTP allowed", "App Transport Security disabled",
                       "android:debuggable", "targetSdkVersion 34 is below 36", "Empty or generic iOS permission usage strings",
                       "No privacy policy link", "no in-app account deletion", "without a Restore Purchases",
                       "Tokens stored in AsyncStorage", "Sensitive Android permissions", "AI SDK in the app",
                       "without App Tracking Transparency", "no report / block", "EAS Update without code signing"):
            self.assertIn(needle, out)
        m = re.search(r"(\d+) blocker\(s\), (\d+) warning\(s\)", out)
        self.assertGreaterEqual(int(m.group(1)), 10)

    def test_good_app_clear(self):
        p = run(["bash", script("app-factory", "preflight.sh"), self.fixture("good-app")])
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("0 blocker(s), 0 warning(s)", p.stdout)

    def test_target_sdk_override_and_usage(self):
        p = run(["bash", script("app-factory", "preflight.sh"), self.fixture("good-app")],
                env={"MIN_TARGET_SDK": "37", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})
        self.assertEqual(p.returncode, 1)
        p = run(["bash", script("app-factory", "preflight.sh"), self.tmp / "missing"])
        self.assertEqual(p.returncode, 2)


class RunGates(TempCase):
    def gates(self, app, *extra):
        return run(["bash", script("app-factory", "run_gates.sh"), app, *extra])

    def test_good_app_ready(self):
        app = self.fixture("good-app")
        p = self.gates(app, "--mobsf-report", ROOT / "tests/fixtures/mobsf-appsec-report.json", "--version", "1.0.0")
        # The MobSF fixture has highs, so the security gate (optional but run) fails the release.
        self.assertEqual(p.returncode, 1, p.stdout[-2000:])
        md = (app / "reports" / "release-report.md").read_text()
        self.assertIn("| 5 | Security: MobSF / MASVS | FAIL", md)
        p = self.gates(app, "--version", "1.0.0")
        self.assertEqual(p.returncode, 0, p.stdout[-2000:])
        md = (app / "reports" / "release-report.md").read_text()
        self.assertIn("READY FOR SUBMISSION", md)
        for f in ("inventory.json", "preflight.json", "privacy.json", "store-policy.json",
                  "data-safety-draft.md", "privacy-labels-draft.md", "data-inventory-draft.md"):
            self.assertTrue((app / "reports" / f).exists(), f)

    def test_bad_app_blocked(self):
        app = self.fixture("bad-app")
        p = self.gates(app)
        self.assertEqual(p.returncode, 1)
        res = self.load(app / "reports" / "preflight.json")
        self.assertGreaterEqual(res["blockers"], 10)
        md = (app / "reports" / "release-report.md").read_text()
        self.assertIn("BLOCKED", md)
        self.assertEqual(md.count("| FAIL |"), 4)


class SkillIntegrity(unittest.TestCase):
    def test_every_skill_has_valid_front_matter(self):
        skills = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))
        self.assertEqual(skills, ["app-build", "app-comply", "app-factory", "app-release", "app-secure", "app-spec", "app-test"])
        for name in skills:
            text = (SKILLS / name / "SKILL.md").read_text()
            m = re.match(r"---\nname: ([a-z0-9-]+)\ndescription: (.+?)\n---\n", text, re.S)
            self.assertTrue(m, name)
            self.assertEqual(m.group(1), name)
            self.assertLess(len(m.group(2)), 1024, name)

    def test_paths_mentioned_in_skills_exist(self):
        for md in SKILLS.glob("*/SKILL.md"):
            for rel in re.findall(r"`((?:scripts|references|templates|data)/[A-Za-z0-9_./-]+)`", md.read_text()):
                self.assertTrue((md.parent / rel).exists(), f"{md.parent.name}: {rel}")
            for skill, rel in re.findall(r"`(?:skills/)?(app-[a-z]+)/((?:scripts|references|templates|data)/[A-Za-z0-9_./-]+)`", md.read_text()):
                self.assertTrue((SKILLS / skill / rel).exists(), f"{md.parent.name}: {skill}/{rel}")

    def test_catalog_is_consistent(self):
        cat = json.loads((SKILLS / "app-comply" / "data" / "sdk-catalog.json").read_text())
        for name, entry in cat["sdks"].items():
            if "alias" in entry:
                self.assertIn(entry["alias"], cat["sdks"], name)
                continue
            for key in ("name", "domains", "data"):
                self.assertIn(key, entry, name)
            for d in entry["data"]:
                self.assertIn(" / ", d["play"], name)
                self.assertIn(" / ", d["apple"], name)
        for perm, item in cat["permissions"].items():
            self.assertIn(item, cat["items"], perm)

    def test_scripts_are_executable(self):
        import os
        for p in SKILLS.glob("*/scripts/*"):
            if p.suffix in (".py", ".sh") and not p.name.startswith("_"):
                self.assertTrue(os.access(p, os.X_OK), p.name)


if __name__ == "__main__":
    unittest.main()
