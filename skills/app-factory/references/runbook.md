# Build runbook: idea to both stores

Seventeen steps take one app from idea to live on Google Play and the App Store, using Expo so one TypeScript codebase produces both builds. Each step ends with a **Done when** line; don't start the next step until it's true. Store and legal rules are referenced here and explained in full in [compliance.md](compliance.md) and [legal-global.md](legal-global.md).

Assumptions: Expo SDK 58 with EAS (Expo Application Services), TypeScript, Expo Router, a small backend (for example Supabase), and these agent skills installed: `expo/skills`, `android/skills`, `mjmirza/app-store-compliance`. Swap pieces freely; the steps stay the same.

Budget the calendar, not just the code: Apple enrolment can take 2–6 weeks and a new personal Play account needs a 14-day closed test, so start Step 0 on day one.

## Step 0: accounts and prerequisites

| Item | Google Play | Apple App Store |
|---|---|---|
| Developer account | Play Console: one-time fee (about US$25); choose **personal** or **organization** | Apple Developer Program: annual fee (about US$99); individual or organization |
| Organization requirements | Organization + D-U-N-S number is **mandatory** for finance (banking, loans, trading, crypto), health, VPN and government apps | Organization enrolment needs a D-U-N-S number and a legal entity |
| Identity checks | Android developer verification of identity and every package name (required in Brazil, Indonesia, Singapore, Thailand from 30 Sep 2026; global in 2027) | Enrolment and ID verification currently take 2–6 weeks, so enrol at least 6 weeks before your first submission |
| Testing gate | New personal accounts (created after 13 Nov 2023): closed test with ≥ 12 testers opted in for 14 continuous days before production | None; TestFlight is optional but strongly advised |
| To sell anything | Payments profile + tax info | Paid Apps agreement accepted by the Account Holder, banking and tax forms |
| EU distribution | Trader details in Play Console | DSA trader status declared and verified, or the app is removed from the EU storefront |
| Tooling | Expo account; EAS CLI (`npm i -g eas-cli`, `eas login`); Node LTS; Android Studio (emulators); a real Android phone | A Mac with Xcode (local iOS builds and simulator), or EAS cloud builds; a real iPhone |

**Done when:** both accounts show Active, agreements are accepted, and you have 12+ named testers lined up.

## Steps 1–3: idea, spec, design

1. **Validate the idea.** Write the problem in one sentence and name the user. Check the top 10 competing apps in both stores (ratings, 1–2-star reviews, price). Avoid saturated categories with nothing new: Apple rejects clones and indistinguishable apps under guideline 4.3, and thin website wrappers under 4.2.
   - **Done when:** a one-page brief with the problem, user, differentiator and one success metric.
2. **Write the spec and the data inventory.** User stories, every screen, edge cases (offline, empty, error, slow network), analytics events and non-goals. Then the **data inventory** ([template](../templates/data-inventory.md)), the document most compliance work hangs on: for every data item, record what it is, why you collect it, where it goes (your server, which SDK), whether it's shared, how long you keep it and how users delete it.
   - Pick the content rating, target age group and whether you have user-generated content, payments, AI features, health or finance features now. Each one switches on extra rules (compliance.md).
   - **Done when:** PRD + data inventory table + list of "switched-on" rule areas.
3. **Design.** Wireframes, then high-fidelity screens for both platforms: dark mode, large text, screen readers (TalkBack / VoiceOver labels), touch targets ≥ 48 dp / 44 pt, contrast at WCAG 2.1 AA. Design the compliance screens too, not as an afterthought: consent and permission explainers, privacy policy link, account deletion, subscription terms, AI-use notice, report/block for UGC.
   - **Done when:** every screen in Figma, including the compliance screens, reviewed against the spec.

## Steps 4–7: setup, architecture, native config

4. **Create the project and install the agent skills.**

