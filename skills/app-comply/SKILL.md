---
name: app-comply
description: Two-store compliance pre-review for Google Play and the Apple App Store - drafts the Play Data safety form, Apple privacy labels and privacy-manifest API list from the app's real SDKs, permissions and network hosts and flags mismatches with the data inventory; checks store policy (target API, 16 KB native pages, permission declarations, account deletion, billing, Sign in with Apple, export compliance, UGC, listing metadata); and decides whether an update may ship over the air or needs store review. Use before submission, after adding an SDK or permission, before every OTA update, or after a rejection.
---

# app-comply — Compliance pack (app-factory phases 6 and 8)

Store rules in detail: `app-factory/references/compliance.md`. Law per country: `app-factory/references/legal-global.md`. This is an engineering check, not legal advice.

## 1. Privacy forms from the code — `scripts/privacy_scan.py`

```bash
python3 skills/app-comply/scripts/privacy_scan.py . --out reports --json reports/privacy.json
```

Reads `package.json`, app config, manifests and source; looks each SDK up in `data/sdk-catalog.json` (36 common Expo / React Native SDKs: analytics, crash reporting, auth, push, ads and attribution, payments, AI providers, device APIs); adds data reachable through permissions; lists every remote host the code calls. Writes:

- `reports/data-inventory-draft.md` — rows to complete into `docs/data-inventory.md`
- `reports/data-safety-draft.md` — Play Console → App content → Data safety, per data type
- `reports/privacy-labels-draft.md` — App Store Connect → App Privacy, plus required-reason API categories

Blocks when: there is no inventory; an SDK, data item or host is missing from it; tracking SDKs run without App Tracking Transparency; an AI SDK runs without a consent screen (Apple 5.1.2(i)); there is no iOS privacy manifest. Links to your own privacy/terms/help pages are not counted as data destinations. Extend the catalog for SDKs it doesn't know; it is plain JSON.

## 2. Store policy — `scripts/store_policy_check.py`

```bash
python3 skills/app-comply/scripts/store_policy_check.py . --artifact build/app-release.aab --json reports/store-policy.json
```

| Check | Store | Severity |
|---|---|---|
| `targetSdkVersion` ≥ 36 (`--min-target-sdk` to change) | Play | blocker |
| 64-bit `.so` files have 16 KB-aligned LOAD segments; uncompressed `.so` 16 KB-aligned in APKs (`--artifact`) | Play | blocker |
| Sensitive permissions → list of Console declarations (SMS/call log, all files, background location, accessibility, exact alarm, full-screen intent, media, foreground service, contacts, local network) | Play | manual |
| Accounts without in-app deletion; Play deletion web URL | Both | blocker / manual |
| Google/Facebook login without Sign in with Apple (4.8) | Apple | blocker |
| IAP without Restore Purchases; purchases without Terms/EULA (3.1.1, 3.1.2) | Both | blocker |
| External payment SDK for digital goods | Both | manual |
| Export compliance not declared | Apple | warning |
| Thin WebView wrapper (4.2) | Apple | warning |
| UGC without report/block (1.2) | Both | blocker |
| Listing: length limits, ranking/price words, emoji, ALL CAPS, other platform named (2.3.10), missing privacy URL | Both | blocker / warning |

Listing text comes from `store/listing.json` (`android`: title, short_description, full_description, privacy_url, account_deletion_url; `ios`: name, subtitle, description, keywords, promotional_text, privacy_url) or `fastlane/metadata`.

## 3. OTA or store build — `scripts/ota_check.py`

```bash
python3 skills/app-comply/scripts/ota_check.py . --base v1.0.0 --json reports/ota.json
```

Compares the last store build's tag with `HEAD`. Requires a store build when native files, native dependencies, permissions, native app config, payment code or security-related code change, or when more than one new screen appears (a change of purpose under Apple DPLA 3.3(b) / 2.5.2). Otherwise prints OTA ALLOWED and the staged command `eas update --channel production --rollout-percentage 10`. Exit 0 OTA allowed, 1 store build required.

## 4. What only a human can do

Enter the drafts into Play Console and App Store Connect; content rating and target audience; ads declaration; category declarations (finance, health, government, VPN); EU trader status; publish the privacy policy (`app-factory/templates/privacy-policy.md`), terms, deletion page and support page; prepare the reviewer kit (`app-factory/templates/review-notes.md`); run [mjmirza/app-store-compliance](https://github.com/mjmirza/app-store-compliance)'s guard as a second opinion.

## Gate

`privacy_scan.py` and `store_policy_check.py` exit 0 · drafts entered in both consoles · documents live · demo account tested · before every OTA update, `ota_check.py` exits 0.
