---
name: app-test
description: Test a mobile app release build like a production team - unit tests, Maestro E2E flows per critical journey, a device matrix, the Play pre-launch report, and agent-driven exploratory testing through mobile-mcp that turns every crash, ANR or bug into a Maestro repro flow and a bug report. Use before any store submission, after major changes, or when asked to explore an app for bugs.
---

# app-test — Verify quality (app-factory phase 4)

Always test **release-mode builds** (`eas build --profile preview`): R8 and Hermes break code that works in development.

## 1. Automated suites

```bash
npx jest --ci                                   # unit + component (React Native Testing Library)
npx expo install --check && npx expo-doctor     # dependency and config health
maestro test .maestro/                          # one flow per journey: sign-up, core action, purchase, delete account
```

## 2. Device matrix

| Axis | Cover |
|---|---|
| Android | Oldest supported API, newest (36), a low-RAM phone (≤ 3 GB), a tablet, one Samsung and one Pixel |
| iOS | Oldest supported iOS, newest, a small iPhone (SE size), an iPad if `supportsTablet` |
| Settings | Dark mode, largest font, a screen reader on, airplane mode, slow 3G, permission denied, a non-English locale |

Upload to a Play test track to get the **pre-launch report** (crashes, accessibility, security warnings on real devices). Fix every crash.

## 3. Agent exploratory testing (mobile-mcp)

Drive the app with [mobile-mcp](https://github.com/mobile-next/mobile-mcp) (or adb / `xcrun simctl`). Explore every screen, and try what users do wrong: empty and huge inputs, negative numbers, double taps, back in the middle of a flow, rotation, denying each permission, killing the app mid-save, no network. Record **every step** in a JSON log:

```json
{
  "app_id": "com.acme.myapp", "platform": "android", "device": "Pixel 4a API 33", "build": "1.0.0 (12)",
  "steps": [
    {"action": "launch", "screen": "Welcome"},
    {"action": "tap", "text": "Sign in", "screen": "Sign in"},
    {"action": "tap", "id": "email"},
    {"action": "type", "text": "demo@acme.com"},
    {"action": "tap", "point": [540, 1650]},
    {"action": "swipe", "direction": "up"},
    {"action": "tap", "text": "Scan receipt", "screen": "Camera",
     "event": {"type": "crash", "message": "App closes when camera permission is denied", "log": "logs/crash.txt"}}
  ]
}
```

Actions: `launch`, `tap` (`text` | `id` | `point`), `long_press`, `type`, `erase`, `swipe` (`direction`), `scroll`, `back`, `hide_keyboard`, `wait` (`ms`), `assert` (`text`), `open_link` (`url`). Event types: `crash`, `anr`, `data_loss` (P0); `error`, `security` (P1); `accessibility`, `ui` (P2); `copy` (P3). Add `expected_text` to an event when you know what should have appeared.

```bash
python3 skills/app-test/scripts/explore_to_maestro.py explore-log.json \
    --out .maestro/repro --report reports/bug-report.md --json reports/explore.json \
    --expect-screens "Home,Settings,Paywall"
```

`scripts/explore_to_maestro.py` writes one Maestro flow per issue (replaying from the last launch, ending with an assertion that fails while the bug exists), a `bug-report.md` with severity, steps and evidence, and screen coverage. It exits 1 on any crash/ANR or an expected screen never reached. Commit the repro flows: once fixed, they become regression tests.

## Gate

0 crashes on the device matrix · all Maestro flows (including repros) green · pre-launch report clean · cold start within budget (for example < 1 s on a mid-range phone) · every expected screen reached in exploration.
