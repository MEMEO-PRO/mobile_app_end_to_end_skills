"""app-test: explore_to_maestro.py · app-release: testers.py, release_report.py."""
from __future__ import annotations

import json
import unittest
from datetime import date, timedelta

from util import FIX, TempCase, run_py

LOG = FIX / "explore-log.json"


class Explore(TempCase):
    def explore(self, log, *extra):
        out = self.tmp / "explore.json"
        p = run_py("app-test", "explore_to_maestro.py", log, "--out", self.tmp / "flows",
                   "--report", self.tmp / "bug-report.md", "--json", out, *extra)
        return p, self.load(out)

    def test_crash_fails_and_writes_repro_flows(self):
        p, res = self.explore(LOG)
        self.assertEqual(p.returncode, 1)
        issues = res["report"]["issues"]
        self.assertEqual([i["type"] for i in issues], ["error", "crash"])
        self.assertEqual([i["severity"] for i in issues], ["P1", "P0"])
        flows = sorted((self.tmp / "flows").glob("*.yaml"))
        self.assertEqual(len(flows), 2)
        err = flows[0].read_text()
        self.assertTrue(err.startswith("appId: in.memeo.goodbudget"))
        for line in ('- tapOn: "Sign in"', '    id: "email"', '- inputText: "-12.50"', '    point: "540,1650"',
                     '- assertVisible: "Enter an amount above 0"'):
            self.assertIn(line, err)
        crash = flows[1].read_text()
        self.assertIn('- tapOn: "Scan receipt"', crash)
        self.assertIn("direction: UP", crash)

    def test_repro_starts_at_last_launch(self):
        log = json.loads(LOG.read_text())
        log["steps"].append({"action": "tap", "text": "Export", "event": {"type": "ui", "message": "Export button cut off"}})
        path = self.tmp / "log.json"
        path.write_text(json.dumps(log))
        self.explore(path)
        flow = sorted((self.tmp / "flows").glob("03-*.yaml"))[0].read_text()
        self.assertNotIn("Sign in", flow)          # replay begins at the second launch
        self.assertIn('- tapOn: "Settings"', flow)

    def test_report_and_coverage(self):
        self.explore(LOG, "--expect-screens", "Home,Settings,Budgets")
        md = (self.tmp / "bug-report.md").read_text()
        self.assertIn("App closes when camera permission is denied", md)
        self.assertIn("**Not reached:** Budgets", md)
        self.assertIn("maestro test", md)

    def test_clean_session_passes(self):
        log = {"app_id": "a.b", "steps": [{"action": "launch", "screen": "Home"}, {"action": "assert", "text": "Hi"}]}
        path = self.tmp / "clean.json"
        path.write_text(json.dumps(log))
        p, res = self.explore(path)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(res["verdict"], "pass")

    def test_missing_app_id_is_usage_error(self):
        path = self.tmp / "bad.json"
        path.write_text('{"steps": []}')
        p = run_py("app-test", "explore_to_maestro.py", path, "--report", self.tmp / "r.md")
        self.assertEqual(p.returncode, 2)


class Testers(TempCase):
    TODAY = date(2026, 11, 21)

    def csv(self, rows):
        path = self.tmp / "t.csv"
        path.write_text("email,opted_in,opted_out\n" + "\n".join(",".join(r) for r in rows) + "\n")
        return path

    def d(self, days_ago):
        return (self.TODAY - timedelta(days=days_ago)).isoformat()

    def check(self, rows):
        out = self.tmp / "t.json"
        p = run_py("app-release", "testers.py", self.csv(rows), "--today", self.TODAY.isoformat(), "--json", out)
        return p, self.load(out)

    def test_twelve_testers_for_fourteen_days_meets_rule(self):
        p, res = self.check([(f"t{i}@x.com", self.d(20), "") for i in range(12)])
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertTrue(res["met"])
        self.assertEqual(res["first_met_on"], self.d(7))

    def test_eleven_testers_is_not_enough(self):
        p, res = self.check([(f"t{i}@x.com", self.d(30), "") for i in range(11)])
        self.assertEqual(p.returncode, 1)
        self.assertIn("recruit 1 more", res["summary"])

    def test_opt_out_breaks_the_streak(self):
        rows = [(f"t{i}@x.com", self.d(20), "") for i in range(11)] + [("t11@x.com", self.d(20), self.d(10)),
                                                                        ("t12@x.com", self.d(5), "")]
        p, res = self.check(rows)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(res["streak_days"], 6)
        self.assertEqual(res["eligible_on"], (self.TODAY + timedelta(days=9)).isoformat())

    def test_bad_rows_are_reported(self):
        rows = [(f"t{i}@x.com", self.d(20), "") for i in range(12)] + [("not-an-email", self.d(3), ""), ("z@x.com", "yesterday", "")]
        p, res = self.check(rows)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(len(res["problems"]), 2)


class ReleaseReport(TempCase):
    def write(self, name, tool, verdict, findings=()):
        (self.tmp / "reports").mkdir(exist_ok=True)
        (self.tmp / "reports" / name).write_text(json.dumps(
            {"tool": tool, "verdict": verdict, "summary": f"{tool} {verdict}", "findings": list(findings)}))

    def test_all_required_pass(self):
        for n, t in (("i.json", "inventory_lint"), ("p.json", "preflight"), ("pr.json", "privacy_scan"), ("s.json", "store_policy_check")):
            self.write(n, t, "pass")
        self.write("o.json", "ota_check", "warn", [{"id": "X", "severity": "warning", "title": "JS deps changed"}])
        p = run_py("app-release", "release_report.py", "--reports", self.tmp / "reports", "--version", "1.2.0", "--app", "Demo")
        self.assertEqual(p.returncode, 0, p.stdout)
        md = (self.tmp / "reports" / "release-report.md").read_text()
        self.assertIn("# Release report — Demo 1.2.0", md)
        self.assertIn("READY FOR SUBMISSION", md)
        self.assertIn("[ota_check] JS deps changed — reason: ____", md)

    def test_failed_or_missing_gate_blocks(self):
        self.write("p.json", "preflight", "fail", [{"id": "S", "severity": "blocker", "title": "secret", "fix": "rotate"}])
        p = run_py("app-release", "release_report.py", "--reports", self.tmp / "reports")
        self.assertEqual(p.returncode, 1)
        md = (self.tmp / "reports" / "release-report.md").read_text()
        self.assertIn("BLOCKED", md)
        self.assertIn("- [preflight] secret — fix: rotate", md)
        self.assertIn("NOT RUN", md)

    def test_manual_ticks(self):
        self.write("p.json", "preflight", "pass")
        tick = self.tmp / "manual.json"
        tick.write_text(json.dumps({"Store listing text and screenshots final": True}))
        run_py("app-release", "release_report.py", "--reports", self.tmp / "reports", "--manual", tick)
        md = (self.tmp / "reports" / "release-report.md").read_text()
        self.assertIn("- [x] Gate 7: Store listing text and screenshots final", md)


if __name__ == "__main__":
    unittest.main()
