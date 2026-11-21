# Compliance: Google Play, App Store and the law

An app has to pass three separate layers: **store technical rules** (SDK levels, signing, manifests), **store policy** (privacy forms, permissions, payments, content) and **the law** where your users live (India's DPDP Act, EU, US). Passing review covers only the first two; the stores do not check whether you're legal.

Two checks prevent most rejections on both stores: a **working demo account on a live backend**, and a **privacy declaration that matches what the app actually sends at runtime, every SDK included**. Do those first.

This is a compliance map for engineering, not legal advice. Several US dates are under litigation and rules change monthly, so re-check the linked source before you rely on a date.

## Compliance skills and tools

**[mjmirza/app-store-compliance](https://github.com/mjmirza/app-store-compliance)** (2.9k★, updated 15 Nov 2026) is the most complete open source option and covers both stores. It ships:

- a **pre-submission guard** script that scans your project and built artifacts and ends with `BLOCKED.`, `CLEAR.` or `NOT CHECKED.` (critical findings first);
- an **agent skill** (`agent-os/skill/SKILL.md`) that runs a full audit and can write a `RELEASE-READINESS-REPORT.md`;
- **117 documented rejection patterns** with guideline numbers and fixes (`data/rejection-patterns.json`), detection recipes for 107 of them;
- a **regulatory deadline database** (`data/regulatory-deadlines.json`, 107 entries) covering the EU AI Act, DSA, COPPA, US state age laws and India's DPDP Rules;
- playbooks: `docs/APPLE.md`, `docs/GOOGLE-PLAY.md`, `docs/PRE-SUBMISSION-CHECKLIST.md` (~100 boxes), `docs/CROSS-PLATFORM-FRAMEWORKS.md` (Expo, React Native, Flutter and others), `docs/BY-APP-TYPE.md`, EU and global regulatory guides.

Wire it in at three points: as an agent hook during development, as a CI step on every release branch, and once more on the final signed binaries.

```bash
git clone https://github.com/mjmirza/app-store-compliance ~/repositories/app-store-compliance
bash ~/repositories/app-store-compliance/scripts/install.sh --tool all
bash ~/repositories/app-store-compliance/agent-os/hooks/app-store-compliance-guard.sh /path/to/app
```

Its stated limits: a code scan can't see store-listing metadata, whether your developer account is active or agreements accepted, or whether package names are registered; accessibility checks are static only. Those stay manual.

**Other compliance skills on GitHub** (stars as of 21 Nov 2026):

| Repo | Stars | Covers |
|---|---|---|
| [safaiyeh/app-store-review-skill](https://github.com/safaiyeh/app-store-review-skill) | 466 | Validates a codebase against Apple App Review |
| [ilan-uzan/app-store-preflight](https://github.com/ilan-uzan/app-store-preflight) | 56 | Agent skill + multi-agent workflow over App Review guidelines |
| [Nikolai-Iakubovskii/app-paywall-pilot](https://github.com/Nikolai-Iakubovskii/app-paywall-pilot) | 40 | Designing App Store-compliant subscription paywalls |
| [yohannescodes/apple-app-review-compliance](https://github.com/yohannescodes/apple-app-review-compliance) | 23 | Apple guideline review skill |
| [cruisediary/apple-app-review-skills](https://github.com/cruisediary/apple-app-review-skills) | 20 | 31 checks from real rejection cases |
| [199-biotechnologies/app-store-connect-skill](https://github.com/199-biotechnologies/app-store-connect-skill) | 11 | App Store Connect from the terminal: metadata, screenshots, TestFlight, IAP |
| [octavi42/ship-expo-app-store](https://github.com/octavi42/ship-expo-app-store) | 4 | Shipping Expo iOS apps to TestFlight and review |
| [FelixGraeber/claude-aso-audit-skill](https://github.com/FelixGraeber/claude-aso-audit-skill) | 4 | Store listing (ASO) audits for both stores |
| `eas-app-stores` in [expo/skills](https://github.com/expo/skills) | 4.2k (repo) | Build, submit, TestFlight, versioning, metadata |

Google Play has far fewer dedicated skills than Apple; the app-store-compliance repo plus Google's own Play Policy Insights lint in Android Studio and the Play pre-launch report are the main automated checks.

## Documents and pages to publish or prepare

Every app needs the first seven. The rest switch on with features, categories or markets.

| Document | Required by | Must contain / do | Where it lives |
|---|---|---|---|
| Data inventory (internal) | You, as the source for every form below | Each data item: purpose, destination (server or SDK), shared or not, retention, deletion path | Repo (`docs/data-inventory.md`) |
| Privacy policy | Play (all apps, even with no data), Apple (all apps), DPDP, GDPR | Itemised data and purposes, every third party / SDK, retention, deletion, user rights and how to exercise them, contact (DPO or grievance contact), children's data, update date | Public URL + link inside the app + both store listings |
| Account & data deletion | Play (in-app + a public web page), Apple 5.1.1(v) (in-app) | Delete the account and its data, say what's kept and why, no "email us" only flows on Apple | In-app settings + web URL declared in Play Console |
| Terms of use / EULA | Apple (standard EULA or your own; subscriptions need a functional terms link), good practice on Play | Usage rules, subscription terms, liability, governing law | Public URL, linked from paywall and settings |
| Support / contact page | Apple (support URL), Play (contact email) | A real way to reach you | Public URL |
| Play Data safety form | All Play apps on any testing or production track | Collected vs shared per data type, purposes, optional/required, encryption in transit, deletion | Play Console |
| Apple privacy nutrition labels + privacy manifest | All App Store apps | Labels: data types, linked to identity or not, used for tracking. Manifest (`PrivacyInfo.xcprivacy`): required-reason APIs and tracking domains, for your code and each SDK | App Store Connect + `ios.privacyManifests` |
| Content rating | Play IARC questionnaire; Apple age rating questionnaire (4+, 9+, 13+, 16+, 18+) | Honest answers on violence, UGC, chat, gambling, location sharing, AI-generated content | Store consoles |
| Reviewer kit | Both stores (Apple 2.1 especially) | Demo account on the live backend, review notes for every non-obvious feature and purchase, demo videos | App Review information fields |
| Permission declarations | Play: SMS/call log, all-files access, background location, accessibility, exact alarms, full-screen intent, each foreground-service type | Core-use justification + demo video showing the feature | Play Console App content |
| Export compliance | Apple (encryption questions); France declaration if non-exempt crypto ships there | Whether you use non-exempt encryption | App Store Connect / `usesNonExemptEncryption` |
| EU trader details | Apple DSA trader status (else removed from EU storefront); Play trader info | Legal name, address, phone, email (shown publicly) | Store consoles |
| AI-use notice and consent | Apple 5.1.2(i) when personal data goes to a third-party AI; EU AI Act Art. 50 | Names the AI provider and the data types, before data leaves the device; marks AI-generated content | In-app screen |
| Child-safety standards page | Play Child Safety Standards (social and dating apps) | Published CSAE standards, in-app reporting, CSAM response protocol, named contact | Public URL |
| UGC moderation policy | Apple 1.2; Play UGC policy | Filtering, report, block, response time, published contact | In-app + public page |
| Subscription disclosures | Apple 3.1.2; Play Subscriptions policy | Price, period, renewal, free-trial terms, how to cancel, before purchase | Paywall screen |
| Accessibility statement | EU Accessibility Act, if your service is in scope (e.g., e-commerce, banking, transport, e-books) | Annex V accessibility information; WCAG 2.1 AA / EN 301 549 | Terms or a public page |
| Grievance / DPO contact and breach plan | India DPDP Rules (from 13 May 2027) | Contact for data questions; breach notice to the Data Protection Board without delay and a detailed report within 72 hours | Privacy policy + internal runbook |
| Category declarations | Play: financial features, health apps, government, news, VPN; Apple: regulated apps under a legal entity | Licences, entity proof; India personal-loan apps must be on RBI's digital-lending-apps list | Store consoles |
| Open-source licence notices | Licences of your dependencies | Attribution list | In-app "Licences" screen |

## Google Play in detail

Play enforces on a ladder: rejected update → app removal → app suspension → account termination, and repeated suspensions can close linked accounts. Most problems surface as a blocked update first, so read every Policy status email.

**Account and program**

| Rule | Detail |
|---|---|
| Organization account for regulated categories | Finance (banking, loans, stock trading, funds, crypto wallets/exchanges), health (medical, human-subjects research), VPN and government apps must publish from an organization account with a D-U-N-S number ([Play Console Requirements](https://support.google.com/googleplay/android-developer/answer/10788890)); policy deadline 30 Sep 2026 |
| Developer verification | Identity + package-name registration, on and off Play; enforced in Brazil, Indonesia, Singapore, Thailand from 30 Sep 2026, global in 2027 |
| Closed testing | New personal accounts: ≥ 12 testers, 14 continuous days, then production-access questions |

**Technical requirements**

| Rule | Detail |
|---|---|
| Target API | New apps and updates: Android 16 (API 36) from 31 Aug 2026 (extension to 1 Nov 2026) |
| Format and signing | Android App Bundle + Play App Signing |
| Native code | 64-bit ABIs and 16 KB memory-page support for native libraries |
| Billing library | Play Billing Library v8+ for new apps and updates from 31 Aug 2026 (extension to 1 Nov 2026) † |
| Integrity | Use the Play Integrity API, verified server-side; SafetyNet Attestation is gone |
| Foreground services | Declare each `foregroundServiceType` in the manifest with its permission, and in Play Console with a demo video |
| Coming: optimisation | From Feb 2027, at least 25% R8 optimisation coverage, no bitmaps held in non-visible states, memory within thresholds † |
| Coming: credentials | From Apr 2027, apps with sign-in must restore it on a new device via the Restore Credentials API † |

**Privacy and the Data safety form** ([official guide](https://support.google.com/googleplay/android-developer/answer/10787469))

- Required for every app on any testing or production track, even if it collects nothing (exempt: internal-track-only, system and private apps).
- **Collected** = any data sent off the device, including by SDKs and by webviews you control. **Shared** = transferred to a third party; service providers acting for you, legal requests, user-initiated sharing with prominent disclosure, and fully anonymised data don't count as sharing.
- On-device-only processing and end-to-end encrypted data are not "collected".
- 14 data categories to answer: location, personal info, financial, health and fitness, messages, photos and videos, audio, files, calendar, contacts, app activity, web browsing, app info and performance, device IDs.
- Declare encryption in transit and the deletion mechanism (in-app, form or email; or automatic deletion within 90 days).
- Optional badges: Families policy commitment, Independent Security Review (MASA/MASVS via an authorised lab), and in India the **"Offers payments through UPI"** badge.
- A mismatch between behaviour and declaration means fix-or-enforcement: blocked updates or removal.
- Sensitive data a user wouldn't expect you to collect also needs an in-app prominent disclosure and consent before collection.

**Permissions with restrictions**

| Permission / API | Allowed when |
|---|---|
| SMS, Call Log | Default SMS/dialer or an approved exception; declaration required (policy update due 27 Jan 2027) |
| Background location | Core feature the user understands; declaration + video (location-button and geofencing changes due 27 Jan 2027) |
| All-files access | File managers, backup and similar; otherwise use scoped storage |
| Photos / videos | Broad `READ_MEDIA_*` only for apps whose core use is media; everyone else uses the Photo Picker (since May 2025) |
| Contacts | From 27 Jan 2027 (API 37 targets), `READ_CONTACTS` only when the Contact Picker can't do the job, with a declaration |
| Accessibility API | Only to help users with disabilities, or with a declaration for other approved uses |
| Exact alarms, full-screen intents | Alarm/calendar/calling apps; declaration |
| Package visibility (`QUERY_ALL_PACKAGES`) | Core need to see all installed apps |
| Coming | AppFunctions API declaration (14 Apr 2027); local network and manage-contacts declarations (25 Aug 2027) |

**Payments, ads and content**

| Area | Rule |
|---|---|
| Digital goods | Play Billing for in-app digital goods and subscriptions (alternative billing only where Google runs a programme, e.g., US external links with transaction reporting) |
| Subscriptions | Clear price, period, trial and cancellation before purchase; policy update due 27 Jan 2027 |
| Ads | No unexpected full-screen ads at launch or mid-task; interstitials closable; ads must not mimic system UI |
| Children | Target audience declaration; if children are a target, the Families policy and only Families-certified ad SDKs; policy updates 26 Aug 2026 |
| Child safety | Social and dating apps: published CSAE standards, in-app reporting, CSAM response, named contact |
| UGC and generative AI | Moderation, reporting and blocking; AI-generated content must not be harmful and users must be able to report it |
| Financial (India) | Personal-loan apps need RBI licensing, must be on RBI's "DLAs deployed by Regulated Entities" list (new apps since 30 Oct 2025; existing apps by 28 Jan 2026), must name every partner NBFC/bank in the description, and complete the financial features declaration ([Personal loans in India](https://support.google.com/googleplay/android-developer/answer/16604194)) |
| Health | Health apps declaration; justify each Health Connect permission; medical-device disclaimer where relevant |
| Listing | Accurate title, description and screenshots; no keyword stuffing, fake ratings or misleading claims |

† Tracked in the app-store-compliance deadline database from Google's developer pages; re-check the linked Google source before relying on it. Full list of dated changes: [Play policy deadlines](https://support.google.com/googleplay/android-developer/table/12921780).

## Apple App Store in detail

Apple reviews every build by hand on a real device. Treat the reviewer as a one-shot integration test with no context: everything they need must work at submission time. [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) were last updated 16 Oct 2026.

**Technical and upload requirements** ([Upcoming requirements](https://developer.apple.com/news/upcoming-requirements/))

| Rule | Detail |
|---|---|
| SDK | Built with Xcode 26 and an iOS 26-family SDK (since 28 Apr 2026); iOS 27 SDK required from April 2027 † |
| Minimum OS | Apps must target iOS 13 or later (since 9 Sep 2026) |
| Required-reason APIs | Approved reasons declared for listed APIs in your code and third-party SDKs (since 1 May 2024); SDK privacy manifests and signatures for commonly used SDKs |
| Software (2.5) | Public APIs only; IPv6-only networks supported; no downloaded code that changes features; background modes only for their purpose; no hidden, dormant or undocumented features |
| Export compliance | Answer the encryption questions (set `usesNonExemptEncryption` in Expo); France needs a declaration for non-exempt crypto |

**Privacy (section 5.1)**

| Rule | Detail |
|---|---|
| 5.1.1 Data collection | Privacy policy link in the app and the listing; consent before collection; collect only what the feature needs; don't make paid features depend on granting data access; **in-app account deletion** for any app with account creation |
| 5.1.2 Data use | Explicit permission before using or sharing personal data, **including sending it to a third-party AI** (consent modal naming the provider and data types); App Tracking Transparency before any cross-app tracking; no repurposing without new consent |
| Privacy labels | Nutrition labels must match runtime behaviour including SDKs |
| Purpose strings | Every permission prompt names the real feature ("Scan receipts to add expenses", not "Needs camera") |
| 4.8 Login services | If you offer third-party or social login for the primary account, also offer an equivalent option that limits data to name and email and allows a private relay email (Sign in with Apple qualifies) |

**Payments (section 3.1)**

| Rule | Detail |
|---|---|
| 3.1.1 In-app purchase | Required for unlocking digital features, content, subscriptions, game currency; disclose loot-box odds; restore purchases |
| 3.1.2 Subscriptions | Minimum period 7 days; clear pricing, renewal and cancellation terms before purchase; ongoing value |
| 3.1.3 Exceptions | Reader apps (with entitlement), multiplatform services, enterprise, one-to-one live services, physical goods and services (use other payments), companion apps |
| Storefront rules | US storefront: links to outside purchases allowed; EU: alternative payments only with the StoreKit External Purchase entitlement and disclosure sheet (DMA) |
| First IAP | Submit the first in-app purchase of each type together with a new app version |

**Content, design and metadata**

| Guideline | Rule |
|---|---|
| 2.1 Completeness | Final build, no placeholders, live backend, demo account or demo mode, purchases visible and working |
| 2.3 Metadata | Name ≤ 30 characters, no keyword stuffing or prices; screenshots show the app in use; honest age-rating answers; new features in review notes |
| 4.2 Minimum functionality | More than a repackaged website or link collection |
| 4.3 Spam | No clones, duplicates or low-effort apps in saturated categories (dating, flashlight, wallpapers, simple timers and similar) |
| 1.2 UGC | Filter objectionable content, report with timely response, block users, published contact |
| 1.3 / 5.1.4 Kids | No external links or purchases without a parental gate; no third-party analytics or ads (narrow exceptions); COPPA/GDPR compliance |

**Age ratings and age laws**

- New rating tiers: 4+, 9+, 13+, 16+, 18+. Answers to the updated questionnaire were due 31 Jan 2026; without them, updates are interrupted.
- From September 2026 you must declare whether the app has social-media capabilities to submit any update; declaring it means a minimum 13+ rating and the Declared Age Range API to serve under-13 users †.
- US state app-store laws (Texas, Utah, Louisiana, Alabama) are served through the Declared Age Range API on iOS and the Play Age Signals API on Android (Legal layer below).

**Account and EU**

- DSA trader status must be declared and verified, or the app is removed from the EU App Store (since 17 Feb 2025).
- The Account Holder must accept every new Program License Agreement update and attachment, or submissions stop.

† From Apple Developer news as tracked in the app-store-compliance database; check the linked Apple page before relying on the date.

## Legal layer by region

Store approval doesn't make an app legal. These laws apply based on where your users are, not where you are.

**India: Digital Personal Data Protection Act 2023 + DPDP Rules 2025** (notified 13 Nov 2025; [Hogan Lovells summary](https://www.hoganlovells.com/en/publications/indias-digital-personal-data-protection-act-2023-brought-into-force-), [Rules PDF](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf))

| Phase | What applies |
|---|---|
| Now | Data Protection Board set up, with investigation and appeal powers |
| 13 Nov 2026 | Registered Consent Managers start; be ready to work with them |
| 13 May 2027 | The main obligations below |

- **Notice:** a standalone, plain-language notice with an itemised list of personal data, each purpose, what the processing enables, and links to withdraw consent, exercise rights and complain to the Board.
- **Consent:** free, specific, informed, unambiguous, by a clear affirmative action; no bundled consent; withdrawal as easy as giving it, after which the data is deleted unless another law needs it.
- **Children (under 18):** verifiable parental consent before processing (using data you already hold, details the parent provides, or a government-backed token such as DigiLocker); no behavioural tracking or targeted ads aimed at children.
- **Security and breaches:** reasonable safeguards; tell the Board without delay on discovering a breach, a detailed report within 72 hours, and notify affected users promptly.
- **Retention:** keep data, traffic data and logs at least 1 year; large e-commerce, social and gaming platforms delete after 3 years of user inactivity, with prior notice.
- **Contact and grievances:** publish who answers data questions (a DPO for significant data fiduciaries) and how users exercise their rights, including nominees.
- Apps that host user content are also "intermediaries" under the IT Rules 2021 and need a grievance officer; fintech apps add RBI rules (see Play's India loan-app policy above).

**European Union**

| Law | What it means for an app |
|---|---|
| GDPR | A lawful basis per purpose, consent for non-essential tracking, processor agreements with SDK vendors, user rights (access, deletion, portability), breach notice to the authority within 72 hours, transfer safeguards for non-EU servers |
| Digital Services Act | Trader status on both stores; UGC apps need notice-and-action and clear terms |
| EU AI Act | Art. 5 prohibited practices and Art. 4 AI literacy since 2 Feb 2025; **Art. 50 transparency from 2 Aug 2026**: tell users they're interacting with AI and mark AI-generated audio, image, video and text in machine-readable form; systems already on the market must retrofit marking by 2 Dec 2026 † |
| European Accessibility Act | Since 28 Jun 2025 for in-scope services (e-commerce, banking, transport, e-books, communications): WCAG 2.1 AA / EN 301 549 and published accessibility information |
| Digital Markets Act | Alternative payments and external offers on iOS only under Apple's EU entitlements and terms |

**United States**

| Law | What it means for an app |
|---|---|
| COPPA (amended rule) | Compliance date 22 Apr 2026 for child-directed apps or known under-13 users: verifiable parental consent, separate opt-in for ads or third-party disclosure, written retention and security programmes, biometrics count as personal info ([FTC](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data)) |
| State App Store Accountability Acts | Texas SB 2420 (effective 1 Jan 2026; injunction stayed by the Fifth Circuit on 4 Jun 2026, so in force while appeals continue), Utah, Alabama; Louisiana from 1 Jul 2027. Read the user's age category from the store, get parental consent for minors, re-ask on major changes ([FPF comparison](https://fpf.org/blog/comparing-enacted-app-store-accountability-acts/)) † |
| State privacy laws (California CCPA/CPRA and others) | Notice at collection, rights to know, delete and correct, "Do Not Sell or Share", honour Global Privacy Control |
| Biometrics (Illinois BIPA, Texas CUBI) | Written consent before capture, a published retention and destruction schedule |
| Health data | HIPAA if you work with covered entities; otherwise the FTC Health Breach Notification Rule |

Every other country, continent by continent, with registration, DPO, breach deadlines, transfer rules, children's age and penalties: 

† Litigation or legislative changes in progress; dates via the app-store-compliance deadline database, re-check the source.

## Upcoming deadlines

As of 21 Nov 2026, soonest first. † = from the app-store-compliance database (source linked there); the rest checked against the official page.

| Date | Who | Requirement |
|---|---|---|
| 2 Dec 2026 | EU AI Act | Retrofit machine-readable AI-content marking on generative features already on the market † |
| 12 Jan 2027 | Apple | New age-rating content descriptors for shared location and dating † |
| 27 Jan 2027 | Google Play | Policy updates: contacts (Contact Picker first), location (location button, no foreground-service geofencing), SMS/call log, foreground-service and full-screen intent, subscriptions ([Play deadlines](https://support.google.com/googleplay/android-developer/table/12921780)) |
| Feb 2027 | Google Play | Technical quality: ≥ 25% R8 optimisation coverage, bitmap and memory thresholds † |
| Apr 2027 | Apple | Uploads must use the iOS 27 / iPadOS 27 SDK † |
| Apr 2027 | Google Play | Sign-in apps must restore credentials on a new device † |
| 14 Apr 2027 | Google Play | AppFunctions API declaration ([Play deadlines](https://support.google.com/googleplay/android-developer/table/12921780)) |
| 13 May 2027 | India DPDP | Notice, consent, children's consent, security, breach reporting, retention, rights management take effect |
| 1 Jul 2027 | Louisiana | App Store Accountability Act takes effect † |
| 25 Aug 2027 | Google Play | Local network and manage-contacts permission declarations ([Play deadlines](https://support.google.com/googleplay/android-developer/table/12921780)) |
| 31 Aug 2027 | Google Play | Play Billing Library v8+ for all apps, not just new ones and updates † |

Google raises the target API every August and Apple the SDK floor every spring, so plan one compliance upgrade a year in each window.

## Sources

- [mjmirza/app-store-compliance](https://github.com/mjmirza/app-store-compliance): README, `docs/PRE-SUBMISSION-CHECKLIST.md`, `data/regulatory-deadlines.json` (v2.4.0, entries verified 14–15 Nov 2026)
- Google: [Play Console Requirements](https://support.google.com/googleplay/android-developer/answer/10788890) · [Data safety section](https://support.google.com/googleplay/android-developer/answer/10787469) · [Personal loans in India](https://support.google.com/googleplay/android-developer/answer/16604194) · [Policy deadlines](https://support.google.com/googleplay/android-developer/table/12921780) · [Target API level](https://developer.android.com/google/play/requirements/target-sdk) · [App testing for new personal accounts](https://support.google.com/googleplay/android-developer/answer/14151465) · [Developer verification](https://developer.android.com/blog/posts/android-developer-verification-rolling-out-to-all-developers-on-play-console-and-android-developer-console) · [Android vitals](https://developer.android.com/google/play/vitals)
- Apple: [App Review Guidelines (updated 16 Oct 2026)](https://developer.apple.com/app-store/review/guidelines/) · [Upcoming requirements](https://developer.apple.com/news/upcoming-requirements/)
- OTA policy: [Bitrise, what stores allow with OTA updates](https://bitrise.io/blog/post/what-app-stores-allow-with-ota-updates-apple-and-google-policy-explained)
- India: [DPDP Rules 2025 (MeitY PDF)](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf) · [Hogan Lovells analysis](https://www.hoganlovells.com/en/publications/indias-digital-personal-data-protection-act-2023-brought-into-force-)
- US: [FTC amended COPPA rule](https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data) · [FPF comparison of App Store Accountability Acts](https://fpf.org/blog/comparing-enacted-app-store-accountability-acts/)
- EU: [AI Act (EUR-Lex)](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng) · [European Accessibility Act (EUR-Lex)](https://eur-lex.europa.eu/eli/dir/2019/882/oj)
- GitHub repository pages linked in the skills table (stars as of 21 Nov 2026)
