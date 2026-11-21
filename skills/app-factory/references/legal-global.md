# Global law map: every continent

Data-protection law follows your **users**, not your company: if your app is offered to people in a country, that country's law usually applies, even if you have no office there. This tab covers 45+ jurisdictions on every inhabited continent, as of 21 Nov 2026. It is an engineering map, not legal advice; for any market that brings real revenue, confirm with local counsel.

**Routine for every market you switch on in the store consoles**

1. **Find the law** in the tables below and note its status (in force, phased, pending).
2. **Registration:** do you need to register with the regulator, or name a local representative, before launch? (E.g., Turkey VERBIS, Kenya ODPC, Egypt licence, Russia Roskomnadzor notice, Philippines NPC, Peru registry, China MIIT filing.)
3. **People:** do you need a DPO or named privacy officer?
4. **Children:** which age needs parental consent (ranges from under 10 to under 18)? Wire the store age signal (Apple Declared Age Range API, Play Age Signals API) where age laws apply.
5. **Data location and transfers:** can data leave the country, and under what mechanism (adequacy, standard clauses, assessment filed with the regulator)? Is local storage required (Russia, parts of Vietnam, Bangladesh, UAE health data)?
6. **Breach runbook:** set your incident clock to the shortest deadline among your markets (Russia 24 h; most others 72 h; Peru 48 h; Colombia 15 business days).

Then update the privacy policy, consent screens and Data safety / privacy labels to match, and only then enable the country in Play Console and App Store Connect. Markets that need a local entity (China) or regulator approval first (Egypt licence) should stay off until that's done.

## Europe

