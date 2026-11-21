# Data inventory — Good Budget

## 1. Data items

| # | Data item | Play category / Apple type | Purpose(s) | Required or optional | Collected by (your code / SDK name) | Sent to (host or vendor) | Shared with third party? | Linked to user identity? | Used for tracking? | Encrypted in transit | Retention | How the user deletes it | Lawful basis (GDPR) / consent (DPDP) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Email address | Personal info / Email address · Contact Info / Email Address | Account | Required | Supabase | abcd.supabase.co | No | Yes | No | Yes | Until account deletion + 30 days | Settings → Delete account; web page | Contract |
| 2 | User IDs | Personal info / User IDs · Identifiers / User ID | Account | Required | Supabase | abcd.supabase.co | No | Yes | No | Yes | Until account deletion | Settings → Delete account | Contract |
| 3 | Purchase history | Financial info / Purchase history · Purchases | Subscriptions | Required | RevenueCat | api.revenuecat.com | No | Yes | No | Yes | 7 years (tax law) | Kept for legal reasons; anonymised on deletion | Legal obligation |
| 4 | Crash logs | App info and performance / Crash logs · Diagnostics | Stability | Required | Sentry | sentry.io | No | No | No | Yes | 90 days | Automatic expiry | Legitimate interest |
| 5 | Diagnostics | App info and performance / Diagnostics · Diagnostics | Stability | Required | Sentry | sentry.io | No | No | No | Yes | 90 days | Automatic expiry | Legitimate interest |
| 6 | Device or other IDs | Device or other IDs · Identifiers / Device ID | Stability | Required | Sentry | sentry.io | No | No | No | Yes | 90 days | Automatic expiry | Legitimate interest |
| 7 | Photos | Photos and videos / Photos · User Content | Receipt scanning | Optional | Your code | abcd.supabase.co | No | Yes | No | Yes | Until the user deletes the receipt | Delete receipt or account | Consent |

## 2. Third-party SDKs

| SDK | Version | What it collects | Ships its own iOS privacy manifest? | Data safety answers it requires | Can it be disabled until consent? |
|---|---|---|---|---|---|
| Supabase | 2.x | Email, user ID | No (JS only) | Email, User IDs | No (required) |
| RevenueCat | 9.x | Purchase history | Yes | Purchase history | No (required) |
| Sentry | 7.x | Crash logs | Yes | Crash logs, Diagnostics | No |
| Sign in with Apple (expo-apple-authentication) | 8.x | Name, email (sent to our Supabase backend) | Yes | Email address | Optional login method |

## 6. Children

- Can children use the app? No (18+ finance app)
