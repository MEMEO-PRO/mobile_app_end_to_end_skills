#!/usr/bin/env bash
# app-factory preflight: scan a mobile app project (Expo / React Native / native Android / iOS)
# for common store-rejection and security problems before submission.
#
# Usage: bash preflight.sh [project-dir]
# Exit code: 0 = CLEAR (no blockers), 1 = BLOCKED, 2 = usage error.
# Static checks only. Store-console items (forms, agreements, listings) stay manual.

set -u
DIR="${1:-.}"
if [ ! -d "$DIR" ]; then echo "Not a directory: $DIR" >&2; exit 2; fi
cd "$DIR" || exit 2

MIN_TARGET_SDK="${MIN_TARGET_SDK:-36}"   # Google Play floor for new apps and updates from 31 Aug 2026
BLOCKERS=0; WARNINGS=0
EXCL=(--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=Pods --exclude-dir=build \
      --exclude-dir=.expo --exclude-dir=dist --exclude-dir=.gradle --exclude-dir=DerivedData \
      --exclude-dir=coverage --exclude-dir=.next)

if [ -t 1 ]; then R=$'\033[31m'; Y=$'\033[33m'; G=$'\033[32m'; B=$'\033[1m'; N=$'\033[0m'; else R=; Y=; G=; B=; N=; fi
block() { BLOCKERS=$((BLOCKERS+1)); printf '%sBLOCKER%s  %s\n' "$R" "$N" "$1"; [ -n "${2:-}" ] && printf '         fix: %s\n' "$2"; return 0; }
warn()  { WARNINGS=$((WARNINGS+1)); printf '%sWARNING%s  %s\n' "$Y" "$N" "$1"; [ -n "${2:-}" ] && printf '         fix: %s\n' "$2"; return 0; }
ok()    { printf '%sok%s       %s\n' "$G" "$N" "$1"; }
# search: files matching extended regex (case-sensitive), limited to source/config files
search() { grep -rIlE "${EXCL[@]}" --include='*.js' --include='*.jsx' --include='*.ts' --include='*.tsx' \
  --include='*.json' --include='*.xml' --include='*.plist' --include='*.gradle' --include='*.kts' \
  --include='*.kt' --include='*.java' --include='*.swift' --include='*.m' --include='*.dart' \
  --include='*.env' --include='.env*' --include='*.yaml' --include='*.yml' --include='*.xcprivacy' \
  -e "$1" . 2>/dev/null | grep -v -E 'package-lock\.json|yarn\.lock|pnpm-lock' ; }
searchi() { grep -rIliE "${EXCL[@]}" --include='*.js' --include='*.jsx' --include='*.ts' --include='*.tsx' \
  --include='*.json' --include='*.xml' --include='*.kt' --include='*.java' --include='*.swift' --include='*.dart' \
  -e "$1" . 2>/dev/null | grep -v -E 'package-lock\.json|yarn\.lock|pnpm-lock' ; }
first() { head -n 3 | tr '\n' ' '; }

CONFIGS=$(ls app.json app.config.js app.config.ts 2>/dev/null | tr '\n' ' ')
MANIFESTS=$(find . -name AndroidManifest.xml -not -path '*/node_modules/*' -not -path '*/build/*' 2>/dev/null)
PLISTS=$(find . -name Info.plist -not -path '*/node_modules/*' -not -path '*/Pods/*' -not -path '*/build/*' 2>/dev/null)
PKG=$( [ -f package.json ] && cat package.json || true )

printf '%sapp-factory preflight%s — %s\n\n' "$B" "$N" "$(pwd)"

# ---------- 1. Project identity ----------
printf '%s[1] Project identity%s\n' "$B" "$N"
if [ -z "$CONFIGS" ] && [ -z "$MANIFESTS" ] && [ -z "$PLISTS" ]; then
  block "No app.json / app.config.* / AndroidManifest.xml / Info.plist found — is this a mobile app project?"
else
  ok "config found: ${CONFIGS}$(echo "$MANIFESTS $PLISTS" | wc -w | tr -d ' ') native file(s)"