The EU app-specific laws (DSA, AI Act, Accessibility Act, DMA) are on the Compliance tab; this table adds the data-protection baseline and non-EU Europe.

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children's consent age | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| EU (27 states) | GDPR (Reg. 2016/679), since 2018 | Lawful basis per purpose; records of processing; **Art. 27 EU representative** if you have no EU establishment; DPO if large-scale monitoring or special-category data; transfers via adequacy, SCCs or BCRs | Authority ≤ 72 h; users without undue delay if high risk | 16 by default; 13 in BE DK EE FI LV MT PT SE, 14 in AT BG CY IT LT ES, 15 in CZ FR GR | €20m or 4% of global turnover | [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng); ages via [euconsent](https://euconsent.eu/digital-age-of-consent-under-the-gdpr/) |
| EEA (Norway, Iceland, Liechtenstein) | GDPR via the EEA Agreement | Same as EU | ≤ 72 h | Norway 13 | As GDPR | [DLA Piper NO](https://www.dlapiperdataprotection.com/guide.pdf?c=NO) |
| United Kingdom | UK GDPR + Data Protection Act 2018, amended by the Data (Use and Access) Act 2025 (commenced 5 Feb 2026); Online Safety Act 2023; ICO Children's Code | UK representative if no UK establishment; re-audit every SDK, pixel and fingerprinting call under the ICO storage-and-access guidance (29 Apr 2026); answer data-subject complaints within 30 days; services likely used by children: privacy-high defaults, geolocation and profiling off, DPIA; user-to-user services: OSA risk assessment and highly effective age assurance where required | ICO ≤ 72 h | 13 | £17.5m or 4% (UK GDPR / PECR); OSA £18m or 10% | Subscription rules (pre-contract info, renewal reminders, easy cancellation) due from Jan 2027 (draft regulations); under-16 social-media restrictions planned for spring 2027 † |
| Switzerland | nFADP (2020), in force 1 Sep 2023 | **Swiss representative** if you target or monitor people in CH at large scale and high risk; records of processing (if ≥ 250 staff or high-risk); transfers via adequacy or SCCs | FDPIC "as soon as possible" if high risk | Not fixed | CHF 250,000, levied on the **responsible individual** | [DLA Piper CH](https://www.dlapiperdataprotection.com/guide.pdf?c=CH) |
| Russia | Federal Law 152-FZ, tightened 30 May and 1 Jul 2025 | **Notify Roskomnadzor before processing**; DPO mandatory; **localise**: Russian citizens' data must first be recorded and stored in Russian databases; notify before cross-border transfers | Roskomnadzor **24 h** (incident) and 72 h (investigation) | Unverified | Repeat leaks: 1–3% of revenue; localisation up to RUB 18m | Devices sold in Russia must allow installing, updating and paying through RuStore (from 1 Sep 2025); sanctions also restrict distribution, so check before enabling Russia. [DLA Piper RU](https://www.dlapiperdataprotection.com/guide.pdf?c=RU) |
| Turkey | KVKK Law No. 6698 (2016) | **VERBIS registration** (exempt if < 50 staff and < TRY 100m balance sheet unless sensitive data is core); **Turkish representative** for foreign controllers; SCC transfers must be notified within 5 business days | Authority ≤ 72 h | Not specified | ~TRY 13.6m per breach (indexed yearly) | Social-network rules under the Internet Law (fines up to 3% of global turnover). [DLA Piper TR](https://www.dlapiperdataprotection.com/index.html?t=law&c=TR) |

† From the app-store-compliance repo's `docs/GLOBAL-REGULATORY-2026.md`, which links the UK government and ICO sources.

## Asia

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| India | DPDP Act 2023 + Rules 2025; Consent Managers from 13 Nov 2026; main duties 13 May 2027 | Standalone itemised notice; unbundled consent with easy withdrawal; published data-query contact (DPO if significant fiduciary); 1-year minimum log retention | Board without delay + detailed report ≤ 72 h; users promptly | **Under 18**: verifiable parental consent; no tracking or targeted ads | Up to ₹250 crore (security failures) | IT Rules amendment (from 20 Feb 2026) requires labelling AI-generated content with 2–3 h takedown windows †. Details on the Compliance tab |
| China | PIPL; CAC rules | **MIIT app filing** (only a Chinese entity can file, so foreign developers need a local partner); data localisation; real-name verification; content moderation; games need a Banhao licence | Regulator + users promptly | Under 14: guardian consent; minors mode | Up to 5% of revenue (PIPL) | AI companion/chat apps: minors mode, no virtual companions for minors (from 15 Jul 2026) † |
| Japan | APPI; amendment Act No. 56 of 2026 (in force by Jul 2028) | Disclose recipient country and its regime for consent-based transfers; law reaches foreign operators | PPC + users for serious breaches | Under 16: legal representative consents (new amendment) | Surcharge regime coming | Mobile Software Competition Act in full effect since 18 Dec 2025: alternative stores and payments on iOS/Android in Japan † |
| South Korea | PIPA (amendment in force 11 Sep 2026: CEO accountability, chief privacy officer) | Alternative in-app payments under the Telecommunications Business Act need a Korea-only binary and Apple's KR entitlement | PIPC + users | Under 14: guardian consent | Up to 3% of revenue (reported rise to 10% unverified) | GRAC age ratings override on the Korean App Store † |
| Singapore | PDPA | DPO required; consent | PDPC ≤ 3 days | App stores enforce under-18 age assurance (since 1 Apr 2026) | Up to 10% of SG turnover | Apple blocks 18+ downloads in Singapore without age verification (since 24 Feb 2026) † |
| Vietnam | PDPL Law 91/2025, in force 1 Jan 2026 + Decree 356/2025 | **File a DPIA and a transfer impact assessment with A05 (Ministry of Public Security)**; DPO or data-protection unit (5-year grace for small firms) | A05 ≤ 72 h | Parental consent; child also consents from age 7 | Up to 5% of revenue (transfer breaches) | Region-specific App Store age rating since 18 Jun 2026. [DLA Piper VN](https://www.dlapiperdataprotection.com/index.html?t=law&c=VN) |
| Indonesia | PDP Law 27/2022 (in force since Oct 2024) | **Electronic System Operator registration with KOMDIGI** for foreign apps; child-protection self-assessment (PP 17/2025) by **31 Dec 2026** | Users and agency ≤ 72 h | Parental consent; under-16 limits on high-risk services | 2% of annual revenue | [AHP update](https://www.ahp.id/clientalert/AHPClientUpdate-1October2026.pdf) |
| Thailand | PDPA 2019 | DPO if large-scale monitoring or sensitive data | PDPC ≤ 72 h | Under 10: parental consent | THB 5m + criminal penalties | [DLA Piper TH](https://www.dlapiperdataprotection.com/index.html?t=law&c=TH) |
| Malaysia | PDPA 2010, amended 2024 (in force 2025) | DPO if > 20k data subjects or > 10k sensitive records | Commissioner ≤ 72 h; users ≤ 7 days | Under 18: parental consent | RM1m and/or 3 years | [Ridza Law](https://www.ridzalaw.com.my/post/malaysia-s-personal-data-protection-amendment-act-2024) |
| Philippines | Data Privacy Act 2012 | DPO mandatory; **register with the NPC** if ≥ 250 staff or sensitive data on ≥ 1,000 people, and show the registration online | NPC and users ≤ 72 h | Not fixed in law | PHP 5m per act | [NPC circular](https://privacy.gov.ph/wp-content/uploads/2022/08/NPC-CIRCULAR-NO.-2022-01-GUIDELINES-ON-ADMINISTRATIVE-FINES-dated-08-AUGUST-2022-w-SGD.pdf) |
| Pakistan | No data-protection law yet (2023 bill is a draft); PECA 2016 amended 2025 | Social-media platforms must enlist with the new SMPRA | None (draft: 72 h) | Not specified | PKR 5m and/or 3 years (identity data offences) | [DLA Piper PK](https://www.dlapiperdataprotection.com/index.html?t=law&c=PK) |
| Bangladesh | Personal Data Protection Act 2026 (some sections await notification) | Chief data officer for significant controllers; a synced local copy of cloud data may be required | Set by regulation | Under 18: parental consent | Up to 5% of Bangladesh turnover | Details from the 2025 Ordinance; the Act may differ. [DataGuidance](https://www.dataguidance.com/jurisdictions/bangladesh) |
| Sri Lanka | PDPA 2022, amended 2025; main duties start on a date still to be gazetted | DPO for large-scale monitoring or special data (draft rules) | ≤ 72 h (draft) | Children's data is special category | LKR 10m per breach | [DLA Piper LK](https://www.dlapiperdataprotection.com/index.html?t=law&c=LK) |
| Taiwan | PDPA, amended 11 Nov 2025 (start date pending) | New PDP Commission being set up | Users now; regulator after amendments | Unverified | NT$15m per violation | [K&L Gates](https://www.klgates.com/thought-leadership/New-Developments-in-the-Taiwan-Personal-Data-Protection-Act-1-13-2026) |
| Hong Kong | PDPO (Cap. 486) | No registration; strict direct-marketing consent | Voluntary | Not specified | HK$1m + up to 5 years (direct marketing, doxxing) | [DLA Piper HK](https://www.dlapiperdataprotection.com/index.html?t=law&c=HK) |

† From the app-store-compliance repo's global regulatory guide (linked sources there). The India penalty figure is from the DPDP Act schedule.

## Middle East

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| UAE (onshore) | PDPL Decree-Law 45/2021 (executive regulations still not issued; compliance due 6 months after they are); DIFC and ADGM have their own laws | DPO for high-risk or large sensitive processing; transfers to approved countries; **health data and stored-value-facility data stay in the UAE** | "Immediately" (deadline to be set) | **Child Digital Safety Law** (Decree-Law 26/2025, in force 1 Jan 2026, 1-year grace): no under-13 data except strict conditions, no social accounts under 15, age verification, private defaults, parental tools | Set by Cabinet decision | [UAE government portal](https://u.ae/en/information-and-services/social-affairs/Priority-groups/children/Childrens-digital-safety) |
| Saudi Arabia | PDPL (2021, amended 2023), enforced since 14 Sep 2024 | **Register on SDAIA's National Data Governance Platform**; DPO for large-scale or sensitive processing; transfer regulations (adequacy or safeguards) | SDAIA ≤ 72 h | Unverified | SAR 5m (prison for harmful disclosure of sensitive data) | [DLA Piper SA](https://www.dlapiperdataprotection.com/index.html?t=law&c=SA) |
| Qatar | Law No. 13 of 2016 (QFC separate) | Specific duties for websites and apps processing children's data | Regulator and users ≤ 72 h | Child-directed services regulated (age not stated) | QAR 5m | [DLA Piper QA](https://www.dlapiperdataprotection.com/index.html?t=law&c=QA) |
| Israel | Protection of Privacy Law, **Amendment 13 in force 14 Aug 2025** | DPO for large-scale monitoring or sensitive data; notify the authority if especially sensitive data covers > 100k people; data security regulations | Authority immediately for serious incidents | Unverified | Administrative fines now possible (amount unverified) + statutory damages | [DLA Piper IL](https://www.dlapiperdataprotection.com/index.html?t=law&c=IL) |

Turkey is in the Europe table.

## Africa

Several African laws require **registration before processing**, which most app teams miss.

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| Nigeria | NDPA 2023 + GAID 2025 (binding since 20 Mar 2025) | **Register with the NDPC** if "of major importance" (e.g., > 200 data subjects in 6 months), fees ₦10k–₦250k by tier; annual compliance audit return (due 31 Mar) for higher tiers; DPO for major-importance controllers | NDPC ≤ 72 h | Under 18 | Higher of 2% of revenue or ₦10m | Applies to foreign apps targeting Nigerians. [DLA Piper NG](https://www.dlapiperdataprotection.com/index.html?t=law&c=NG) |
| Kenya | Data Protection Act 2019 | **Register with the ODPC** (exempt below KES 5m turnover and < 10 staff, except sectors such as digital credit, ride-hailing and direct marketing, which always register); certificate valid 24 months | Commissioner ≤ 72 h | Unverified | KES 5m or 1% of turnover (the lower) | [DLA Piper KE](https://www.dlapiperdataprotection.com/index.html?t=law&c=KE) |
| South Africa | POPIA 2013 | **Register an Information Officer** with the Information Regulator; prior authorisation in some cases (e.g., children's data to an inadequate country) | Regulator and users as soon as reasonably possible | Unverified | R10m and/or 10 years | [DLA Piper ZA](https://www.dlapiperdataprotection.com/index.html?t=law&c=ZA) |
| Egypt | PDPL 151/2020; **Executive Regulations (Decree 816/2025) issued 1 Nov 2025** | **Licence or permit** from the Personal Data Protection Centre (fees up to EGP 2m); registered DPO; **foreign entities targeting Egypt must appoint a local representative** | Centre ≤ 72 h; users within 3 working days after | Under 15: guardian's written consent | EGP 5m and/or prison | [Al Tamimi](https://www.tamimi.com/law_update_articles/from-policy-to-practice-egypt-issues-executive-regulations-of-the-personal-data-protection-law/) |
| Ghana | Data Protection Act 2012 | **Register with the Data Protection Commission** (renew every 2 years; foreign controllers register as an external company) | As soon as reasonably practicable | Not specified | ~GHS 30k and/or 5 years (sale of data) | [DLA Piper GH](https://www.dlapiperdataprotection.com/index.html?t=law&c=GH) |

Other African markets (e.g., Rwanda, Uganda, Morocco, Tunisia, Senegal, Zambia) also have data-protection laws, many with registration duties; check the regulator before enabling them.

## North America

US federal and state rules (COPPA, App Store Accountability Acts, CCPA, BIPA, health data) are on the Compliance tab. Two more US items from the repo's global guide: the **FTC negative-option (click-to-cancel) rules** for subscriptions, and **ADA Title II** web/app accessibility for public entities from 26 Apr 2027 †.

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| Canada (federal) | PIPEDA (2000); Bill C-36 tabled 15 Jun 2026 would replace it | Name an accountable person; tell users data may be stored abroad | OPC and users as soon as feasible if real risk of significant harm; keep breach records 24 months | No statutory age | CAD 100k per offence today (C-36 proposes up to CAD 25m / 5%) | [Justice Laws](https://laws-lois.justice.gc.ca/eng/acts/p-8.6/page-5.html) |
| Quebec | Law 25 (fully in force 22 Sep 2024) | Person in charge of personal information; **privacy impact assessment + contract before any transfer outside Quebec**; **highest privacy settings by default**; tracking, location and profiling **off by default** (opt-in) | CAI and users promptly if risk of serious injury | **Under 14**: parent consent | CAD 25m or 4% of global turnover | [DLA Piper CA](https://www.dlapiperdataprotection.com/guide.pdf?c=CA) |
| Mexico | New LFPDPPP (in force 21 Mar 2025; INAI dissolved, enforced by the anti-corruption ministry SABG) | Privacy notice; named data officer for ARCO requests; pass the notice to third-party recipients | Users immediately if rights are significantly affected (no authority notice) | Not specified | Up to 320,000 UMA (doubled for sensitive data) | [DLA Piper MX](https://www.dlapiperdataprotection.com/guide.pdf?c=MX) |

† Via the app-store-compliance global guide.

## Latin America

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| Brazil | LGPD + **Digital ECA (Law 15,211/2025), enforceable 17 Mar 2026**, regulated by Decree 12,880; ANPD enforcement from Jan 2027 | DPO (encarregado); legal basis per purpose; **real age verification** (self-declaration no longer counts) for services likely used by minors; read the store age signal (Play Age Signals API, Apple age range) | ANPD and users within 3 working days (ANPD rule) | Under 18 protections; guardian authorisation for minors | ECA: up to R$50m or 10% of Brazilian revenue | Stores must block gambling apps and apps without age verification; Apple blocks 18+ downloads in Brazil without verification; iOS alternative stores and payments allowed in Brazil from iOS 26.5 † |
| Mexico | See North America |  |  |  |  |  |
| Argentina | Law 25,326 (2000) | **Register databases with the AAIP**; transfers only to adequate countries or with consent; privacy policy must show the controller's legal address | No statutory duty | Unverified | ARS 100k per infraction (scaled for repeats) | [DLA Piper AR](https://www.dlapiperdataprotection.com/guide.pdf?c=AR) |
| Chile | Law 21.719 (amends Law 19.628). Start date **1 Dec 2026**; Congress voted on 17 Nov 2026 to move it to 15 Oct 2027, pending publication | **Foreign companies must file an electronic contact with the new Agency**; transfers via adequacy, SCCs or BCRs | Agency without undue delay; users if sensitive, under-14 or financial data | Under 14: parental consent; sensitive data of under-16s: parental consent | 20,000 UTM (~US$1.6m); 2–4% of revenue for large repeat offenders | [BCN Ley Chile](https://www.bcn.cl/leychile/Navegar?idNorma=1209272&idVersion=2026-12-01) |
| Colombia | Law 1581 (2012) | **Register databases in the RNBD** if assets > 100,000 UVT; name a person for data requests; transfers only to adequate countries or with consent | SIC ≤ **15 business days** | Parental authorisation (no numeric age) | 2,000 monthly minimum wages (~US$955k) | Law 2489 of 2025 on minors' digital safety. [DLA Piper CO](https://www.dlapiperdataprotection.com/guide.pdf?c=CO) |
| Peru | Law 29733 + new Regulation (in force 30 Mar 2025) | **Register databases and cross-border transfers** in the national registry; **DPO phased by size** (medium firms by 30 Nov 2026, small by 30 Nov 2027); local representative | ANPD and users ≤ **48 h** | Under 14: verified parental consent | S/ 550,000 | [DLA Piper PE](https://www.dlapiperdataprotection.com/guide.pdf?c=PE) |

† Via the app-store-compliance global guide (Planalto and ANPD sources). The Brazil breach window is the ANPD's incident regulation; confirm before relying on it.

## Oceania

| Jurisdiction | Law & status | Must do before launch | Breach notice | Children | Max penalty | App-specific / source |
|---|---|---|---|---|---|---|
| Australia | Privacy Act 1988 (APPs); Online Safety Act; Social Media Minimum Age Act (in force 10 Dec 2025) | From 10 Dec 2026 the privacy policy must disclose automated decisions that significantly affect people; Children's Online Privacy Code due by 10 Dec 2026; age-restricted social platforms must stop under-16 accounts (self-declaration alone isn't enough) | OAIC and users for eligible breaches (assess within 30 days) | Under-16 social media ban; children's code coming | Social media age law: A$49.5m | Apple blocks 18+ downloads without verification (since 24 Feb 2026); 15+ rating removed (now 16+) † |
| New Zealand | Privacy Act 2020; **IPP3A in force 1 May 2026** | Privacy officer mandatory; **tell people when you collect their data indirectly** (e.g., from SDKs, ad networks, data partners); overseas disclosure only under IPP12 exceptions | Commissioner and users as soon as practicable if serious harm likely | Not specified | NZD 10,000 | Applies to overseas agencies doing business in NZ. [Privacy Commissioner](https://www.privacy.org.nz/resources-and-learning/a-z-topics/ipp3a/) |

† Via the app-store-compliance global guide (eSafety, OAIC, Apple sources).

## Sources

- Country pages on [DLA Piper Data Protection Laws of the World](https://www.dlapiperdataprotection.com/), opened 21 Nov 2026 (links in each row)
- [mjmirza/app-store-compliance ](https://github.com/mjmirza/app-store-compliance)[`docs/GLOBAL-REGULATORY-2026.md`](https://github.com/mjmirza/app-store-compliance) (UK, Australia, Brazil, Korea, Japan, China, Singapore, Vietnam, Indonesia items marked †; each item links its government source)
- Regulators and officials: [EUR-Lex GDPR](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng) · [UAE Child Digital Safety](https://u.ae/en/information-and-services/social-affairs/Priority-groups/children/Childrens-digital-safety) · [NZ Privacy Commissioner, IPP3A](https://www.privacy.org.nz/resources-and-learning/a-z-topics/ipp3a/) · [Canada PIPEDA](https://laws-lois.justice.gc.ca/eng/acts/p-8.6/page-5.html) · [Chile Law 21.719](https://www.bcn.cl/leychile/Navegar?idNorma=1209272&idVersion=2026-12-01) · [Philippines NPC](https://privacy.gov.ph/wp-content/uploads/2022/08/NPC-CIRCULAR-NO.-2022-01-GUIDELINES-ON-ADMINISTRATIVE-FINES-dated-08-AUGUST-2022-w-SGD.pdf)
- Law-firm updates: [Al Tamimi, Egypt](https://www.tamimi.com/law_update_articles/from-policy-to-practice-egypt-issues-executive-regulations-of-the-personal-data-protection-law/) · [Ridza Law, Malaysia](https://www.ridzalaw.com.my/post/malaysia-s-personal-data-protection-amendment-act-2024) · [AHP, Indonesia](https://www.ahp.id/clientalert/AHPClientUpdate-1October2026.pdf) · [K&L Gates, Taiwan](https://www.klgates.com/thought-leadership/New-Developments-in-the-Taiwan-Personal-Data-Protection-Act-1-13-2026) · [DataGuidance, Bangladesh](https://www.dataguidance.com/jurisdictions/bangladesh) · [euconsent, GDPR ages](https://euconsent.eu/digital-age-of-consent-under-the-gdpr/)
- Cells marked "unverified" could not be confirmed from an opened source; check with local counsel.
