"""Shared helpers for the test suite (standard library only)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
FIX = ROOT / "tests" / "fixtures"
PY = sys.executable


def script(skill: str, name: str) -> Path:
    return SKILLS / skill / "scripts" / name


def run(cmd: list, cwd: Path | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([str(c) for c in cmd], cwd=cwd, capture_output=True, text=True, env=env, timeout=120)


def run_py(skill: str, name: str, *args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return run([PY, script(skill, name), *args], cwd=cwd)


class TempCase(unittest.TestCase):
    """Gives each test a private temp dir and copies of the fixtures."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="appfactory-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fixture(self, name: str) -> Path:
        dst = self.tmp / name
        shutil.copytree(FIX / name, dst)
        if name == "bad-app":
            # The planted secret is added at runtime so no key-shaped string is stored in the repository.
            fake_key = "sk_" + "live_" + "0" * 24
            with open(dst / "src" / "api.ts", "a", encoding="utf-8") as fh:
                fh.write(f'export const KEY = "{fake_key}";\n')
        return dst

    def load(self, p: Path) -> dict:
        return json.loads(Path(p).read_text(encoding="utf-8"))

    def ids(self, res: dict, severity: str | None = None) -> set[str]:
        return {f["id"] for f in res["findings"] if severity is None or f["severity"] == severity}