fi
if [ -n "$CONFIGS" ]; then
  grep -qE '"?package"?[[:space:]]*:' $CONFIGS || warn "No android.package in app config" "Set android.package (reverse-DNS, permanent once published)."
  grep -qE '"?bundleIdentifier"?[[:space:]]*:' $CONFIGS || warn "No ios.bundleIdentifier in app config" "Set ios.bundleIdentifier."
  grep -qE 'com\.example\.|com\.yourcompany' $CONFIGS && block "Placeholder package / bundle id (com.example...) in app config" "Use your own reverse-DNS id; the stores reject com.example."
fi

# ---------- 2. Secrets ----------
printf '\n%s[2] Secrets in the app%s\n' "$B" "$N"
SECRETS=$(search 'sk_live_[0-9A-Za-z]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|xox[bpas]-[0-9A-Za-z-]{10,}|ghp_[0-9A-Za-z]{30,}|sk-(proj-|ant-)?[0-9A-Za-z_-]{20,}|service_role')
if [ -n "$SECRETS" ]; then block "Possible secret keys in source: $(echo "$SECRETS" | first)" "Move secrets to your server; the JS bundle and APK can be decompiled. Rotate any key that was committed."
else ok "no known secret-key patterns"; fi
PUBSECRET=$(search 'EXPO_PUBLIC_[A-Z0-9_]*(SECRET|PRIVATE|SERVICE_ROLE|PASSWORD)')
[ -n "$PUBSECRET" ] && block "Secret-looking EXPO_PUBLIC_* variable: $(echo "$PUBSECRET" | first)" "EXPO_PUBLIC_* values are embedded in the bundle. Keep secrets server-side."
ASYNC_TOKEN=$(grep -rIlE "${EXCL[@]}" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' 'AsyncStorage\.setItem\([^)]*([Tt]oken|[Pp]assword|[Ss]ecret)' . 2>/dev/null)
[ -n "$ASYNC_TOKEN" ] && warn "Tokens stored in AsyncStorage (plain text): $(echo "$ASYNC_TOKEN" | first)" "Use expo-secure-store (Keychain / Keystore)."

# ---------- 3. Network & build hardening ----------
printf '\n%s[3] Network and build hardening%s\n' "$B" "$N"
CLEAR=$(search 'usesCleartextTraffic="true"|cleartextTrafficPermitted="true"|usesCleartextTraffic"?[[:space:]]*:[[:space:]]*true')
[ -n "$CLEAR" ] && block "Cleartext HTTP allowed: $(echo "$CLEAR" | first)" "HTTPS only (MASVS-NETWORK). Remove usesCleartextTraffic / cleartextTrafficPermitted."
ATS=$(search 'NSAllowsArbitraryLoads')
if [ -n "$ATS" ] && grep -A1 -h 'NSAllowsArbitraryLoads' $ATS | grep -qiE '<true/>|: *true'; then
  block "iOS App Transport Security disabled (NSAllowsArbitraryLoads = true): $(echo "$ATS" | first)" "Remove it, or use a narrow NSExceptionDomains entry with a justification for review."
fi
DEBUG=$(search 'android:debuggable="true"')
[ -n "$DEBUG" ] && block "android:debuggable=\"true\" in a manifest: $(echo "$DEBUG" | first)" "Never ship debuggable builds."
HTTP=$(grep -rIhoE "${EXCL[@]}" --include='*.ts' --include='*.tsx' --include='*.js' --include='*.jsx' --include='*.dart' --include='*.kt' --include='*.swift' "['\"]http://[a-zA-Z0-9.-]+" . 2>/dev/null | grep -vE 'localhost|127\.0\.0\.1|10\.0\.2\.2|schemas\.android|www\.w3\.org|apple\.com/DTDs' | sort -u | head -3 | tr '\n' ' ')
[ -n "$HTTP" ] && warn "Plain http:// URLs in code: $HTTP" "Switch to https://."
[ -z "$CLEAR$ATS$DEBUG" ] && ok "no cleartext / ATS / debuggable flags"

# ---------- 4. Target SDK ----------
printf '\n%s[4] Android target SDK (Play floor: %s)%s\n' "$B" "$MIN_TARGET_SDK" "$N"
TSDK=$(grep -rhoE "${EXCL[@]}" --include='*.json' --include='*.js' --include='*.ts' --include='*.gradle' --include='*.kts' --include='*.properties' \
  'targetSdk(Version)?["]?[[:space:]]*[:=]?[[:space:]]*[0-9]{2}' . 2>/dev/null | grep -oE '[0-9]{2}$' | sort -n | head -1)
if [ -z "$TSDK" ]; then
  if echo "$PKG" | grep -q '"expo"'; then warn "targetSdkVersion not set explicitly" "Expo SDK 58 defaults to a current target; pin it with expo-build-properties (targetSdkVersion: $MIN_TARGET_SDK) so upgrades can't regress it."
  elif [ -n "$MANIFESTS" ]; then warn "Could not find targetSdkVersion" "Check build.gradle: targetSdk must be >= $MIN_TARGET_SDK."; fi
elif [ "$TSDK" -lt "$MIN_TARGET_SDK" ]; then block "targetSdkVersion $TSDK is below $MIN_TARGET_SDK" "Raise targetSdkVersion/compileSdkVersion to $MIN_TARGET_SDK (Play rejects new apps and updates below it)."
else ok "targetSdkVersion $TSDK"; fi

# ---------- 5. Permissions ----------
printf '\n%s[5] Permissions%s\n' "$B" "$N"
SENSITIVE='READ_SMS|RECEIVE_SMS|SEND_SMS|READ_CALL_LOG|WRITE_CALL_LOG|PROCESS_OUTGOING_CALLS|MANAGE_EXTERNAL_STORAGE|ACCESS_BACKGROUND_LOCATION|BIND_ACCESSIBILITY_SERVICE|QUERY_ALL_PACKAGES|REQUEST_INSTALL_PACKAGES|SCHEDULE_EXACT_ALARM|USE_FULL_SCREEN_INTENT|READ_MEDIA_IMAGES|READ_MEDIA_VIDEO|READ_CONTACTS|SYSTEM_ALERT_WINDOW'
FOUND=$( { [ -n "$CONFIGS" ] && grep -hoE "$SENSITIVE" $CONFIGS; for m in $MANIFESTS; do grep -hoE "uses-permission[^>]*($SENSITIVE)" "$m" | grep -oE "$SENSITIVE"; done; } 2>/dev/null | sort -u | tr '\n' ' ')
BLOCKED_LIST=$( [ -n "$CONFIGS" ] && grep -hoE 'blockedPermissions[^]]*' $CONFIGS 2>/dev/null )
REAL=""
for p in $FOUND; do echo "$BLOCKED_LIST" | grep -q "$p" || REAL="$REAL $p"; done
if [ -n "$REAL" ]; then warn "Sensitive Android permissions need a Play declaration + core-use justification:$REAL" "Remove them (blockedPermissions / Photo Picker / Contact Picker) unless they are the app's core function; otherwise file the declaration with a demo video."
else ok "no sensitive Android permissions"; fi
FGS=$(for m in $MANIFESTS; do grep -l 'FOREGROUND_SERVICE' "$m"; done 2>/dev/null)
[ -n "$FGS" ] && warn "Foreground service declared: $(echo "$FGS" | first)" "Declare each foreground-service type in Play Console with a video."
# iOS usage strings
USAGE=$( { [ -n "$CONFIGS" ] && cat $CONFIGS; for p in $PLISTS; do cat "$p"; done; } 2>/dev/null | grep -oE 'NS[A-Za-z]+UsageDescription"?[^,<]*(<string>[^<]*)?' )
if [ -n "$USAGE" ]; then
  BAD=$(echo "$USAGE" | grep -iE ':[[:space:]]*["'"'"'][[:space:]]*["'"'"']|<string>[[:space:]]*$|\$\(PRODUCT_NAME\) (needs|requires|would like)|(needs|requires) (access|permission)[[:space:]]*["'"'"'<]|TODO|lorem|Allow \$\(PRODUCT_NAME\)' | head -3)
  [ -n "$BAD" ] && block "Empty or generic iOS permission usage strings" "Each NS*UsageDescription must name the real feature (e.g. \"Scan receipts to add expenses\")."
  [ -z "$BAD" ] && ok "iOS usage strings present"
fi

# ---------- 6. Privacy declarations ----------
printf '\n%s[6] Privacy declarations%s\n' "$B" "$N"
if [ -n "$CONFIGS$PLISTS" ]; then
  if ! search 'privacyManifests|NSPrivacyAccessedAPITypes' >/dev/null || [ -z "$(search 'privacyManifests|NSPrivacyAccessedAPITypes')" ]; then
    [ -z "$(find . -name 'PrivacyInfo.xcprivacy' -not -path '*/node_modules/*' -not -path '*/Pods/*' 2>/dev/null)" ] && \
      warn "No iOS privacy manifest (ios.privacyManifests or PrivacyInfo.xcprivacy)" "Declare required-reason APIs; Apple rejects uploads that use them undeclared."
  else ok "iOS privacy manifest declared"; fi
  if [ -n "$CONFIGS" ] && ! grep -q 'usesNonExemptEncryption' $CONFIGS && [ -z "$(search 'ITSAppUsesNonExemptEncryption')" ]; then
    warn "Export compliance not declared (usesNonExemptEncryption)" "Set ios.config.usesNonExemptEncryption (false if only HTTPS/OS crypto) to skip the question on every upload."
  fi
fi
DOCS_INV=$(ls docs/data-inventory.md docs/data_inventory.md 2>/dev/null)
[ -z "$DOCS_INV" ] && warn "No docs/data-inventory.md" "Create it from templates/data-inventory.md; every privacy form is built from it."
PRIV=$(searchi 'privacy[ -]?policy|privacyPolicyUrl|/privacy')
[ -z "$PRIV" ] && block "No privacy policy link found in the app" "Both stores require a privacy policy URL in the listing and reachable inside the app."

# ---------- 7. Accounts ----------
printf '\n%s[7] Accounts%s\n' "$B" "$N"
AUTH=$(echo "$PKG" | grep -oE '"(@supabase/supabase-js|firebase|@react-native-firebase/auth|expo-auth-session|@clerk/clerk-expo|@auth0/[a-z-]+|aws-amplify|@aws-amplify/[a-z-]+|react-native-app-auth)"' | head -1)
[ -z "$AUTH" ] && AUTH=$(searchi 'signUp|createUserWithEmailAndPassword|registerUser|sign_up' | head -1)
if [ -n "$AUTH" ]; then
  DEL=$(searchi 'delete[ _-]?(my[ _-]?)?account|deleteAccount|deleteUser|account[ _-]?deletion|close[ _-]?account')
  if [ -z "$DEL" ]; then block "Accounts can be created ($AUTH) but no in-app account deletion was found" "Add Settings → Delete account (Apple 5.1.1(v)) and a public deletion web page (Play)."
  else ok "account creation + deletion path found"; fi
  echo "$PKG" | grep -qE '"(expo-apple-authentication|@invertase/react-native-apple-authentication)"' || \
    { echo "$PKG" | grep -qE 'google-signin|expo-auth-session|facebook' && warn "Third-party login without Sign in with Apple" "Apple 4.8: offer an equivalent privacy-focused login option (e.g. Sign in with Apple) alongside Google/Facebook login."; }
else ok "no account system detected"; fi

# ---------- 8. Payments ----------
printf '\n%s[8] Payments%s\n' "$B" "$N"
IAP=$(echo "$PKG" | grep -oE '"(react-native-purchases|react-native-iap|expo-in-app-purchases|expo-iap)"' | head -1)
STRIPE=$(echo "$PKG" | grep -oE '"(@stripe/stripe-react-native|react-native-razorpay|react-native-paypal[a-z-]*)"' | head -1)
if [ -n "$IAP" ]; then
  RESTORE=$(searchi 'restorePurchases|restoreTransactions|getAvailablePurchases|restore[ _-]?purchase')
  [ -z "$RESTORE" ] && block "In-app purchases ($IAP) without a Restore Purchases action" "Add a visible Restore Purchases button (Apple 3.1.1)."
  TERMS=$(searchi 'terms[ -]?of[ -]?(use|service)|EULA|/terms')
  [ -z "$TERMS" ] && warn "No terms / EULA link found near purchases" "Subscriptions need price, period, renewal terms and a functional Terms link on the paywall (Apple 3.1.2)."
  [ -n "$RESTORE" ] && ok "IAP with restore"
fi
[ -n "$STRIPE" ] && warn "External payment SDK ($STRIPE)" "Allowed for physical goods and services. Digital goods and subscriptions must use store billing except where a regional exception applies (see compliance.md)."
[ -z "$IAP$STRIPE" ] && ok "no payment SDKs"

# ---------- 9. AI, tracking, UGC ----------
printf '\n%s[9] AI, tracking, user content%s\n' "$B" "$N"
AI=$(echo "$PKG" | grep -oE '"(openai|@anthropic-ai/sdk|@google/generative-ai|@google/genai|@mistralai/mistralai|groq-sdk|cohere-ai|replicate|ai|@ai-sdk/[a-z-]+)"' | head -3 | tr '\n' ' ')
if [ -n "$AI" ]; then
  CONSENT=$(searchi 'ai[ _-]?consent|aiConsent|share.{0,40}with.{0,40}(openai|ai provider|gemini|mistral)|AI disclosure')
  [ -z "$CONSENT" ] && warn "AI SDK in the app ($AI) but no AI consent screen found" "Before sending personal data to an AI provider, name it and the data types and ask (Apple 5.1.2(i)); mark AI-generated content (EU AI Act Art. 50). Better: call the AI from your server."
fi
ADS=$(echo "$PKG" | grep -oE '"(react-native-google-mobile-ads|react-native-fbsdk-next|react-native-appsflyer|@adjust/react-native-sdk|react-native-branch|expo-ads-admob|@amplitude/analytics-react-native|mixpanel-react-native)"' | head -3 | tr '\n' ' ')
if [ -n "$ADS" ]; then
  echo "$PKG" | grep -q 'expo-tracking-transparency' || [ -n "$(search 'NSUserTrackingUsageDescription')" ] || \
    warn "Ads / attribution SDKs ($ADS) without App Tracking Transparency" "Add expo-tracking-transparency and ask before tracking; declare tracking domains in the privacy manifest and Data safety form."
fi
UGC=$(searchi 'createPost|uploadPost|sendMessage|addComment|postComment|chatMessage' | head -1)
if [ -n "$UGC" ]; then
  MOD=$(searchi 'report(User|Post|Content|Abuse)|blockUser|block[ _-]user|flagContent')
  [ -z "$MOD" ] && warn "User-generated content found but no report / block feature" "Apple 1.2 and Play UGC policy require filtering, reporting, blocking and a published contact."
fi
[ -z "$AI$ADS$UGC" ] && ok "no AI, ads/attribution or UGC features detected"

# ---------- 10. Expo / OTA ----------
if echo "$PKG" | grep -q '"expo-updates"'; then
  printf '\n%s[10] Over-the-air updates%s\n' "$B" "$N"
  [ -n "$CONFIGS" ] && ! grep -q 'codeSigningCertificate' $CONFIGS && warn "EAS Update without code signing" "Set updates.codeSigningCertificate + codeSigningMetadata so only bundles signed with your key run."
  [ -n "$CONFIGS" ] && ! grep -qE 'fingerprint|appVersion|runtimeVersion' $CONFIGS && warn "No runtimeVersion policy" "Use runtimeVersion: { policy: \"fingerprint\" } so updates only reach compatible binaries."
  ok "OTA rule: JS/content fixes only; native, permission, payment or purpose changes need a store build"
fi

# ---------- Summary ----------
printf '\n%s%d blocker(s), %d warning(s)%s\n' "$B" "$BLOCKERS" "$WARNINGS" "$N"
echo "Still manual: store-console forms (Data safety, privacy labels, content rating, declarations), developer accounts and agreements, listing text and screenshots, demo account, launch-country legal steps."
if [ "$BLOCKERS" -gt 0 ]; then printf '%sBLOCKED.%s\n' "$R" "$N"; exit 1; fi
printf '%sCLEAR.%s\n' "$G" "$N"; exit 0
