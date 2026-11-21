---
name: app-release
description: Ship a mobile app to Google Play and the App Store and operate it - production EAS builds, Play closed testing with the 12-tester / 14-day rule tracked from a CSV, TestFlight, store listings, submission and rejection handling, staged rollout with Play vitals thresholds, and a generated release-report.md that collects the evidence from every gate. Use when preparing a submission, applying for Play production access, rolling out, or writing the release evidence pack.
---

# app-release — Ship and operate (app-factory phases 7–8)

Commands in detail: `app-factory/references/runbook.md` steps 11–17.

## 1. Production builds

```bash
git tag v1.0.0
eas build --profile production --platform all      # signed .aab + .ipa, build numbers auto-incremented
```

Re-run `app-secure` and `app-comply` on these exact binaries.

## 2. Closed testing (new personal Play accounts) — `scripts/testers.py`

Play requires **12+ testers opted in for 14 continuous days** before you can apply for production. Track real opt-ins in `testers.csv`:

```csv
email,opted_in,opted_out
asha@example.com,2026-11-01,
ravi@example.com,2026-11-01,2026-11-09
```

```bash
python3 skills/app-release/scripts/testers.py testers.csv --json reports/testers.json
```

It reports how many testers are active today, the current continuous streak, and the earliest date you can apply (or how many more testers to recruit). Exit 0 when met. Never invent testers: Play checks real opt-ins.

```bash
eas submit --platform android --profile production   # Play internal → closed track
eas submit --platform ios --profile production       # TestFlight → App Store Connect
```

## 3. Listings and submission

Accurate screenshots of the app in use for every required size; no prices, "#1", or the other platform. Apple: demo account + review notes (`app-factory/templates/review-notes.md`). If rejected: fix the root cause of the cited guideline, answer in Resolution Center / Play inbox, resubmit; appeal only if the reviewer misread the app.

## 4. Release evidence pack — `scripts/release_report.py`

```bash
python3 skills/app-release/scripts/release_report.py --reports reports --version 1.0.0 \
    [--manual docs/manual-checks.json]
```

Collects every gate's JSON (`inventory_lint`, `preflight`, `explore`, `mobsf_gate`, `privacy_scan`, `store_policy_check`, `testers`, `ota_check`) into `reports/release-report.md`: a gate table with evidence files, all blockers with fixes, the manual store-console checklist (tick items via `--manual` JSON `{"item text": true}`), and warnings that need a written reason. Exit 1 when a required gate failed or never ran. `app-factory/scripts/run_gates.sh` runs everything and calls this last.

## 5. Rollout and operate

| Step | Rule |
|---|---|
| Staged rollout | Play 1% → 5% → 20% → 50% → 100%; Apple 7-day phased release |
| Halt when | User-perceived crash rate nears **1.09%** or ANR **0.47%** (per device model 8%), or a key funnel drops |
| Hotfix | JS-only: signed OTA after `ota_check.py` passes; anything else: store build |
| Yearly | Expo SDK upgrade before Google's 31 Aug target-API deadline and Apple's spring SDK floor |
| Monthly | Check the deadline table in `app-factory/references/compliance.md`; re-run gates after any new SDK |

## Gate

Approved on both stores · `release_report.py` exits 0 · rollout reaches 100% with vitals under threshold.
