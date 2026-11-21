---
name: app-factory
description: End-to-end pipeline for taking a mobile app from idea to live on Google Play and the Apple App Store, with a pass/fail gate after every phase. Covers spec, design, Expo (React Native) or native build, testing, OWASP MASVS security, store policy (Play and App Store), privacy forms, and data-protection law in 45+ jurisdictions on every continent. Use when building, auditing, submitting or maintaining a mobile app, when an app was rejected by a store, or when launching in a new country.
---

# app-factory

Take one app from idea to both stores, and keep it there. Work through the eight phases in order. Each phase ends with a **gate**: a short list of checks that must all pass before the next phase starts. Record the result of every gate in `docs/release-report.md` (template in `templates/release-report.md`).

Default stack: **Expo (SDK 58) + EAS**, so one TypeScript codebase produces an Android `.aab` and an iOS `.ipa`. Use native Kotlin / Swift only for heavy native work (custom camera pipelines, low-latency audio, games, Wear/TV/Auto). Every gate applies either way, because the stores review the native binary, not the framework.

This skill is an engineering map, not legal advice. Dates and rules change monthly: re-check the linked source before relying on one. Entries marked † or "unverified" in the references were not confirmed against an official page.

## Orchestration

This skill is the orchestrator. Each phase hands its detailed work to a phase skill in the same repository:

| Phase | Skill | Automated tool |
|---|---|---|
| 1 Plan · 2 Legal scoping | `app-spec` | `app-spec/scripts/inventory_lint.py` |
| 3 Build | `app-build` | `app-build/scripts/scaffold.py`, `scripts/preflight.sh` |
| 4 Verify quality | `app-test` | `app-test/scripts/explore_to_maestro.py` |
| 5 Verify security | `app-secure` | `app-secure/scripts/mobsf_gate.py` |
| 6 Compliance pack · 8 OTA route | `app-comply` | `app-comply/scripts/privacy_scan.py`, `app-comply/scripts/store_policy_check.py`, `app-comply/scripts/ota_check.py` |
| 7 Ship · 8 Operate | `app-release` | `app-release/scripts/testers.py`, `app-release/scripts/release_report.py` |

Run every automated gate at once and get the evidence pack:

```bash
bash skills/app-factory/scripts/run_gates.sh /path/to/app [--base v1.0.0] [--artifact app.aab] \
     [--mobsf-file app.aab | --mobsf-report mobsf.json] [--explore-log explore.json] [--testers testers.csv] [--version 1.1.0]
```

It writes `reports/*.json`, the privacy-form drafts, and `reports/release-report.md`, and exits 1 if any gate fails. Every tool also runs alone (see each skill). All tools need only `bash` and `python3` (standard library).

## Files

| File | Use it for |
|---|---|
| `scripts/run_gates.sh` | Runs every automated gate and writes the release report |
| `references/runbook.md` | The 17 build steps with exact commands, example config and a "done when" line each |
| `references/overview.md` | How production teams build apps: stages, quality checks, security checks (MASVS), store requirements, the Expo path, release thresholds, existing open-source skills |
| `references/compliance.md` | Every document and page to publish, Google Play and Apple rules in detail, EU / US / India law, upcoming deadlines |
| `references/legal-global.md` | Data-protection law for 45+ jurisdictions: registration, representative / DPO, breach deadline, children's consent age, transfers, penalties |
| `scripts/preflight.sh` | Automated pre-submission scan of a project. Prints `BLOCKED` or `CLEAR` |
| `templates/data-inventory.md` | The data map every privacy form is built from |
| `templates/privacy-policy.md` | Privacy policy skeleton that satisfies both stores, GDPR and DPDP |
| `templates/review-notes.md` | Notes and demo account for the store reviewer |
| `templates/release-report.md` | Evidence that each gate passed, per release |

Read only the reference a phase needs; they are long.

## Phase 1 — Plan (runbook steps 0–3)

Open both developer accounts on day one (Apple enrolment takes 2–6 weeks; a new personal Play account needs a 14-day closed test with 12+ testers). Validate the idea, write the spec, fill in `templates/data-inventory.md`, and decide which rule areas are switched on: kids / target age, user-generated content, payments or subscriptions, AI features, health, finance, location, and the list of countries. Design the compliance screens with the rest (consent, permission explainers, account deletion, paywall terms, AI notice, report / block).

**Gate 1:** both accounts Active and agreements accepted · one-page brief · spec + data inventory complete · switched-on rule areas and launch countries listed · every screen designed, compliance screens included.

## Phase 2 — Legal scoping (compliance.md, legal-global.md)

For every launch country, follow the routine at the top of `references/legal-global.md`: law and status, pre-launch registration or local representative, DPO, children's consent age, data-transfer mechanism and localisation, breach deadline. Set the incident clock to the shortest breach deadline among your markets. Keep countries that need a local entity or licence first (for example China, Egypt) switched off until that is done.

**Gate 2:** a per-country table in `docs/legal.md` with every column filled or marked "not required" · registrations filed · breach runbook names a deadline and an owner · children's consent age wired into sign-up where kids can be users.

## Phase 3 — Build (runbook steps 4–7)

