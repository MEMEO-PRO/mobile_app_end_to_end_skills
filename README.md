# Mobile App End-to-End Skills

Agent skills and tools that take a mobile app from **idea to live on Google Play and the Apple App Store**, and keep it compliant afterwards. They implement the production pipeline real teams use: each phase ends with a **gate**, and nothing moves on until the gate passes. Every automated gate writes evidence, and one command collects it into a release report.

Most first-time rejections come from paperwork and policy, not code: a Data safety form that doesn't match what the SDKs send, a missing account-deletion path, an unjustified permission, a missing demo account. These skills catch those before a reviewer does.

- **One orchestrator + six phase skills:** spec, build, test, secure, comply, release.
- **Eleven tools, all tested:** Python 3.9+ standard library and Bash only. No `pip install`, no Node needed to run them.
- **Expo by default:** one TypeScript codebase produces the Android `.aab` and the iOS `.ipa`, with a native Kotlin/Swift path for apps that need heavy native work.
- **Global compliance:** Google Play and App Store rules in detail, plus data-protection law in 45+ jurisdictions on every continent.
- **55 automated tests:** run locally in about 5 seconds, covering a deliberately broken app and a store-ready app.

> Engineering guidance, not legal advice. Store rules and laws change monthly. Every reference links its source, and items marked † or "unverified" were not confirmed against an official page. Check the source before relying on a date.

---

## Contents

