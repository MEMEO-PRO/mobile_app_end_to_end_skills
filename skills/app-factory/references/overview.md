# How Production Android & App Store Apps Are Built

*As of 21 Nov 2026.*

A production app is not "code that works". It is code that passes a chain of gates: architecture and design review, automated tests on every commit, static and security scans, a signed release build, store policy checks, a staged rollout, and live crash and ANR monitoring with hard thresholds. Google and Apple enforce several of these gates for you. For example, from 31 Aug 2026 Play rejects new apps and updates that don't target Android 16 (API 36), and Play reduces your visibility if your user-perceived crash rate goes above 1.09%.

This doc maps every gate, the checks inside it and the tools teams use, both for native Android and for Expo, which ships one codebase to both stores. It then lists what already exists on GitHub as agent skills and MCP servers, so your open-source project can automate the gaps instead of rebuilding what's there.

Step-by-step build from idea to both stores: [runbook.md](runbook.md) · Every store and legal requirement in detail: [compliance.md](compliance.md) · Every continent: [legal-global.md](legal-global.md)

## The lifecycle at a glance

```
PLAN ──gate──▶ BUILD ──gate──▶ VERIFY ──gate──▶ SHIP ──gate──▶ OPERATE
(idea, spec,     (setup, arch,    (tests, security, (build, tracks,   (rollout, vitals,
 design)          features)        compliance pack)  submit, review)   OTA, yearly upkeep)
   ▲                                                                      │
   └──────────────────── production data feeds the next plan ─────────────┘
```

Work moves left to right only when the gate passes; what happens in production loops back into the next plan.

## Stage by stage

| # | Stage | What a real team does | Output (artifact) | Typical tools |
|---|---|---|---|---|
| 1 | Ideation & validation | Problem interviews, competitor teardown, store keyword research, a landing page or waitlist | One-page problem brief, success metric | Store search, Google Trends, Figma |
| 2 | Product spec | User stories, flows, edge cases, non-goals, analytics events, privacy data map (what data, why, where it goes) | PRD + data inventory, which later feeds Play's Data safety form and Apple's privacy labels | Docs, Linear/Jira |
| 3 | UX/UI design | Wireframes → high-fidelity screens, design tokens, dark mode, accessibility (contrast, touch targets ≥ 48 dp, TalkBack labels) | Figma file + design system | Figma, Material 3 |
| 4 | Architecture | Modules (`:app`, `:core:*`, `:feature:*`), layers (UI → ViewModel → domain → data), offline strategy, DI, threat model | Architecture decision records, threat model | Kotlin, Jetpack Compose, Hilt/Koin, Room, Retrofit/Ktor, Gradle version catalogs |
| 5 | Build | Feature branches, PR reviews, conventional commits, feature flags | Merged code behind flags | Android Studio, Git, Firebase Remote Config |
| 6 | Continuous integration | Every PR: build, lint, unit tests, static analysis, dependency scan, screenshot tests | Green checks required to merge | GitHub Actions, Gradle, Detekt, Android Lint |
| 7 | QA & device testing | UI/E2E flows on emulators and real devices across API levels, screen sizes and low-RAM phones; exploratory testing | Test reports, bug tickets | Espresso, Compose UI test, Maestro, Firebase Test Lab |
| 8 | Security testing | Static analysis of the APK/AAB, dynamic testing, network interception, secrets scan, against OWASP MASVS | Security report with fixed/accepted findings | MobSF, jadx, Frida, Burp/mitmproxy |
| 9 | Performance | Startup time, jank, memory, battery, APK size; Baseline Profiles | Benchmarks vs. budget | Macrobenchmark, Perfetto, Android Studio profilers, R8 |
| 10 | Release engineering | Versioning, signed AAB with Play App Signing, R8/ProGuard, release notes, store assets | Signed `.aab`, store listing | Gradle, fastlane, Play Console |
| 11 | Store review | Policy declarations, Data safety, content rating, target API, testing track, then review | Approved release | Play Console, App Store Connect |
| 12 | Rollout & operate | Staged rollout (1% → 5% → 20% → 100%), halt on regressions, crash/ANR triage, reviews, analytics | Vitals dashboards, hotfixes | Play Console vitals, Crashlytics/Sentry |

## Quality checks

Teams run cheap checks on every commit and expensive ones before each release. Bugs are found mostly by automation; humans do exploratory testing at the end.

