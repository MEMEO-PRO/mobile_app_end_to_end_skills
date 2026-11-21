# Release report — <App name> <version>

Commit: <sha> · Tag: <vX.Y.Z> · Android versionCode: <n> · iOS build: <n> · Date: <YYYY-MM-DD> · Prepared by: <name>

One report per release. Every gate needs evidence (a link or file), not just a tick.

| Gate | Check | Result | Evidence |
|---|---|---|---|
| 1 Plan | Accounts active, agreements accepted | ☐ Pass ☐ Fail | |
| 1 Plan | Spec + data inventory up to date | ☐ Pass ☐ Fail | docs/data-inventory.md |
| 2 Legal | Per-country table complete, registrations filed | ☐ Pass ☐ Fail | docs/legal.md |
| 3 Build | Only justified permissions in generated manifests; target API ≥ 36 | ☐ Pass ☐ Fail | |
| 3 Build | `preflight.sh` — no blockers | ☐ Pass ☐ Fail | output file |
| 4 Quality | Unit + Maestro suites green on release build | ☐ Pass ☐ Fail | CI run |
| 4 Quality | Device matrix: 0 crashes; cold start <n> ms vs budget <n> ms | ☐ Pass ☐ Fail | |
| 4 Quality | Play pre-launch report: crashes and accessibility warnings fixed | ☐ Pass ☐ Fail | |
| 5 Security | MobSF: 0 open high findings (score <n>) | ☐ Pass ☐ Fail | report |
| 5 Security | Secret scan clean; no secrets in `EXPO_PUBLIC_*` | ☐ Pass ☐ Fail | |
| 5 Security | Intercepted traffic matches data inventory | ☐ Pass ☐ Fail | |
| 5 Security | OTA code signing on | ☐ Pass ☐ Fail | |
| 6 Compliance | app-store-compliance guard: CLEAR | ☐ Pass ☐ Fail | output file |
| 6 Compliance | Data safety form and privacy labels match inventory | ☐ Pass ☐ Fail | screenshots |
| 6 Compliance | Privacy policy, terms, deletion page, support page live | ☐ Pass ☐ Fail | URLs |
| 6 Compliance | Demo account tested today | ☐ Pass ☐ Fail | |
| 7 Ship | Approved on Google Play | ☐ Pass ☐ Fail | date |
| 7 Ship | Approved on App Store | ☐ Pass ☐ Fail | date |
| 8 Operate | Crash rate <n>% (limit 1.09%), ANR <n>% (limit 0.47%) at 100% rollout | ☐ Pass ☐ Fail | vitals |

## Changes in this release

- <Feature / fix> — route: ☐ store build ☐ OTA (JS-only, same purpose, no payment change)

## New SDKs, permissions or data types

- <None> or <item → inventory row, forms updated on YYYY-MM-DD>

## Known issues and accepted risks

- <Issue — why accepted — owner — fix by>