Create the project, install the agent skills, set up the architecture (routes in `app/`, logic in `src/`, OAuth/OIDC + PKCE, tokens in `expo-secure-store`, feature flags), write a threat model, and build features with unit tests and one Maestro flow per critical journey. Put all native configuration in `app.config.ts`: `runtimeVersion.policy = "fingerprint"`, target API 36, iOS privacy manifest, `usesNonExemptEncryption`, a real usage string per iOS permission, `android.blockedPermissions` for anything libraries add that you don't use. After `npx expo prebuild --clean`, read the generated `AndroidManifest.xml` and `Info.plist`.

**Gate 3:** dev build runs on a real Android phone and iPhone · ADR + threat model reviewed · tests green in CI · every permission maps to a visible feature · in-app account deletion exists if accounts exist · `bash scripts/preflight.sh .` has no blockers.

## Phase 4 — Verify quality (runbook step 8)

Test release builds (`eas build --profile preview`), not dev builds. Run `npx expo install --check`, `npx expo-doctor` and the Maestro suite on: oldest and newest supported OS, a low-RAM Android phone, a tablet, dark mode, largest font, airplane mode, slow network. Upload to a Play test track to get the pre-launch report.

**Gate 4:** 0 crashes on the device matrix · all Maestro flows green · cold start within budget · pre-launch report crashes and accessibility warnings fixed.

## Phase 5 — Verify security (runbook step 9, overview.md "Security checks")

Run a MobSF static scan of the release `.aab` and `.ipa`. Check MASVS STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE and PRIVACY (add RESILIENCE for banking and payments). No secrets in the JS bundle or `EXPO_PUBLIC_*` variables. Turn on EAS Update code signing. Intercept your own traffic with mitmproxy and compare every destination with the data inventory.

**Gate 5:** no open high MobSF findings · gitleaks / secret scan clean · traffic matches the data inventory exactly (every SDK listed) · OTA updates signed.

## Phase 6 — Compliance pack (runbook step 10, compliance.md)

Publish the documents in the "Documents and pages" table of `references/compliance.md` that apply: privacy policy (from `templates/privacy-policy.md`), terms, account deletion web page, support page, and category pages (child-safety standards, UGC policy, accessibility statement, AI notice). Fill in the Play Data safety form and Apple privacy labels **from the data inventory**, the permission and foreground-service declarations, content rating, target audience, ads, export compliance, EU trader status. Prepare the reviewer kit from `templates/review-notes.md`: a demo account on the live backend plus notes for every non-obvious feature and purchase.

Run both automated checks:

```bash
bash skills/app-factory/scripts/preflight.sh /path/to/app
bash ~/repositories/app-store-compliance/agent-os/hooks/app-store-compliance-guard.sh /path/to/app
```

**Gate 6:** both checks print `CLEAR` · every applicable document is live at a public URL and linked in the app · store forms match the data inventory · demo account works · every manual store-console item ticked.

## Phase 7 — Ship (runbook steps 11–14)

`eas build --profile production --platform all` from a tagged commit, re-run MobSF and both checks on those exact binaries, `eas submit` to the Play closed track and TestFlight, complete the 14-day closed test if required, write the store listings (accurate screenshots of the app in use, no prices, "#1" claims or the other platform), and submit. If rejected: fix the root cause of the cited guideline, reply in the Resolution Center / Play inbox, resubmit.

**Gate 7:** approved on both stores · release report filled in for this build.

## Phase 8 — Operate (runbook steps 15–17)

Staged rollout (Play 1% → 5% → 20% → 50% → 100%; Apple 7-day phased release). Halt if the user-perceived crash rate nears 1.09% or ANR rate 0.47%. Ship JS-only fixes as signed OTA updates to a small channel first; anything that changes native code, permissions, payments or the app's purpose goes through a new store build and review. Every year: upgrade Expo for Google's 31 Aug target-API deadline and Apple's spring SDK floor; re-check the deadline table in `references/compliance.md` monthly; re-run the checks and update the privacy forms whenever an SDK or data type is added.

**Gate 8 (recurring):** vitals under threshold · each change routed correctly (OTA vs store) · calendar reminders exist for the yearly upgrades and the monthly deadline check.

## Rules that cause most rejections

1. No working demo account, or a backend that is down during review (Apple 2.1).
2. Privacy forms that don't match what the app and its SDKs actually send (Play Data safety; Apple 5.1.1 and privacy manifests).
3. Accounts without in-app deletion (Apple 5.1.1(v); Play also needs a web link).
4. Sensitive permissions without a core-use justification and declaration (Play).
5. Digital goods sold outside the store's billing (Apple 3.1.1; Play Payments policy), subject to the regional exceptions in compliance.md.
6. Misleading metadata or screenshots (Apple 2.3), thin or copycat apps (Apple 4.2 / 4.3).
7. User-generated content without filter, report and block (Apple 1.2; Play UGC policy).
8. Personal data sent to an AI provider without naming it and asking first (Apple 5.1.2(i)).
9. Target API below the current floor (Play: API 36 from 31 Aug 2026) or an old Xcode / iOS SDK (Apple).
