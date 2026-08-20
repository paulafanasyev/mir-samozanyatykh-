# Appcircle CI — Android APK

This repository is prepared for a GitHub → Appcircle → Flutter Android release pipeline, so Android builds do not consume GitHub Actions minutes.

## Appcircle profile

Create one Android build profile and connect it to:

- Repository: `paulafanasyev/mir-samozanyatykh-next10`
- Branch: `main`
- Target platform: Android
- Target framework: Flutter
- Flutter project directory: `src/mobile`
- Build mode: Release
- Output: APK
- Flavor / variant: `prod`

The Flutter project is under `src/mobile`; its Android Gradle project defines the `prod` flavor. The production application id is `com.mirsamozanyatykh.mobile`.

## Recommended workflow

1. Git Clone
2. Flutter Install — select a stable Flutter version compatible with the repository (`3.44.x` is the current CI baseline)
3. Flutter Pub Get
4. Flutter Build for Android — Release / APK, project directory `src/mobile`, flavor `prod`
5. Artifact collection

Alternatively use the repository script:

```bash
bash ci/appcircle/build-android.sh
```

The script runs `flutter pub get` and `flutter build apk --release --flavor prod`.

## Signing

Do not commit a keystore or passwords. Add the release keystore through Appcircle Signing Identities / Android Keystores and configure the signing environment there. The Android project already supports `KEY_ALIAS`, `KEY_PASSWORD`, `KEYSTORE_PATH`, and `KEYSTORE_PASSWORD` environment variables.

## Important

The external CI only replaces the GitHub Actions runner. It does not hide or fix project compilation errors. The current Android project must still pass the Flutter/Gradle build before an APK is produced.

The current repository `pubspec.yaml` already uses `intl: ^0.20.2`, `form_builder_validators: ^11.1.2`, and `flutter_webrtc: ^1.6.0`, so the older dependency conflict and obsolete `flutter_webrtc` version seen in earlier CI logs are not expected from the current manifest.
