# Android Build Readiness v8.4.38

- Android app version: 8.4.38+861
- Backend version: 8.4.38
- Gradle wrapper: 8.7
- Android Gradle Plugin: 8.5.0
- Kotlin: 1.9.22
- Java target: 17
- Release signing: configured keystore when CI secrets exist; debug signing fallback otherwise
- Firebase: not initialized without real project credentials; no fake credentials are shipped
- Native Firebase service declaration removed because the referenced class did not exist
- GitHub Actions workflow added for Flutter analyze/test/release APK build

## Runtime limitation

This environment does not contain the Flutter SDK, so an APK build was not claimed as locally executed. The workflow above is the executable build path for a Flutter-capable CI runner.