1. [How it works](#how-it-works)
2. [Install](#install)
3. [Quick start](#quick-start)
4. [The skills](#the-skills)
5. [The tools](#the-tools)
6. [Run every gate at once](#run-every-gate-at-once)
7. [What a run looks like](#what-a-run-looks-like)
8. [Use it in CI](#use-it-in-ci)
9. [Reference material](#reference-material)
10. [Testing this repository](#testing-this-repository)
11. [Limits](#limits)
12. [Repository layout](#repository-layout)
13. [Contributing](#contributing)

---

## How it works

```
  PLAN ─gate─▶ BUILD ─gate─▶ VERIFY ─gate─▶ COMPLY ─gate─▶ SHIP ─gate─▶ OPERATE
 app-spec     app-build     app-test        app-comply     app-release   app-release
                            app-secure                                   app-comply (OTA)
    ▲                                                                        │
    └──────────────── production data feeds the next plan ───────────────────┘
```

| # | Phase | Skill | Gate (must pass to move on) | Automated by |
|---|---|---|---|---|
| 1 | Plan: accounts, brief, spec, data inventory, design | `app-spec` | Accounts active · inventory complete · compliance screens designed | `inventory_lint.py` |
| 2 | Legal scoping per launch country | `app-spec` | Registrations filed · breach runbook · children's consent age wired in | manual + `legal-global.md` |
| 3 | Build: project, architecture, native config | `app-build` | Real-device builds · justified permissions only · account deletion · no preflight blockers | `scaffold.py`, `preflight.sh` |
| 4 | Verify quality | `app-test` | Release build crash-free on the device matrix · E2E green · every screen reached | `explore_to_maestro.py` |
| 5 | Verify security (OWASP MASVS) | `app-secure` | No high MobSF findings · no secrets · traffic matches inventory · signed OTA | `mobsf_gate.py` |
| 6 | Compliance pack | `app-comply` | Privacy forms match code · store policy clean · documents live · demo account works | `privacy_scan.py`, `store_policy_check.py` |
| 7 | Ship: production build, test tracks, listings, review | `app-release` | 12 testers × 14 days (new Play accounts) · approved on both stores | `testers.py`, `release_report.py` |
| 8 | Operate: rollout, hotfixes, yearly upgrades | `app-release`, `app-comply` | Vitals under Play thresholds · each change routed OTA vs store correctly | `ota_check.py` |

The orchestrator, `skills/app-factory/SKILL.md`, walks an agent through the phases in order and hands each one to its phase skill.

## Install

The skills are plain folders with a `SKILL.md` (YAML front matter + instructions), so they work with any coding agent that loads skill folders.

```bash
git clone https://github.com/MEMEO-PRO/mobile_app_end_to_end_skills.git
cd mobile_app_end_to_end_skills
```

Link all seven skills into your agent's skills directory (change the path to the one your agent reads):

```bash
mkdir -p ~/.agents/skills && for s in skills/*/; do ln -sfn "$PWD/$s" ~/.agents/skills/$(basename "$s"); done
```

Or with the open skills CLI:

```bash
npx skills add MEMEO-PRO/mobile_app_end_to_end_skills
```

Requirements to run the tools: `bash`, `python3` 3.9 or newer, and `git` for the OTA check. Optional: Docker for MobSF, [Maestro](https://github.com/mobile-dev-inc/Maestro) to run the generated flows, [mobile-mcp](https://github.com/mobile-next/mobile-mcp) for agent-driven device testing.

Recommended companion skills, which the runbook calls at the right steps: [expo/skills](https://github.com/expo/skills), [android/skills](https://github.com/android/skills) and [mjmirza/app-store-compliance](https://github.com/mjmirza/app-store-compliance).

## Quick start

Ask your agent, for example:

- "Use app-factory to take my expense-tracker idea to both stores."
- "Run app-factory's gates on this project and fix every blocker."
- "Can this change go out as an OTA update, or does it need store review?"
- "We're launching in Brazil, Turkey and Indonesia. What must we do first?"
- "Apple rejected us under 5.1.1(v). Fix it."

Or drive the tools yourself on a new Expo app:

```bash
npx create-expo-app@latest my-app && cd my-app
python3 ../mobile_app_end_to_end_skills/skills/app-build/scripts/scaffold.py \
    --name "My App" --package com.acme.myapp --website https://myapp.acme.com
bash ../mobile_app_end_to_end_skills/skills/app-factory/scripts/run_gates.sh .
open reports/release-report.md
```

## The skills

| Skill | What the agent does with it |
|---|---|
| [`app-factory`](skills/app-factory/SKILL.md) | Orchestrator: the eight phases, their gates, the top rejection causes, and `run_gates.sh`. Holds the long reference files and templates. |
| [`app-spec`](skills/app-spec/SKILL.md) | Brief, spec, switched-on rule areas (accounts, kids, UGC, payments, AI, health/finance, sensitive permissions, countries), and the data inventory every privacy form is built from. |
| [`app-build`](skills/app-build/SKILL.md) | Expo project with hardened config from day one: target API 36, fingerprint runtime, signed OTA, privacy manifest, export compliance, blocked permissions, secure token storage, threat model. Native path described too. |
| [`app-test`](skills/app-test/SKILL.md) | Release-build testing, a device matrix, the Play pre-launch report, and agent exploratory testing that turns every bug into a Maestro repro flow. |
| [`app-secure`](skills/app-secure/SKILL.md) | OWASP MASVS gate: MobSF scan through its REST API, findings grouped by MASVS area, plus the checks MobSF can't make (secrets, token storage, traffic vs inventory, OTA signing). |
| [`app-comply`](skills/app-comply/SKILL.md) | Two-store pre-review: drafts Data safety, privacy labels and the privacy-manifest list from the real code; checks store policy and listing text; decides OTA vs store build. |
| [`app-release`](skills/app-release/SKILL.md) | Production builds, the 12-tester / 14-day closed test, listings, submission and rejections, staged rollout against Play vitals thresholds, and the release evidence pack. |

## The tools

Every tool prints readable output, can write a JSON result (`--json`), and uses the same exit codes: **0** pass (warnings allowed), **1** gate failed, **2** usage or input error. Each JSON result has the shape `{"tool", "verdict": "pass|warn|fail", "summary", "findings": [{"id", "severity": "blocker|warning|manual|pass", "title", "fix"}]}`, which `release_report.py` merges.

### `app-factory/scripts/preflight.sh` — fast pre-submission scan

```bash
bash skills/app-factory/scripts/preflight.sh /path/to/app        # MIN_TARGET_SDK=35 to override the floor
```

Ten sections, about 30 checks: placeholder `com.example` ids · secret keys (Stripe live, AWS, private keys, GitHub, Slack, OpenAI/Anthropic, Supabase service role) · secret `EXPO_PUBLIC_*` variables · tokens in AsyncStorage · cleartext HTTP, disabled App Transport Security, `debuggable` · plain `http://` URLs · target SDK below 36 · sensitive Android permissions · empty or generic iOS usage strings · missing privacy manifest, export compliance, data inventory, privacy-policy link · accounts without deletion · Google login without Sign in with Apple · IAP without restore or terms · external payment SDKs · AI SDKs without consent · ad SDKs without App Tracking Transparency · UGC without report/block · OTA without code signing or a runtime-version policy. Prints `BLOCKED.` or `CLEAR.`

### `app-spec/scripts/inventory_lint.py` — is the data inventory complete?

```bash
python3 skills/app-spec/scripts/inventory_lint.py docs/data-inventory.md --json reports/inventory.json
```

Checks every required column exists and every row is filled: no blanks, `<placeholders>` or `TBD`. Shared items must name a recipient. Yes/No columns must start with Yes or No, and the children section must be answered. Rows used for tracking produce a warning, because they need App Tracking Transparency.

### `app-build/scripts/scaffold.py` — store-ready config for a new app

```bash
python3 skills/app-build/scripts/scaffold.py --name "My App" --package com.acme.myapp \
    [--bundle-id com.acme.myapp.ios] [--website https://myapp.acme.com] [--owner acme] [--dir .] [--force]
```

Writes `app.config.ts`, `eas.json`, `.maestro/smoke.yaml`, `src/config/legal.ts`, `docs/data-inventory.md`, `docs/threat-model.md`, `docs/legal.md`, `store/listing.json` and `.github/workflows/app-gates.yml`. Refuses to overwrite files without `--force`, and rejects placeholder or invalid ids. A freshly scaffolded project passes `preflight.sh` and `store_policy_check.py` (tested).

### `app-test/scripts/explore_to_maestro.py` — exploratory testing → repro flows

```bash
python3 skills/app-test/scripts/explore_to_maestro.py explore-log.json \
    --out .maestro/repro --report reports/bug-report.md --expect-screens "Home,Settings,Paywall"
```

The agent explores the app through mobile-mcp and logs each step (`launch`, `tap` by text/id/point, `type`, `swipe`, `back`, `assert`…), marking issues with an `event` (`crash`, `anr`, `error`, `ui`…). The tool writes one Maestro flow per issue, replaying from the last launch and ending in an assertion that fails while the bug exists. It also writes a bug report with P0–P3 severity, steps and evidence, and lists screens never reached. Log format: [`skills/app-test/SKILL.md`](skills/app-test/SKILL.md).

Example generated flow:

```yaml
appId: in.memeo.goodbudget
name: "Repro 1: Negative amount accepted and saved"
tags:
  - repro
  - error
---
- launchApp:
    clearState: true
- tapOn: "Sign in"
- tapOn:
    id: "email"
- inputText: "demo@goodbudget.app"
...
- inputText: "-12.50"
- assertVisible: "Enter an amount above 0"   # expected; fails while the bug exists
```

### `app-secure/scripts/mobsf_gate.py` — OWASP MASVS security gate

```bash
docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest
export MOBSF_API_KEY=...
python3 skills/app-secure/scripts/mobsf_gate.py --file app-release.aab --max-high 0 --min-score 60
python3 skills/app-secure/scripts/mobsf_gate.py --report mobsf-report.json        # offline
```

Uploads, scans and downloads the report through MobSF's REST API (`/api/v1/upload`, `/scan`, `/report_json`, `/scorecard`). It reads both the newer `appsec` scorecard and the older per-section format, sorts findings into MASVS-STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE and PRIVACY, and fails on too many highs or too low a score. Writes `reports/security.json` and a MASVS table in `reports/security.md`.

### `app-comply/scripts/privacy_scan.py` — Data safety + privacy labels from the code

```bash
python3 skills/app-comply/scripts/privacy_scan.py . --out reports --json reports/privacy.json
```

Looks up every dependency in [`sdk-catalog.json`](skills/app-comply/data/sdk-catalog.json): 36 common Expo / React Native SDKs across analytics, crash reporting, auth, push, ads and attribution, payments, AI providers and device APIs. It adds data reachable through permissions and every host the code calls. Writes three drafts:

- `data-inventory-draft.md`: rows to complete into your inventory
- `data-safety-draft.md`: Play Console answers per data type (collected, shared, purposes)
- `privacy-labels-draft.md`: App Store Connect answers (linked, tracking, purposes) plus the required-reason API list

It **blocks** when an SDK, data item or host is missing from `docs/data-inventory.md`, when tracking SDKs run without App Tracking Transparency, when an AI SDK runs without a consent screen (Apple 5.1.2(i)), or when there is no iOS privacy manifest. Links to your own privacy and help pages don't count as data destinations.

### `app-comply/scripts/store_policy_check.py` — Play + App Store policy pre-review

```bash
python3 skills/app-comply/scripts/store_policy_check.py . --artifact app-release.aab --json reports/store-policy.json
```

- **Target API** ≥ 36 (`--min-target-sdk` to change).
- **16 KB pages:** parses every 64-bit `.so` in the `.aab`/`.apk` and checks each ELF LOAD segment is 16 KB aligned. In APKs it also checks that uncompressed libraries are 16 KB aligned in the zip.
- **Play declarations** each sensitive permission needs.
- **Accounts:** in-app deletion, plus a deletion web URL for Play.
- **Sign in with Apple** whenever Google or Facebook login is offered (4.8).
- **Purchases:** Restore Purchases and Terms/EULA (3.1.1, 3.1.2); external payment SDKs are flagged for review.
- **Other Apple checks:** export compliance, thin WebView wrappers (4.2), UGC moderation (1.2).
- **Listing text** from `store/listing.json` or `fastlane/metadata`: length limits (title 30, short description 80, keywords 100 bytes…), ranking and price words, emoji, ALL CAPS, mentions of the other platform (2.3.10), privacy URLs.

### `app-comply/scripts/ota_check.py` — may this ship over the air?

```bash
python3 skills/app-comply/scripts/ota_check.py . --base v1.0.0     # tag of the last store build
```

Compares the last store build with `HEAD`. It requires a **store build** when any of these change: native files, native dependencies, permissions or usage strings, native app config (plugins, ios/android, runtimeVersion), payment code, or security-related code. It also does when more than one new screen appears, because Apple DPLA 3.3(b) and 2.5.2 allow OTA only if the app's purpose doesn't change. Otherwise it prints `OTA ALLOWED` and the staged rollout command.

### `app-release/scripts/testers.py` — Play's 12-tester / 14-day rule

```bash
python3 skills/app-release/scripts/testers.py testers.csv      # columns: email,opted_in,opted_out
```

Reports how many testers are active today and the current continuous streak. It also gives the earliest date you can apply for production, or how many more testers you need, and flags bad rows. It works only from real opt-ins; never fake testers.

### `app-release/scripts/release_report.py` — the release evidence pack

```bash
python3 skills/app-release/scripts/release_report.py --reports reports --version 1.2.0 [--manual docs/manual-checks.json]
```

Merges every JSON result into `reports/release-report.md`. The report has a gate table with evidence files, every blocker with its fix, and the manual store-console checklist (tick items with `--manual`). It also lists warnings that need a written reason. It fails if a required gate failed or never ran.

## Run every gate at once

```bash
bash skills/app-factory/scripts/run_gates.sh /path/to/app \
    [--base v1.0.0]                       # OTA check against the last store build
    [--artifact app-release.aab]          # 16 KB native-library check
    [--mobsf-file app-release.aab | --mobsf-report mobsf.json]
    [--explore-log explore.json]          # agent exploratory-test log
    [--testers testers.csv]               # Play closed-test tracker
    [--version 1.2.0]
```

It runs inventory lint → preflight → privacy scan → store policy → (OTA, MobSF, exploration, testers when given) → release report. Everything is written to `PROJECT/reports/`, and the script exits 1 if any gate fails.

## What a run looks like

On the deliberately broken fixture in [`tests/fixtures/bad-app`](tests/fixtures/bad-app), with the sample MobSF report and exploration log. The tests add a fake Stripe key at runtime, so no key-shaped string is stored in the repository.

```
| Gate | Check                                  | Result  | Summary                              |
|------|----------------------------------------|---------|--------------------------------------|
| 1    | Plan: data inventory complete          | FAIL    | docs/data-inventory.md missing       |
| 3    | Build: preflight scan                  | FAIL    | 10 blocker(s), 14 warning(s)         |
| 4    | Quality: exploratory test              | FAIL    | 2 issue(s), 1 crash/ANR, 6 screens   |
| 5    | Security: MobSF / MASVS                | FAIL    | 3 high finding(s) > 0                |
| 6    | Compliance: privacy forms vs code      | FAIL    | 4 blocker(s), 2 warning(s)           |
| 6    | Compliance: Play + App Store policy    | FAIL    | 13 blocker(s), 2 warning(s)          |
```

Blockers found include:
- a placeholder bundle id and a hard-coded Stripe live key
- cleartext HTTP, disabled ATS and a debuggable build
- target SDK 34 and an empty camera usage string
- no privacy policy link and no account deletion
- Google login without Sign in with Apple
- IAP without restore or terms, and UGC without moderation
- AdMob without App Tracking Transparency and OpenAI without a consent screen
- no privacy manifest
- a store title "BEST BUDGET APP #1 FREE 💰"
- an iOS name that mentions Google Play
- a crash when camera permission is denied

The store-ready fixture [`tests/fixtures/good-app`](tests/fixtures/good-app) passes every gate: `READY FOR SUBMISSION (after manual items)`.

## Use it in CI

`scaffold.py` adds `.github/workflows/app-gates.yml` to your app, which runs `run_gates.sh` on every pull request. To add it by hand:

```yaml
- uses: actions/checkout@v4
  with: { repository: MEMEO-PRO/mobile_app_end_to_end_skills, path: .app-factory }
- run: bash .app-factory/skills/app-factory/scripts/run_gates.sh . --skills .app-factory/skills
```

## Reference material

The long-form knowledge lives in [`skills/app-factory/references/`](skills/app-factory/references):

| File | Contents |
|---|---|
| [`runbook.md`](skills/app-factory/references/runbook.md) | 17 build steps from developer accounts to yearly upkeep, with commands, an `app.config.ts` example and a "done when" line each |
| [`overview.md`](skills/app-factory/references/overview.md) | How production apps are built: 12 stages, quality checks, MASVS security checks, store requirements, the Expo path, release thresholds, and what already exists on GitHub |
| [`compliance.md`](skills/app-factory/references/compliance.md) | Every document to publish, Google Play and App Store rules in detail, EU / US / India law, upcoming deadlines |
| [`legal-global.md`](skills/app-factory/references/legal-global.md) | 45+ jurisdictions across Europe, Asia, the Middle East, Africa, North America, Latin America and Oceania: registration, representative / DPO, breach deadline, children's consent age, transfers, penalties |

Templates in [`skills/app-factory/templates/`](skills/app-factory/templates): data inventory, privacy policy, notes for the store reviewer, release report.

## Testing this repository

```bash
cd tests && python3 -m unittest -v
```

55 tests, about 5 seconds, standard library only. They cover:

- **preflight.sh**: every planted problem in the broken app is caught; the good app is CLEAR; the target-SDK override works.
- **privacy_scan.py**: SDK detection; Data safety and label drafts; undeclared SDK and host detection; permission-derived items; legal links ignored.
- **store_policy_check.py**: policy blockers; listing rules; fastlane metadata; 16 KB checks on synthetic ELF libraries (misaligned, aligned, and an unaligned stored `.so` in an APK).
- **ota_check.py**: real git repositories where JS-only, native file, permission, payment, native dependency and new-screen changes each get the right route.
- **mobsf_gate.py**: offline reports in both formats; a mock MobSF server that checks the upload → scan → report flow and the API-key header; connection errors.
- **explore_to_maestro.py**: generated Maestro YAML, replay from the last launch, coverage, clean sessions.
- **testers.py**: rule met, not enough testers, an opt-out breaking the streak, bad rows.
- **release_report.py**: pass, failed or missing gates, manual ticks.
- **inventory_lint.py, scaffold.py, run_gates.sh** end to end, plus integrity checks: every skill's front matter, every referenced file exists, the SDK catalog is consistent, scripts are executable.

## Limits

- **Static checks are evidence, not a guarantee.** They read code, config and binaries. Store-console answers, listing screenshots, whether your backend and demo account are up, and legal registrations stay on the manual checklist that the release report prints.
- **The SDK catalog covers common SDKs in their default setup.** Check each SDK's own Data safety and privacy-label guidance for your configuration, and add missing SDKs to the JSON.
- **`ota_check.py` uses heuristics** (file paths, dependency names, keywords). For Expo, also compare `npx expo-updates fingerprint:generate` against the store build.
- **Exploratory testing needs a device driver** (mobile-mcp, adb, simctl). The tool turns the agent's log into flows and a report; it doesn't drive the device itself.
- **MobSF must run separately** (Docker is easiest). Dynamic testing with Frida and an external pentest are still advised for banking and payments apps.

## Repository layout

```
skills/
├── app-factory/                 orchestrator
│   ├── SKILL.md
│   ├── references/              runbook, overview, compliance, legal-global
│   ├── scripts/                 preflight.sh, run_gates.sh
│   └── templates/               data-inventory, privacy-policy, review-notes, release-report
├── app-spec/      SKILL.md · scripts/inventory_lint.py
├── app-build/     SKILL.md · scripts/scaffold.py
├── app-test/      SKILL.md · scripts/explore_to_maestro.py
├── app-secure/    SKILL.md · scripts/mobsf_gate.py
├── app-comply/    SKILL.md · scripts/privacy_scan.py, store_policy_check.py, ota_check.py · data/sdk-catalog.json
└── app-release/   SKILL.md · scripts/testers.py, release_report.py
tests/
├── fixtures/      bad-app, good-app, MobSF reports, exploration log
└── test_*.py      55 tests
```

## Contributing

Issues and pull requests are welcome, especially:

- new SDKs in `sdk-catalog.json`, with a link to the vendor's Data safety or privacy-label guidance
- rule changes, with an official source link
- new jurisdictions in `legal-global.md`
- new checks, each with a fixture-based test

Run `cd tests && python3 -m unittest` before opening a pull request.

## License

MIT, see [LICENSE](LICENSE).
