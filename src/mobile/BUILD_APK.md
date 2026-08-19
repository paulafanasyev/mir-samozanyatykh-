# Сборка APK — Мир Самозанятых

## Автоматическая сборка

В репозитории есть GitHub Actions workflow `Build Android APK`.
Он выполняет `flutter pub get`, `flutter analyze`, `flutter test` и release APK build.

**Важно:** наличие workflow не означает, что APK уже успешно собран. Успешным считается только workflow, завершившийся без ошибок и содержащий APK artifact.

## Локальная сборка

Требуется установленный Flutter SDK, Android SDK и JDK. Точную совместимость следует подтверждать командой `flutter doctor`.

После установки окружения:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --release --flavor prod
```

Ожидаемый artifact:

`mobile/build/app/outputs/flutter-apk/app-prod-release.apk`

Для публикации в Google Play нужен production signing key. Текущий проект допускает debug signing только как fallback для локального installable APK; это НЕ production Play signing.
