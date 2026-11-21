# Notes for the store reviewer — <App name> <version> (<build>)

Paste the relevant parts into App Store Connect (App Review Information → Notes) and Play Console (App access, declarations). Keep the backend and demo account live for the whole review.

## Demo account

- Username: <demo@example.com>
- Password: <set in the store console, never committed to the repo>
- The account is pre-loaded with <sample data> so every feature can be reached without real payments or real users.
- If sign-in needs a one-time code: <fixed code for this account, or how the reviewer gets it>.
- Region / hardware needed: <none> or <how to test without it>.

## What the app does

<Two or three sentences: who it is for and the main task it does.>

## How to reach each feature

1. <Feature>: <tap path>.
2. <Purchase / subscription>: <tap path>. Sandbox purchases work with the reviewer's sandbox account. Restore purchases: <Settings → Restore>.
3. Account deletion: <Settings → Account → Delete account>. Also on the web at <URL>.
4. Report / block (if user-generated content): <tap path>. Reports are reviewed within <24 h> by <team>.
5. AI feature (if any): consent screen appears at <where>, naming <provider> and the data sent.

## Permissions and why

| Permission | Feature | When it is requested |
|---|---|---|
| <Camera> | <Scan receipts> | <Only when the user taps Scan> |

Demo videos for sensitive permissions (Play declarations): <links>.

## Non-obvious points

- <Anything a reviewer might misread: external links, login with a company account, content that differs by region, why a payment uses an external method allowed in that region, OTA updates only change JS content and never the app's purpose.>

## Contact during review

<Name> · <email> · <phone, international format> · available <hours and time zone>.
