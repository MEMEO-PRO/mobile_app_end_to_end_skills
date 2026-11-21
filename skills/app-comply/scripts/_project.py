"""Shared helpers for reading a mobile app project (Expo / React Native / native). Standard library only."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", "Pods", "build", ".expo", "dist", ".gradle", "DerivedData",
             "coverage", ".next", "reports", "__pycache__", ".maestro"}
SOURCE_EXT = {".js", ".jsx", ".ts", ".tsx", ".kt", ".java", ".swift", ".m", ".mm", ".dart"}
CONFIG_NAMES = ("app.json", "app.config.ts", "app.config.js")


def walk(root: Path, exts: set[str] | None = None):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            p = Path(dirpath) / f
            if exts is None or p.suffix in exts:
                yield p


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


class Project:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        pkg = self.root / "package.json"
        self.package = {}
        if pkg.exists():
            try:
                self.package = json.loads(read(pkg))
            except json.JSONDecodeError:
                self.package = {}
        self.deps = {**self.package.get("dependencies", {}), **self.package.get("devDependencies", {})}
        self.runtime_deps = dict(self.package.get("dependencies", {}))
        self.config_files = [self.root / n for n in CONFIG_NAMES if (self.root / n).exists()]
        self.config_text = "\n".join(read(p) for p in self.config_files)
        self.manifests = [p for p in walk(self.root) if p.name == "AndroidManifest.xml"]
        self.plists = [p for p in walk(self.root) if p.name == "Info.plist"]
        self.gradle = [p for p in walk(self.root) if p.name in ("build.gradle", "build.gradle.kts", "gradle.properties")]
        self.native_text = "\n".join(read(p) for p in self.manifests + self.plists + self.gradle)
        self._sources = None

    @property
    def sources(self) -> dict[Path, str]:
        if self._sources is None:
            self._sources = {p: read(p) for p in walk(self.root, SOURCE_EXT)}
        return self._sources

    @property
    def is_expo(self) -> bool:
        return "expo" in self.deps

    def rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.root))
        except ValueError:
            return str(p)

    def grep(self, pattern: str, flags=re.I) -> list[str]:
        rx = re.compile(pattern, flags)
        return [self.rel(p) for p, t in self.sources.items() if rx.search(t)]

    def all_config(self) -> str:
        return self.config_text + "\n" + self.native_text

    def permissions(self) -> set[str]:
        """Android permissions + iOS usage-description keys declared in config and native files."""
        text = self.all_config()
        perms = set(re.findall(r"android\.permission\.([A-Z_]+)", text))
        # Expo config arrays: permissions: ["CAMERA", ...]
        for block in re.findall(r"permissions\"?\s*:\s*\[([^\]]*)\]", self.config_text):
            perms.update(re.findall(r"[\"']([A-Z_]{4,})[\"']", block))
        blocked = set()
        for block in re.findall(r"blockedPermissions\"?\s*:\s*\[([^\]]*)\]", self.config_text):
            blocked.update(re.findall(r"(?:android\.permission\.)?([A-Z_]{4,})[\"']", block))
        perms -= blocked
        perms.update(re.findall(r"(NS[A-Za-z]+UsageDescription)", text))
        return perms

    def target_sdk(self) -> int | None:
        vals = [int(v) for v in re.findall(r"targetSdk(?:Version)?\"?\s*[:=]?\s*[\"']?(\d{2})", self.all_config())]
        return min(vals) if vals else None

    def hosts(self) -> dict[str, list[str]]:
        """Remote hosts referenced in source code -> files."""
        out: dict[str, list[str]] = {}
        rx = re.compile(r"https?://([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(/[^\s\"'`)]*)?")
        ignore = re.compile(r"(^|\.)(w3\.org|apple\.com|android\.com|schemas\.|example\.(com|org)|localhost|reactnative\.dev|expo\.dev|github\.com)$")
        # Pages opened for the user to read (policy, terms, help) are links, not data destinations.
        page = re.compile(r"^/(privacy|terms|eula|legal|support|help|faq|about|contact|delete[-_]?account|account[-_]?deletion)\b", re.I)
        for p, t in self.sources.items():
            for h, path in rx.findall(t):
                h = h.lower()
                if ignore.search(h) or (path and page.search(path)):
                    continue
                out.setdefault(h, [])
                if self.rel(p) not in out[h]:
                    out[h].append(self.rel(p))
        return out


def result(tool: str, findings: list[dict], summary: str = "", extra: dict | None = None) -> dict:
    blockers = sum(1 for f in findings if f.get("severity") == "blocker")
    warnings = sum(1 for f in findings if f.get("severity") == "warning")
    verdict = "fail" if blockers else ("warn" if warnings else "pass")
    out = {"tool": tool, "verdict": verdict, "blockers": blockers, "warnings": warnings,
           "summary": summary or f"{blockers} blocker(s), {warnings} warning(s)", "findings": findings}
    if extra:
        out.update(extra)
    return out


def emit(res: dict, json_path: str | None, quiet: bool = False) -> int:
    if json_path:
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(json_path).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    if not quiet:
        icon = {"blocker": "BLOCKER", "warning": "WARNING", "manual": "MANUAL ", "pass": "ok     "}
        for f in res["findings"]:
            print(f"{icon.get(f.get('severity'), '       ')}  [{f.get('id', '')}] {f.get('title', '')}")
            if f.get("fix") and f.get("severity") in ("blocker", "warning", "manual"):
                print(f"         fix: {f['fix']}")
        print(f"\n{res['tool']}: {res['summary']} -> {res['verdict'].upper()}")
    return 1 if res["verdict"] == "fail" else 0
