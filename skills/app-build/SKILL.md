---
name: app-build
description: Set up and build a store-ready mobile app with Expo (default, one codebase for Android and iOS) or native Kotlin/Swift, with hardened config from day one - target API 36, privacy manifest, export compliance, blocked permissions, fingerprint runtime and signed OTA updates, secure token storage, threat model. Use when creating a new app project, adding native config or permissions, or preparing EAS builds.
---

# app-build — Build (app-factory phase 3)

Default target: **Expo SDK 58 + EAS**, so one TypeScript codebase produces the Android `.aab` and the iOS `.ipa`. Choose native Kotlin/Swift only for custom camera pipelines, low-latency audio, games, deep OS integration or Wear/TV/Auto; even then, Expo native modules (`expo-module` skill) can hold the native parts. Full commands: `app-factory/references/runbook.md` steps 4–7.

## 1. Create the project and add the hardened config

```bash
npx create-expo-app@latest my-app && cd my-app
npx expo install expo-dev-client expo-secure-store expo-build-properties expo-updates expo-router
python3 path/to/skills/app-build/scripts/scaffold.py --name "My App" --package com.acme.myapp \
    --website https://myapp.acme.com --owner acme
```

`scripts/scaffold.py` writes (and refuses to overwrite without `--force`):

| File | What it sets |
|---|---|
| `app.config.ts` | `targetSdkVersion 36`, `runtimeVersion: fingerprint`, signed updates, `usesNonExemptEncryption`, a starter `privacyManifests`, `blockedPermissions` for media/audio/overlay/storage |
| `eas.json` | development / preview / production profiles, remote version source with auto-increment, submit to the Play internal track |
| `.maestro/smoke.yaml` | First E2E flow to extend per journey |
| `src/config/legal.ts` | Privacy, terms, deletion and support URLs, referenced by the app |
| `docs/data-inventory.md`, `docs/threat-model.md`, `docs/legal.md` | Templates to fill |
| `store/listing.json` | Listing text checked by `app-comply` |
| `.github/workflows/app-gates.yml` | Runs every gate on pull requests |

It rejects placeholder ids (`com.example.*`) and non reverse-DNS ids; the package name is permanent once published.

Then generate the OTA signing key (command is in the comment in `app.config.ts`), keep the private key out of git, and build: `eas build --profile development --platform all`.

## 2. Architecture rules

- Routes only in `app/` (Expo Router); screens and logic in `src/`; React Query over a typed API client.
- Auth with OAuth/OIDC + PKCE; never a client secret in the app; tokens in `expo-secure-store`, never AsyncStorage.
- No secrets in the bundle or in `EXPO_PUBLIC_*`: proxy paid APIs (including AI providers) through your server.
- Feature flags for anything unfinished; offline cache for read paths; validated deep links.
- Write `docs/threat-model.md`: assets, entry points (API, deep links, storage, OTA channel), mitigations.

## 3. Permissions

Add a permission only with the feature that needs it, and give iOS a specific usage string (`"Scan receipts to add expenses"`, not `"$(PRODUCT_NAME) needs camera"`). Prefer the Photo Picker and Contact Picker. After `npx expo prebuild --clean`, read the generated `AndroidManifest.xml` and `Info.plist`: libraries add permissions; remove extras with `android.blockedPermissions`.

## 4. Native path (no Expo)

Same gates, different files: `targetSdk 36` and `compileSdk 36` in `build.gradle`, NDK r28+ / AGP 8.5.1+ for 16 KB pages, R8 on, Play App Signing; on iOS a `PrivacyInfo.xcprivacy`, `ITSAppUsesNonExemptEncryption` in `Info.plist`, current Xcode. Use `android/skills` and `swift-ios-skills` for code patterns.

## Gate

Development build runs on a real Android phone and iPhone · `bash skills/app-factory/scripts/preflight.sh .` has no blockers · threat model reviewed · tests green in CI.
