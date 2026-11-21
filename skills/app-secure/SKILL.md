---
name: app-secure
description: Security gate for mobile apps against OWASP MASVS - runs a MobSF static scan of the release .aab/.apk/.ipa through its REST API, maps every finding to a MASVS group, fails on high findings or a low score, plus secret, storage, network and OTA-signing checks and traffic interception against the data inventory. Use before every release build is submitted, after adding SDKs, or when asked for a mobile security review.
---

# app-secure — Verify security (app-factory phase 5)

Standard: [OWASP MAS](https://mas.owasp.org/) — MASVS says what must be true, MASTG how to test it. Background and tools: `app-factory/references/overview.md` → Security checks.

## 1. Static scan with MobSF (every release build)

```bash
docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest
export MOBSF_API_KEY=...            # from the MobSF REST API docs page
python3 skills/app-secure/scripts/mobsf_gate.py --file build/app-release.aab --max-high 0 --min-score 60 \
    --json reports/security.json --md reports/security.md --save-report reports/mobsf-raw.json
```

`scripts/mobsf_gate.py` uploads the file (`/api/v1/upload`), scans (`/api/v1/scan`), downloads the report (`/api/v1/report_json`, plus `/api/v1/scorecard` when available), groups findings into MASVS-STORAGE, CRYPTO, AUTH, NETWORK, PLATFORM, CODE, RESILIENCE and PRIVACY, and fails when highs exceed `--max-high` or the score is below `--min-score`. Offline: `--report mobsf-raw.json`. Exit 0 pass, 1 gate failed, 2 cannot reach MobSF / bad input.

Fix every high, rebuild, and re-scan **the exact binary you will submit**. Record accepted warnings with a reason in the release report.

## 2. Checks MobSF can't make for you

| MASVS | Check | How |
|---|---|---|
| STORAGE | Tokens only in Keychain/Keystore (`expo-secure-store`); nothing sensitive in logs, backups, screenshots | `preflight.sh` flags AsyncStorage tokens; review logs on a device |
| CRYPTO / CODE | No secrets in the bundle or `EXPO_PUBLIC_*` | `preflight.sh`; `gitleaks detect` on every PR |
| NETWORK | HTTPS only; pinning for high-risk apps | `preflight.sh`; mitmproxy |
| PRIVACY | Every destination is in the data inventory | Run the release build through mitmproxy, then add any unknown host to `docs/data-inventory.md` or remove the call; `app-comply/scripts/privacy_scan.py` cross-checks hosts in code |
| PLATFORM | Deep links validate input; exported components protected | Manifest review, try malformed links |
| CODE | OTA bundles signed | `updates.codeSigningCertificate` set (scaffold does this) |
| RESILIENCE | Banking/payments only: root/jailbreak and tamper detection, Play Integrity / App Attest | Frida bypass attempt; external pentest against MASVS L2 + R |

## Gate

`mobsf_gate.py` exits 0 · secret scan clean · intercepted traffic matches the data inventory · OTA code signing on · high-risk apps: external pentest report.