| Check | What it catches | When | Tool | Typical gate |
|---|---|---|---|---|
| Android Lint | API misuse, missing permissions, accessibility, deprecated calls, wrong API levels | Every PR | Built into AGP | 0 errors, warnings baselined |
| Kotlin static analysis | Code smells, complexity, potential bugs | Every PR | [Detekt](https://github.com/detekt/detekt) (7.1k★), ktlint | 0 new issues |
| Unit tests | ViewModel/domain logic, mappers, repositories | Every PR | JUnit, Turbine, MockK | Coverage on changed code (often 70–80%) |
| Screenshot tests | Unintended UI changes, dark mode, font scaling | Every PR | Roborazzi, Paparazzi | No unreviewed diffs |
| UI/instrumented tests | Screen behaviour, navigation | Nightly / pre-merge | Espresso, Compose UI test | Green on 3+ API levels |
| E2E flows | Login, payment, onboarding on a real build | Pre-release | [Maestro](https://github.com/mobile-dev-inc/Maestro) (16.5k★), Appium | Critical paths green |
| Device matrix | OEM bugs, small screens, low RAM, Android Go | Pre-release | Firebase Test Lab, Play pre-launch report | No crashes on top devices |
| Performance | Cold start, jank, memory leaks, battery | Pre-release | Macrobenchmark, Baseline Profiles, LeakCanary, Perfetto | Cold start under budget (e.g., < 1 s on mid-range) |
| Accessibility | Missing labels, contrast, touch target size | Pre-release | Accessibility Scanner, Lint, Compose semantics tests | No critical findings |
| Size & shrinking | Bloat, unused resources, broken reflection after R8 | Release build | R8, APK Analyzer | Size budget; release build tested, not debug |
| Dependency health | Known CVEs, outdated libraries, licence issues | Weekly | Dependabot/Renovate, OWASP Dependency-Check | No high-severity CVEs |
| Exploratory/bug bash | Real-world confusion and odd states | Pre-release | Humans, plus a closed testing track | Triage all P0/P1 |

## Security checks

The industry standard is [OWASP MAS](https://mas.owasp.org/): MASVS says *what* must be true, and MASTG says *how* to test it. MASTG v2.0.0 (July 2026) dropped the old checklist spreadsheet; tests, controls and profiles now live as structured data in the MAS repositories, which makes them easy for an agent to read.

| MASVS group | What is checked | How it's tested | Tools |
|---|---|---|---|
| STORAGE | No tokens, PII or keys in SharedPreferences, logs, backups, clipboard or screenshots | Inspect app data dirs, `adb backup`, logcat | MobSF, adb, jadx |
| CRYPTO | No hardcoded keys; Android Keystore; no ECB, MD5 or SHA-1 for security | Static scan for crypto APIs and key literals | MobSF, Semgrep, jadx |
| AUTH | Server-side session checks, biometric bound to Keystore, logout really invalidates | Dynamic tests against the backend | Burp/mitmproxy, Frida |
| NETWORK | TLS only, no `cleartextTrafficPermitted`, certificate pinning where needed, no trust-all TrustManager | Intercept traffic with a proxy; test pinning bypass | mitmproxy, Frida, Network Security Config review |
| PLATFORM | Exported activities/services/receivers protected, safe intents and deep links, WebView JS bridges, FLAG_SECURE on sensitive screens | Manifest review, intent fuzzing | drozer, MobSF, Lint |
| CODE | Up-to-date dependencies, input validation, no debug builds, minimum SDK sane | Dependency scan, static analysis | OWASP Dependency-Check, Semgrep, Detekt |
| RESILIENCE | Root/emulator/tamper detection and obfuscation, for high-risk apps only (banking, payments) | Try to repackage, hook and bypass | R8, Play Integrity API, Frida |
| PRIVACY | Minimal data collection, declared purposes match code, consent before tracking, data deletion | Compare SDK traffic with Data safety answers | MobSF, mitmproxy, Exodus Privacy |

The usual pipeline:

1. **Every PR:** secrets scan (gitleaks), Semgrep mobile rules, dependency CVEs.
2. **Every release build:** MobSF static scan of the signed AAB/APK ([MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF), 22.3k★), manifest and exported-component review.
3. **Before a major release:** dynamic testing on a rooted emulator with Frida (22.9k★) and mitmproxy; decompile with [jadx](https://github.com/skylot/jadx) (51.9k★) to see what an attacker sees.
4. **High-risk apps:** an external penetration test against MASVS L2 + R profiles.

## Store requirements

Most first-time rejections come from paperwork and policy, not code: a Data safety form that doesn't match what the SDKs actually send, a missing account-deletion path, or an unjustified sensitive permission.

**Google Play (as of Nov 2026)**

| Requirement | Detail | Source |
|---|---|---|
| Target API level | From 31 Aug 2026, new apps and updates must target Android 16 (API 36); extension possible to 1 Nov 2026. Existing apps below API 35 stop showing to new users on newer devices. | [Android Developers](https://developer.android.com/google/play/requirements/target-sdk) |
| Closed testing for new personal accounts | Accounts created after 13 Nov 2023 need ≥ 12 testers opted in for 14 continuous days, then answer production-readiness questions | [Play Console Help](https://support.google.com/googleplay/android-developer/answer/14151465) |
| Developer verification | Identity + app registration for apps on and off Play. Brazil, Indonesia, Singapore, Thailand from 30 Sep 2026; global in 2027. Free limited-distribution account for students/hobbyists (up to 20 devices) | [Android Developers Blog](https://developer.android.com/blog/posts/android-developer-verification-rolling-out-to-all-developers-on-play-console-and-android-developer-console) |
| App format & signing | Android App Bundle (.aab) with Play App Signing | Play Console |
| Data safety form | Every data type collected or shared, by you *and* your SDKs, with purpose, encryption and deletion answers | Play Console |
| Account deletion | If users can create an account, they must be able to delete it in-app and via a web link | Play policy |
| Sensitive permissions | SMS, call log, all-files access, background location, accessibility, exact alarms and foreground-service types each need a declaration and a core-use justification | Play policy |
| Native code | 64-bit and 16 KB memory-page support for apps with native libraries | Android Developers |
| Listing & content | Privacy policy URL, content rating questionnaire, target audience, ads declaration, accurate screenshots; extra declarations for finance (e.g., personal-loan apps in India), health and kids | Play policy |
| Pre-launch report | Play automatically crawls your build on real devices for crashes, accessibility and security warnings | Play Console |

**Apple App Store**

| Requirement | Detail |
|---|---|
| Build toolchain | From 28 Apr 2026, uploads must be built with Xcode 26 and the iOS 26 SDK ([QAwerk summary](https://qawerk.com/blog/app-store-rejection-reasons/)) |
| Privacy | Privacy nutrition labels; privacy manifests for your app and for third-party SDKs (with signatures); declared reasons for "required reason" APIs; App Tracking Transparency before tracking |
| AI disclosure | Consent before sending personal data to an external AI provider, naming the provider and data types (reported as enforced since Nov 2025) |
| Top rejection reasons | 2.1 crashes and incomplete builds (give the reviewer a demo account), 5.1.1 privacy policy and data use, missing account deletion, 3.1.1 using non-IAP payments for digital goods, 2.3 misleading metadata, 4.2 minimum functionality / copycat apps, 1.2 user-generated content without moderation |
| Testing | TestFlight internal (up to 100) and external testers; external builds get a lighter beta review |

Full text: [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).

## The Expo path: one codebase, both stores

Expo (React Native) builds one TypeScript codebase into a native Android `.aab` and an iOS `.ipa`. The current release is SDK 58 (15 Oct 2026, React Native 0.88, builds with Xcode 27) ([changelog](https://expo.dev/changelog/sdk-58)). Every gate above still applies, because the stores review the native binary, not your framework. What Expo changes is *how* you pass each gate.

| Stage | Native Android way | Expo way |
|---|---|---|
| Project setup | Android Studio template | `npx create-expo-app`, TypeScript, Expo Router (file-based routes) |
| Native config | Hand-edit AndroidManifest, Gradle, Info.plist | Continuous Native Generation: `app.config.ts` + config plugins; `npx expo prebuild` generates `android/` and `ios/`, so don't hand-edit those folders |
| Target API, minSdk, shrinking | Gradle | `expo-build-properties`; R8 is on by default in SDK 58 Android release builds |
| Running on devices | Android Studio run | Development builds with `expo-dev-client` (Expo Go only for quick prototypes) |
| Build & signing | Gradle + keystore; Xcode + certificates and profiles | EAS Build manages the Android keystore, iOS certificates and provisioning profiles; local builds are free |
| CI | GitHub Actions | EAS Workflows (YAML), or GitHub Actions calling `eas build` |
| Submit | Upload in Play Console / Xcode | `eas submit` to Play tracks and to TestFlight / App Store Connect |
| Hotfixes | New store release | EAS Update: over-the-air JS and asset updates with runtime versions, channels and staged rollouts |
| Monitoring | Play vitals + Crashlytics | EAS Observe and EAS Update insights + Sentry; Play vitals and App Store crash data still count |

**Expo-specific checks to add to the gates**

| Check | Why it matters | How |
|---|---|---|
| OTA vs native compatibility | An update that expects native code the installed binary doesn't have crashes on launch | Use the `fingerprint` runtime-version policy; test each update on the exact store build before rolling out |
| OTA store policy | Apple allows downloaded interpreted code only if it doesn't change the app's primary purpose, create a storefront or bypass OS security (DPLA 3.3(b), guideline 2.5.2). Google allows JS running in an interpreter but not downloaded dex/.so files. ([Bitrise summary](https://bitrise.io/blog/post/what-app-stores-allow-with-ota-updates-apple-and-google-policy-explained)) | OTA for fixes, copy and content; new features, payment flows and permission changes go through store review |
| OTA security | A hijacked update channel can push code to every user | Turn on EAS Update code signing so the app runs only bundles signed with your key |
| Readable JS bundle | Hermes bytecode can be decompiled, and `EXPO_PUBLIC_*` variables are embedded in the bundle | No secrets or private API keys in the app; keep them server-side |
| Token storage | AsyncStorage is plain text on disk | `expo-secure-store` (Android Keystore / iOS Keychain) |
| Hidden permissions | Libraries and config plugins can add permissions you never asked for | After `prebuild`, audit the generated AndroidManifest and Info.plist; remove extras with `android.blockedPermissions` |
| iOS privacy manifests | Apple rejects missing required-reason API declarations | Set `ios.privacyManifests` in app config; check each native library ships its own |
| Dependency compatibility | Mismatched native library versions break release builds | `npx expo install --check` and `npx expo-doctor` before every release |
| Release-mode testing | R8 and Hermes can break code that works in dev | Run Maestro E2E and the MobSF scan on the EAS-built release `.aab` / `.ipa`, not the dev build |
| SDK upgrades | Each SDK bump carries the new target API and Xcode requirements | Upgrade with every Expo SDK release, using the `expo-upgrade` skill |

**When to choose Expo:** most consumer and business apps (forms, lists, feeds, payments, maps, camera, notifications), where one team ships both stores. **When to stay native:** heavy native work such as custom camera pipelines, low-latency audio, games, deep OS integration or Wear/TV/Auto. Even then, Expo native modules (`expo-module` skill) let you write those parts in Kotlin/Swift inside an Expo app.

## Release and post-launch

Shipping is gradual and reversible. Teams release to a small slice of users, watch the numbers, and halt the rollout if anything regresses.

1. **Internal track** (team) → **closed track** (testers) → **open track** (optional public beta) → **production**.
2. **Staged rollout:** 1% → 5% → 20% → 50% → 100% over a few days. Halt and ship a hotfix if crash-free users or key events drop.
3. **Watch Google's thresholds:** above these, Play may lower your app's visibility and show users a warning on the listing ([Android vitals](https://developer.android.com/google/play/vitals)).

| Core vital | Bad-behaviour threshold (overall) | Per phone model |
|---|---|---|
| User-perceived crash rate | 1.09% | 8% |
| User-perceived ANR rate | 0.47% | 8% |
| Excessive battery usage | 1% | — |
| Excessive partial wake locks | 5% | — |

4. **Operate:** crash reporting (Crashlytics or Sentry), triage by affected users, reply to store reviews, track funnels in analytics, renew dependencies monthly, and redo the target-API upgrade every year before Google's August deadline.

## What already exists on GitHub

The build side is well covered, including by Google itself. Security testing, store compliance and release automation have only a few small, early projects. Star counts were read from GitHub on 21 Nov 2026.

**Build: Android and iOS coding skills**

| Repo | Stars | What it gives an agent |
|---|---|---|
| [android/skills](https://github.com/android/skills) (official, Google) | — | Skills folders for build-system, Compose, navigation, migration, performance, profilers, **play**, **security**, **testing**, devtools, Wear, TV, XR, cars. Installs with Android CLI (`android skills add --all`) or as a coding-agent plugin. Apache 2.0; public contributions not accepted. Focuses on areas "where evaluations show LLMs underperform". |
| [new-silvermoon/awesome-android-agent-skills](https://github.com/new-silvermoon/awesome-android-agent-skills) | 1,008 | Community collection: Kotlin, Compose, architecture |
| [dpearson2699/swift-ios-skills](https://github.com/dpearson2699/swift-ios-skills) | 1,309 | iOS 26 / Swift 6.3 / SwiftUI skills, including StoreKit, accessibility and an App Store review-prep skill |
| [Drjacky/claude-android-ninja](https://github.com/Drjacky/claude-android-ninja) | 142 | Modular architecture, Navigation3, Gradle conventions, testing |
| [anhvt52/jetpack-compose-skills](https://github.com/anhvt52/jetpack-compose-skills) | 101 | Compose code generation and review |
| [mmiani/kotlin-kmp-claude-agent-skills](https://github.com/mmiani/kotlin-kmp-claude-agent-skills) | 93 | Kotlin Multiplatform (shared Android + iOS) |
| [wataru-maeda/react-native-boilerplate](https://github.com/wataru-maeda/react-native-boilerplate) | 524 | Expo template with Maestro E2E and AGENTS.md skills |
| Others: [dpconde/claude-android-skill](https://github.com/dpconde/claude-android-skill), [rcosteira79/android-skills](https://github.com/rcosteira79/android-skills), [krutikJain/android-agent-skills](https://github.com/krutikJain/android-agent-skills) (includes CI and release) | small | Overlapping best-practice skills |

**Build: Expo and React Native (both stores from one codebase)**

| Repo / tool | Stars | What it gives an agent |
|---|---|---|
| [expo/skills](https://github.com/expo/skills) (official, Expo) | 4,199 | 23 skills: `expo-router`, `expo-module`, `expo-upgrade`, `expo-dev-client`, plus EAS skills `eas-app-stores` (build + submit, TestFlight, versioning), `eas-update`, `eas-update-insights` (rollout gates), `eas-workflows` (CI), `eas-simulator`. MIT. Install: `npx skills add expo/skills`, or your agent's plugin marketplace |
| [Expo MCP server](https://docs.expo.dev/eas/ai/mcp/) (official) | — | Live tools: EAS builds, submit, workflows, cloud simulators with tap/type/screenshot automation, TestFlight crashes and feedback, Play Store crashes and reviews, Sentry issues. Some tools need a paid Expo plan. Comes bundled with Expo's agent plugin |
| [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) | 1,715 | React Native skills from Callstack (performance, architecture) |
| [suleimanodetoro/skills](https://github.com/suleimanodetoro/skills) | 675 | React, React Native and software-security skills |
| [margelo/react-native-skills](https://github.com/margelo/react-native-skills) | 181 | React Native skills from Margelo (native modules, performance) |

**Test: letting agents drive real devices**

| Repo | Stars | Use |
|---|---|---|
| [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp) | 10,770 | MCP server for agents to drive iOS/Android simulators, emulators and real devices |
| [mobile-dev-inc/Maestro](https://github.com/mobile-dev-inc/Maestro) | 16,477 | YAML E2E flows; the easiest test format for an agent to write |
| [ghost-in-the-droid/android-agent](https://github.com/ghost-in-the-droid/android-agent) | 430 | 66 MCP tools over ADB/WebDriverAgent, human-in-the-loop steps |
| [yang1ming/android-harness](https://github.com/yang1ming/android-harness) | 179 | ADB-first harness: screenshots, UI inspection, input, diagnostics |
| [robbin/android-adb-control](https://github.com/robbin/android-adb-control) | 98 | Observe → act → verify skill over ADB |

**Secure: mobile security**

| Repo | Stars | Use |
|---|---|---|
| [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF) | 22,287 | Automated static + dynamic analysis mapped to MASVS; has a REST API an agent can call |
| [skylot/jadx](https://github.com/skylot/jadx) | 51,923 | Decompile APK/DEX to Java: see what attackers see |
| [frida/frida](https://github.com/frida/frida) | 22,870 | Runtime hooking for dynamic tests (pinning, root checks, crypto) |
| [detekt/detekt](https://github.com/detekt/detekt) | 7,117 | Kotlin static analysis |
| [dweinstein/mobile-security-skills](https://github.com/dweinstein/mobile-security-skills) | 56 | Agent skills for mobile security testing |
| [ivRodriguezCA/MobHunt](https://github.com/ivRodriguezCA/MobHunt) | 44 | Orchestrator + narrow sub-agents for mobile security research |
| [senaiverse/reactnative-expo-ai-agent-system-workflow](https://github.com/senaiverse/reactnative-expo-ai-agent-system-workflow) | 132 | 7 agents for React Native: accessibility, design system, security |

**Ship: store release and compliance**

| Repo | Stars | Use |
|---|---|---|
| [vimleshkpandey/app-store-deploy-skill](https://github.com/vimleshkpandey/app-store-deploy-skill) | 0 | iOS build → sign → upload → submit with fastlane |
| [PinoyFreeCoder/deployment-checklist](https://github.com/PinoyFreeCoder/deployment-checklist) | 50 | Pre-deployment checklist with human and AI-agent versions |
| Google's `play` folder in android/skills | — | Official Play-related guidance (contents not inspected here) |

## Gaps and what your project should cover

Don't write another "Compose best practices" skill; Google and the community already have that covered. The open space is the **gates**: an agent pipeline that takes an app from spec to a store-ready, security-tested release and produces evidence at each step.

| Gap | Why it's open | What your project adds |
|---|---|---|
| Spec → data inventory → Data safety / privacy labels | No tool links what the code and SDKs actually collect to the store forms | A skill that scans dependencies + network calls and drafts the Data safety form and Apple privacy labels, flagging mismatches |
| Agentic security testing | MobSF and Frida exist, but agent skills around them have < 100 stars | A `security-gate` skill: run MobSF via its API, map findings to MASVS groups, auto-propose fixes, re-scan |
| Store-policy pre-check | Rejections come from policy, and there's no open "pre-review" | A `play-policy-check` + `appstore-review-check`: target API, permissions declarations, account deletion, 16 KB pages, IAP rules, metadata |
| Agent-driven exploratory testing | mobile-mcp drives devices but nothing turns that into a bug report | An explorer agent that taps through every screen via mobile-mcp, records crashes and ANRs, and writes Maestro repro flows |
| Closed-testing logistics | The 12-tester / 14-day rule blocks solo developers | A checklist + tester-tracking bot; never fake testers |
| Release evidence pack | Teams need proof each gate passed | One generated `release-report.md` per build: test results, MobSF score, policy checks, vitals targets |

Suggested shape: one repo, `app-factory`, with one orchestrator and 6 skills (spec, build, test, secure, comply, release). Make **Expo the default target**, so one run produces both an Android `.aab` and an iOS `.ipa`, with a native Kotlin path only for apps that need heavy native work. Reuse what exists instead of rebuilding it: expo/skills and the Expo MCP server for build, submit and simulators; android/skills and swift-ios-skills for native code; mobile-mcp and Maestro for testing; MobSF for security. Your own skills cover what nobody has yet:

- an **OTA-update compliance check** (does this update change native code, payments or the app's primary purpose?), and
- a **two-store pre-review**: Play Data safety and Apple privacy labels and privacy manifests, generated from the same dependency and network scan.

Build it alongside a small real app, so every gate is proven on something that actually ships to both stores.

One caution: GitHub file access was limited in this session, so I saw only the top-level folders of android/skills, not each skill inside them. Check the `security`, `testing` and `play` folders before you write overlapping skills.

## Sources

- [Meet Google Play's target API level requirement — Android Developers](https://developer.android.com/google/play/requirements/target-sdk)
- [App testing requirements for new personal developer accounts — Play Console Help](https://support.google.com/googleplay/android-developer/answer/14151465)
- [Android developer verification rolling out — Android Developers Blog](https://developer.android.com/blog/posts/android-developer-verification-rolling-out-to-all-developers-on-play-console-and-android-developer-console)
- [Android vitals — Android Developers](https://developer.android.com/google/play/vitals)
- [Android skills overview — Android Developers](https://developer.android.com/tools/agents/android-skills) · [android/skills README](https://github.com/android/skills)
- [MASTG v2.0.0 removes MAS checklists — OWASP MAS](https://mas.owasp.org/news/2026/07/14/checklists-removal/)
- [App Review Guidelines — Apple](https://developer.apple.com/app-store/review/guidelines/)
- [App Store rejection reasons in 2026 — QAwerk](https://qawerk.com/blog/app-store-rejection-reasons/)
- GitHub repository pages linked in the tables above (star counts as of 21 Nov 2026)

- Expo: [SDK 58 changelog](https://expo.dev/changelog/sdk-58) · [expo/skills README](https://github.com/expo/skills) · [Expo MCP server docs](https://docs.expo.dev/eas/ai/mcp/)
- [What app stores allow with OTA updates — Bitrise](https://bitrise.io/blog/post/what-app-stores-allow-with-ota-updates-apple-and-google-policy-explained)