```bash
npx create-expo-app@latest my-app && cd my-app
npx expo install expo-dev-client expo-secure-store expo-build-properties expo-updates
eas init && eas build:configure          # creates eas.json with development / preview / production profiles
npx skills add expo/skills               # Expo skills (or install them from your agent's plugin marketplace)
git clone https://github.com/mjmirza/app-store-compliance ~/repositories/app-store-compliance
bash ~/repositories/app-store-compliance/scripts/install.sh --tool all   # compliance skill + pre-submission guard
```

   - **Done when:** a development build runs on a real Android phone and a real iPhone (`eas build --profile development`).

5. **Architecture.** Routes only in `app/` (Expo Router), screens and logic in `src/`; a data layer (React Query) over a typed API client; auth with OAuth/OIDC + PKCE, never a client secret in the app; tokens in `expo-secure-store`; offline cache for read paths; feature flags for anything unfinished. Write a one-page **threat model**: what an attacker wants, the entry points (API, deep links, local storage, OTA channel) and the mitigation for each.
   - **Done when:** architecture decision record + threat model reviewed.
6. **Build the features with tests alongside.** Unit tests (Jest + React Native Testing Library) for logic and components as you go; one Maestro flow per critical journey (sign-up, core action, purchase, delete account).
   - **Done when:** all spec stories implemented behind flags, tests green in CI.
7. **Native configuration and permissions** in `app.config.ts`. The stores review the generated native app, so this file is where most compliance lives:

```ts
export default {
  name: "My App", slug: "my-app", version: "1.0.0",
  runtimeVersion: { policy: "fingerprint" },           // OTA updates only reach compatible binaries
  ios: {
    bundleIdentifier: "com.example.myapp",
    config: { usesNonExemptEncryption: false },        // only if you use nothing beyond standard HTTPS/OS crypto
    infoPlist: { NSCameraUsageDescription: "Scan receipts to add expenses" }, // a real reason per permission
    privacyManifests: { NSPrivacyAccessedAPITypes: [ /* required-reason APIs + reasons */ ] },
  },
  android: {
    package: "com.example.myapp",
    permissions: ["CAMERA"],
    blockedPermissions: ["android.permission.READ_MEDIA_IMAGES", "android.permission.RECORD_AUDIO"], // strip what libraries add
  },
  plugins: [["expo-build-properties", { android: { targetSdkVersion: 36, compileSdkVersion: 36 } }]],
};
```

   - Run `npx expo prebuild --clean` and read the generated `AndroidManifest.xml` and `Info.plist`: every permission must map to a visible feature, every iOS usage string must name the real feature.
   - Use the Android Photo Picker instead of broad media permissions, and avoid SMS, call log, all-files access, background location and accessibility services unless they are the app's core function (each needs a Play declaration).
   - **Done when:** the generated manifests contain only justified permissions, target API 36, and an iOS privacy manifest that covers your code and every native library.

## Steps 8–10: testing, security, compliance pack

8. **Test the release build, not the dev build.** R8 shrinking and the Hermes engine can break code that works in development.

```bash
eas build --profile preview --platform all     # installable release-mode builds
npx expo install --check && npx expo-doctor    # dependency and config health
maestro test .maestro/                          # E2E flows on emulator / simulator / device
```

   - Run on the oldest and newest supported OS, a small low-RAM Android phone, a tablet, dark mode, largest font size, airplane mode and a slow network.
   - Run the Play pre-launch report (automatic once you upload to a test track) and fix every crash and accessibility warning.
   - **Done when:** 0 crashes on the device matrix, all Maestro flows green, cold start within your budget.
9. **Security pass** against OWASP MASVS ([overview.md](overview.md), Security checks):
   - MobSF static scan of the `.aab` and `.ipa`; fix high findings.
   - No secrets in the JS bundle or `EXPO_PUBLIC_*` variables; tokens only in `expo-secure-store`; HTTPS only; validated deep links; EAS Update code signing on.
   - Intercept your own traffic with mitmproxy and compare it with the data inventory: every destination you didn't list is an undeclared SDK.
   - **Done when:** MobSF report with no open highs, traffic matches the data inventory.
