# Data inventory — <App name>

Last updated: <YYYY-MM-DD> · Owner: <name>

Every privacy form is generated from this table: the Play Data safety form, Apple privacy nutrition labels, the iOS privacy manifest, the privacy policy and consent screens. Update it **before** adding any SDK, permission or data field. Verify it by intercepting the release build's traffic (mitmproxy): every destination must appear here.

## 1. Data items

| # | Data item | Play category / Apple type | Purpose(s) | Required or optional | Collected by (your code / SDK name) | Sent to (host or vendor) | Shared with third party? | Linked to user identity? | Used for tracking? | Encrypted in transit | Retention | How the user deletes it | Lawful basis (GDPR) / consent (DPDP) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Email address | Personal info → Email / Contact info → Email | Account, support | Required | Your code | api.example.com | No | Yes | No | Yes (TLS) | Until account deletion + 30 days | In-app Settings → Delete account; web page | Contract |
| 2 | Crash logs | App info and performance → Crash logs / Diagnostics | App stability | Required | Sentry SDK | sentry.io | Yes (processor) | No | No | Yes | 90 days | Automatic expiry | Legitimate interest |
| 3 | | | | | | | | | | | | | |

## 2. Third-party SDKs

| SDK | Version | What it collects | Ships its own iOS privacy manifest? | Data safety answers it requires | Can it be disabled until consent? |
|---|---|---|---|---|---|
| | | | | | |

## 3. Permissions

| Platform permission | Feature that needs it | Shown to user when | Store declaration needed? | Usage string (iOS) |
|---|---|---|---|---|
| CAMERA / NSCameraUsageDescription | Scan receipts | User taps "Scan" | No | "Scan receipts to add expenses" |

## 4. Required-reason APIs (iOS privacy manifest)

| API category | Reason code | Where used (your code / SDK) |
|---|---|---|
| NSPrivacyAccessedAPICategoryUserDefaults | CA92.1 | Your code |

## 5. Cross-border transfers

| Destination country | Data items | Mechanism (adequacy, SCCs, consent, filed assessment) | Countries whose law requires it |
|---|---|---|---|
| | | | |

## 6. Children

- Can children use the app? <yes / no / mixed audience>
- Youngest age needing parental consent in your markets: <age> (see references/legal-global.md)
- Age signal used: <Apple Declared Age Range API / Play Age Signals API / own age gate>
