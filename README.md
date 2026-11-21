# Mobile App End-to-End Skills

Agent skills that take a mobile app from **idea to live on Google Play and the Apple App Store**, and keep it compliant afterwards. One skill, `app-factory`, runs eight phases with a pass/fail gate after each, so nothing reaches a store reviewer until it has passed the same checks production teams use.

- **Build:** 17 steps with exact commands, using Expo (React Native) so one TypeScript codebase produces both the Android `.aab` and the iOS `.ipa`. Native Kotlin/Swift is covered for apps that need heavy native work.
- **Quality and security:** release-build testing, device matrix, OWASP MASVS security checks, MobSF, traffic interception against your data inventory.
- **Store compliance:** Google Play and Apple App Store rules in detail: target API, privacy forms, permissions, account deletion, payments, AI disclosure, user-generated content, kids, metadata, review.
- **Law on every continent:** 45+ jurisdictions across Europe, Asia, the Middle East, Africa, North America, Latin America and Oceania: registration, local representative / DPO, breach deadlines, children's consent age, data transfers and penalties.
- **Automation:** `preflight.sh` scans a project and prints `BLOCKED` or `CLEAR` before you submit.
- **Templates:** data inventory, privacy policy, reviewer notes, release report.

> This is an engineering map, not legal advice. Store rules and laws change monthly; every reference links its source, and entries marked † or "unverified" were not confirmed against an official page. Check the source before relying on a date.

## The eight phases

| # | Phase | Gate (must pass before moving on) |
|---|---|---|
| 1 | Plan: accounts, idea, spec, data inventory, design | Accounts active · spec + data inventory · compliance screens designed |
| 2 | Legal scoping per launch country | Registrations filed · breach runbook · children's consent age wired in |
| 3 | Build: project, architecture, native config | Real-device dev builds · only justified permissions · account deletion · no preflight blockers |
| 4 | Verify quality | Release build crash-free on the device matrix · E2E green |
| 5 | Verify security | No high MobSF findings · no secrets · traffic matches inventory · signed OTA |
| 6 | Compliance pack | Both checks `CLEAR` · documents live · store forms match inventory · demo account works |
| 7 | Ship: production build, test tracks, listings, review | Approved on both stores · release report filled |
| 8 | Operate: staged rollout, OTA vs store fixes, yearly upgrades | Vitals under Play thresholds · reminders set |

## Repository layout

```
skills/app-factory/
├── SKILL.md                    # the orchestrator: phases, gates, top rejection causes
├── references/
│   ├── runbook.md              # 17 build steps, commands, app.config.ts example
│   ├── overview.md             # production lifecycle, quality + security checks, Expo path, existing tools
│   ├── compliance.md           # documents to publish, Play + Apple rules, EU/US/India law, deadlines
│   └── legal-global.md         # data-protection law map for 45+ jurisdictions
├── scripts/
│   └── preflight.sh            # pre-submission scan → BLOCKED / CLEAR
└── templates/
    ├── data-inventory.md
    ├── privacy-policy.md
    ├── review-notes.md
    └── release-report.md
```

## Install

The skill is plain Markdown plus a Bash script, so it works with any coding agent that reads skill folders (a `SKILL.md` with YAML front matter).

```bash
git clone https://github.com/MEMEO-PRO/mobile_app_end_to_end_skills.git
```

Then copy or symlink `skills/app-factory` into your agent's skills directory, for example:

```bash
mkdir -p ~/.agents/skills && ln -s "$PWD/mobile_app_end_to_end_skills/skills/app-factory" ~/.agents/skills/app-factory
```

Use your agent's own skills path if it differs. Or install with the open skills CLI:

```bash
npx skills add MEMEO-PRO/mobile_app_end_to_end_skills
```

Recommended companions, which the runbook calls at the right steps: [expo/skills](https://github.com/expo/skills), [android/skills](https://github.com/android/skills) and [mjmirza/app-store-compliance](https://github.com/mjmirza/app-store-compliance).

## Use

Ask your agent, for example:

- "Use app-factory to take my expense-tracker idea to both stores."
- "Run app-factory phase 6 on this project and tell me what blocks submission."
- "We're launching in Brazil, Turkey and Indonesia. What does app-factory say we must do first?"
- "Apple rejected us under 5.1.1(v). Fix it using app-factory."

Or run the scanner yourself:

```bash
bash skills/app-factory/scripts/preflight.sh /path/to/your/app
```

It checks placeholder bundle IDs, hard-coded secrets and `EXPO_PUBLIC_*` leaks, tokens in AsyncStorage, cleartext HTTP / disabled ATS / debuggable builds, the Android target SDK (36 for Play from 31 Aug 2026; override with `MIN_TARGET_SDK=35`), sensitive permissions, iOS usage strings, privacy manifest and export compliance, privacy-policy link, account deletion, Sign in with Apple, IAP restore and terms, external payments, AI consent, ad tracking without ATT, UGC moderation, and OTA code signing. Exit code `0` = CLEAR, `1` = BLOCKED, so it can gate CI.

Store-console items (Data safety form, privacy labels, content rating, declarations, agreements, listings, demo account) can't be seen from code and stay on the manual checklist in `SKILL.md`.

## Contributing

Issues and pull requests are welcome, especially for new jurisdictions, rule changes with an official source link, and new preflight checks with a test case.

## License

MIT, see [LICENSE](LICENSE).
