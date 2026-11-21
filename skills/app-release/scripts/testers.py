#!/usr/bin/env python3
"""Closed-testing tracker for Google Play's rule for new personal developer accounts:
at least 12 testers opted in for 14 continuous days before applying for production.

Input CSV (header required):  email,opted_in,opted_out
  - dates as YYYY-MM-DD; opted_out empty while still in the test
  - one row per opt-in period (a tester who left and rejoined gets two rows)

Usage:
  testers.py testers.csv [--today 2026-11-21] [--min-testers 12] [--days 14] [--json reports/testers.json]
Exit: 0 requirement met, 1 not met yet, 2 bad input.
Never invent testers: Play checks real opt-ins, and fake ones can get the account banned.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def parse(path: Path) -> tuple[list[tuple[str, date, date | None]], list[str]]:
    rows, problems = [], []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        need = {"email", "opted_in"}
        if not reader.fieldnames or not need <= {h.strip() for h in reader.fieldnames}:
            raise ValueError("CSV needs columns: email,opted_in[,opted_out]")
        for n, r in enumerate(reader, 2):
            email = (r.get("email") or "").strip().lower()
            if not EMAIL.match(email):
                problems.append(f"line {n}: invalid email '{email}'")
                continue
            try:
                start = date.fromisoformat((r.get("opted_in") or "").strip())
                end_s = (r.get("opted_out") or "").strip()
                end = date.fromisoformat(end_s) if end_s else None
            except ValueError:
                problems.append(f"line {n}: bad date")
                continue
            if end and end < start:
                problems.append(f"line {n}: opted_out before opted_in")
                continue
            rows.append((email, start, end))
    return rows, problems


def active_on(rows, day: date) -> set[str]:
    return {e for e, s, t in rows if s <= day and (t is None or day < t)}


def evaluate(rows, today: date, min_testers: int, days: int) -> dict:
    if not rows:
        return {"met": False, "active_today": 0, "streak_days": 0, "streak_start": None, "eligible_on": None}
    first = min(s for _, s, _ in rows)
    streak, streak_start, met_on = 0, None, None
    d = first
    while d <= today:
        if len(active_on(rows, d)) >= min_testers:
            if streak == 0:
                streak_start = d
            streak += 1
            if streak >= days and met_on is None:
                met_on = d
        else:
            streak, streak_start = 0, None
        d += timedelta(days=1)
    active = active_on(rows, today)
    if met_on:
        eligible = met_on + timedelta(days=1)
    elif len(active) >= min_testers:
        eligible = today + timedelta(days=days - streak + 1)
    else:
        eligible = None
    return {"met": met_on is not None, "active_today": len(active), "streak_days": streak,
            "streak_start": streak_start.isoformat() if streak_start else None,
            "eligible_on": eligible.isoformat() if eligible else None, "first_met_on": met_on.isoformat() if met_on else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--min-testers", type=int, default=12)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--json", dest="json_path")
    a = ap.parse_args(argv)
    try:
        rows, problems = parse(Path(a.csv))
        today = date.fromisoformat(a.today)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    r = evaluate(rows, today, a.min_testers, a.days)
    need = max(0, a.min_testers - r["active_today"])
    if r["met"]:
        msg = f"Requirement met on {r['first_met_on']}: you can apply for production access."
    elif need:
        msg = f"{r['active_today']} testers opted in today; recruit {need} more, then keep {a.min_testers}+ opted in for {a.days} days."
    else:
        msg = f"{r['streak_days']}/{a.days} continuous days with {a.min_testers}+ testers; earliest apply date {r['eligible_on']} if nobody opts out."
    out = {"tool": "testers", "verdict": "pass" if r["met"] else "fail", "blockers": 0 if r["met"] else 1,
           "warnings": len(problems), "summary": msg, **r, "problems": problems,
           "findings": [{"id": "PLAY-CLOSED-TEST", "severity": "pass" if r["met"] else "blocker", "title": msg}]
           + [{"id": "CSV", "severity": "warning", "title": p} for p in problems]}
    if a.json_path:
        Path(a.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_path).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    for p in problems:
        print(f"WARNING  {p}")
    print(msg)
    return 0 if r["met"] else 1


if __name__ == "__main__":
    sys.exit(main())
