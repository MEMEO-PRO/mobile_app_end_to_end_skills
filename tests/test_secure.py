"""app-secure: mobsf_gate.py, offline and against a mock MobSF server."""
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from util import FIX, PY, TempCase, run, run_py, script

APPSEC_REPORT = FIX / "mobsf-appsec-report.json"
LEGACY_REPORT = FIX / "mobsf-legacy-report.json"


class Offline(TempCase):
    def gate(self, report, *extra):
        out, md = self.tmp / "s.json", self.tmp / "s.md"
        p = run_py("app-secure", "mobsf_gate.py", "--report", report, "--json", out, "--md", md, "--quiet", *extra)
        return p, self.load(out), md.read_text()

    def test_high_findings_fail_the_gate(self):
        p, res, md = self.gate(APPSEC_REPORT)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(res["verdict"], "fail")
        self.assertEqual(res["score"], 42)
        self.assertGreaterEqual(res["by_masvs"]["NETWORK"], 1)
        self.assertGreaterEqual(res["by_masvs"]["STORAGE"], 1)
        self.assertIn("MASVS-NETWORK", md)

    def test_limits_are_configurable(self):
        p, res, _ = self.gate(APPSEC_REPORT, "--max-high", "5")
        self.assertEqual(p.returncode, 0)
        p, res, _ = self.gate(APPSEC_REPORT, "--max-high", "5", "--min-score", "60")
        self.assertEqual(p.returncode, 1)
        self.assertIn("score 42 < 60", res["summary"])

    def test_legacy_report_sections_are_mapped(self):
        p, res, _ = self.gate(LEGACY_REPORT)
        self.assertEqual(p.returncode, 1)
        groups = {k for k, v in res["by_masvs"].items() if v}
        self.assertTrue({"CRYPTO", "PLATFORM", "NETWORK"} <= groups, groups)

    def test_missing_api_key_is_usage_error(self):
        p = run([PY, script("app-secure", "mobsf_gate.py"), "--file", APPSEC_REPORT],
                env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(p.returncode, 2)


class MockMobSF(BaseHTTPRequestHandler):
    calls: list = []

    def log_message(self, *a):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        MockMobSF.calls.append((self.path, self.headers.get("Authorization"), body[:200]))
        if self.headers.get("Authorization") != "test-key":
            self.send_response(401); self.end_headers(); return
        payload = {"/api/v1/upload": {"hash": "abc123", "scan_type": "apk", "file_name": "app.apk"},
                   "/api/v1/scan": {"status": "ok"},
                   "/api/v1/report_json": json.loads(APPSEC_REPORT.read_text()),
                   "/api/v1/scorecard": json.loads(APPSEC_REPORT.read_text())["appsec"]}.get(self.path)
        if payload is None:
            self.send_response(404); self.end_headers(); return
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class Online(TempCase):
    def test_upload_scan_report_flow(self):
        server = HTTPServer(("127.0.0.1", 0), MockMobSF)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        try:
            apk = self.tmp / "app.apk"
            apk.write_bytes(b"PK\x03\x04fake")
            out = self.tmp / "s.json"
            p = run_py("app-secure", "mobsf_gate.py", "--file", apk, "--server", f"http://127.0.0.1:{server.server_port}",
                       "--api-key", "test-key", "--json", out, "--md", self.tmp / "s.md", "--quiet",
                       "--save-report", self.tmp / "raw.json")
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(p.returncode, 1, p.stderr)
        paths = [c[0] for c in MockMobSF.calls]
        self.assertEqual(paths[:3], ["/api/v1/upload", "/api/v1/scan", "/api/v1/report_json"])
        self.assertTrue(all(c[1] == "test-key" for c in MockMobSF.calls))
        self.assertIn(b"filename=\"app.apk\"", MockMobSF.calls[0][2])
        self.assertTrue((self.tmp / "raw.json").exists())
        self.assertEqual(self.load(out)["score"], 42)

    def test_unreachable_server_is_usage_error(self):
        apk = self.tmp / "app.apk"
        apk.write_bytes(b"x")
        p = run_py("app-secure", "mobsf_gate.py", "--file", apk, "--server", "http://127.0.0.1:9", "--api-key", "k")
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