10. **Assemble the compliance pack** (compliance.md has every item):
    - Publish: privacy policy ([template](../templates/privacy-policy.md)), terms, account and data deletion web page, support page, and any category pages (child-safety standards for social apps, accessibility statement for the EU).
    - Fill in: Play Data safety form, permission and foreground-service declarations, content rating, target audience, ads, financial / health declarations; Apple privacy nutrition labels, age rating questionnaire, export compliance, and the social-media capability answer.
    - Prepare a **reviewer kit** ([template](../templates/review-notes.md)): a working demo account on the live backend, review notes explaining every non-obvious feature and purchase, and demo videos for any sensitive permission.
    - Run both guards: `bash scripts/preflight.sh .` (this skill) and `bash ~/repositories/app-store-compliance/agent-os/hooks/app-store-compliance-guard.sh .`
    - **Done when:** both guards print `CLEAR` and every manual (store-console) item is ticked.

## Steps 11–14: build, test tracks, submit, review

11. **Production builds.** EAS manages the Android upload keystore and iOS certificates and provisioning profiles; enrol in Play App Signing.

```bash
eas build --profile production --platform all   # signed .aab + .ipa, versionCode / buildNumber auto-incremented
```

   - **Done when:** both artifacts built from a tagged commit, and the MobSF scan and guards re-run on these exact binaries.

12. **Internal and closed testing.**

```bash
eas submit --platform android --profile production   # to the Play internal or closed track set in eas.json
eas submit --platform ios --profile production       # to App Store Connect / TestFlight
```

   - Play: internal track for the team, then the closed track with ≥ 12 testers for 14 continuous days (new personal accounts). Collect real feedback; you'll be asked about it when applying for production.
   - Apple: TestFlight internal testers, then external testers (lighter beta review).
   - **Done when:** the 14 days are complete, crash-free on both stores' test tracks, feedback triaged.

13. **Store listings.** Name (Apple: ≤ 30 characters), subtitle / short description, full description that matches what the app does, screenshots of the app in use (not the splash or login screen) for every required device size, feature graphic and icon, category, contact email and phone (international format), privacy policy URL. No prices, "#1" claims or mentions of the other platform in screenshots or art.
    - **Done when:** listing reviewed against the metadata rules in compliance.md.
14. **Submit for review.** Play: apply for production access, then send for review. Apple: choose the build, answer export compliance and content rights, add the demo account and review notes, submit. Typical first reviews take days, not hours; keep the backend and demo account live throughout.
    - If rejected: read the cited guideline, fix the root cause (not only the symptom), answer in the Resolution Center / Play inbox, and resubmit. Appeal only when you're sure the reviewer misread the app.
    - **Done when:** approved on both stores.

## Steps 15–17: launch and operate

15. **Staged rollout.** Play: 1% → 5% → 20% → 50% → 100% over several days; Apple: phased release over 7 days. Halt if the user-perceived crash rate approaches 1.09% or the ANR rate 0.47% (Play's bad-behaviour thresholds), or a key funnel drops.
    - **Done when:** 100% rollout with vitals under threshold.
16. **Ship fixes safely.**
    - JS-only fixes, copy and content: EAS Update with code signing, to a small channel first (`eas update --channel production --rollout-percentage 10`), then widen.
    - Anything that changes native code, permissions, payments or what the app is for: a new store build and review. Store policy forbids using OTA for those (compliance.md).
    - **Done when:** every change type has a documented route (OTA vs store).
17. **Keep it compliant every year.**
    - Upgrade Expo with each SDK release (the `expo-upgrade` skill), which carries the new Android target API (Google's deadline is each 31 Aug) and the new Xcode/iOS SDK (Apple's is each spring; iOS 27 SDK from April 2027).
    - Re-run the guards and re-check the Data safety form and privacy labels whenever you add an SDK or a data type.
    - Watch Play Console and App Store Connect inboxes for policy notices; check the deadline list in compliance.md monthly.
    - **Done when:** a recurring calendar reminder exists for each of these.
