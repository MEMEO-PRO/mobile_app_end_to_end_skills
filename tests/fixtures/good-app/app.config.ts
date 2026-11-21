export default {
  name: "Good Budget", slug: "good-budget", version: "1.0.0",
  runtimeVersion: { policy: "fingerprint" },
  updates: { codeSigningCertificate: "./certs/certificate.pem", codeSigningMetadata: { keyid: "main", alg: "rsa-v1_5-sha256" } },
  ios: {
    bundleIdentifier: "in.memeo.goodbudget",
    config: { usesNonExemptEncryption: false },
    infoPlist: { NSCameraUsageDescription: "Scan receipts to add expenses" },
    privacyManifests: { NSPrivacyAccessedAPITypes: [{ NSPrivacyAccessedAPIType: "NSPrivacyAccessedAPICategoryUserDefaults", NSPrivacyAccessedAPITypeReasons: ["CA92.1"] }] },
  },
  android: { package: "in.memeo.goodbudget", permissions: ["CAMERA"], blockedPermissions: ["android.permission.READ_MEDIA_IMAGES"] },
  plugins: [["expo-build-properties", { android: { targetSdkVersion: 36, compileSdkVersion: 36 } }]],
};
