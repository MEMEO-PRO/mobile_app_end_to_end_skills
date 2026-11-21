---
name: app-spec
description: Turn a mobile app idea into a validated brief, a product spec and a complete data inventory, and decide which store and legal rule areas apply (kids, UGC, payments, AI, health, finance, location, launch countries). Use at the start of a new app, before adding a feature that collects new data, or when the privacy forms need a source of truth.
---

# app-spec — Plan (app-factory phases 1–2)

The data inventory written here is the source for every privacy form later: Play Data safety, Apple privacy labels, the iOS privacy manifest, the privacy policy and consent screens. Get it right once and the rest is copying.

## Steps

1. **Brief (one page).** Problem in one sentence, the user, the top 10 competitors in both stores (rating, 1–2★ complaints, price), the differentiator, one success metric. Reject ideas that are a clone (Apple 4.3) or a website wrapper (Apple 4.2).
2. **Spec.** User stories, every screen, edge cases (offline, empty, error, slow network, permission denied), analytics events, non-goals.
3. **Switched-on rule areas.** Answer yes/no and record in the spec. Each yes adds work in `app-comply`:

   | Area | Adds |
   |---|---|
   | Accounts | In-app + web account deletion; Sign in with Apple if you offer Google/Facebook login |
   | Kids under 13–18 (by country) | Families / Kids Category rules, parental consent, no third-party ads/analytics |
   | User-generated content | Filter, report, block, published contact; child-safety page for social apps |
   | Payments | Store billing for digital goods, restore purchases, subscription terms |
   | AI features | Consent naming the provider before sending personal data; AI-content labels in the EU |
   | Health / finance / VPN / government | Organization account + D-U-N-S, licences, extra declarations |
   | Location, contacts, SMS, files | Permission declarations, pickers instead of broad permissions |
   | Launch countries | Per-country legal table (`app-factory/references/legal-global.md`) |

4. **Data inventory.** Copy `app-factory/templates/data-inventory.md` to `docs/data-inventory.md`. One row per data item: purpose, collector (your code or SDK), destination host, shared or not, linked to identity, tracking, retention, deletion path, lawful basis. Once code exists, `app-comply/scripts/privacy_scan.py` drafts the rows from the dependencies.
5. **Check it.**

```bash
python3 skills/app-spec/scripts/inventory_lint.py docs/data-inventory.md --json reports/inventory.json
```

`scripts/inventory_lint.py` fails on empty cells, `<placeholders>`, missing columns, a shared item with no recipient, and an unanswered children section. It warns on Yes/No columns with other answers and on tracking rows (which need App Tracking Transparency).

## Gate

`inventory_lint.py` exits 0 · brief and spec reviewed · rule areas and launch countries listed in the spec.

## Hand-off

Pass the rule areas to `app-build` (permissions and screens), `app-comply` (forms and declarations) and the countries to the legal table in `docs/legal.md`.
