# Android / Mobile Recheck v8.4.39

## Реально проверено в текущем окружении

- Java 21 доступен.
- Flutter SDK не установлен.
- Dart SDK отдельно не установлен.
- Android SDK environment variable не обнаружен.
- Python backend `compileall`: PASS.
- Все Dart `package:` imports сопоставлены с `pubspec.yaml`: PASS.
- Все локальные Dart imports разрешаются в существующие файлы: PASS.
- Firebase Google Services Gradle plugin отсутствует: PASS.
- Ссылка на несуществующий Firebase MessagingService отсутствует: PASS.
- `assets/images/` существует и соответствует декларации pubspec: PASS.
- Android MainActivity существует: PASS.
- Android Manifest существует: PASS.
- POST_NOTIFICATIONS permission добавлен: PASS.
- Network security config подключён: PASS.
- Mobile version: 8.4.38+861.

## Исправлено в этом проходе

1. Добавлены отсутствовавшие зависимости `hive_flutter` и `table_calendar`.
2. Исправлены два неверных относительных импорта `ApiClient`.
3. Удалён оставшийся Google Services Gradle plugin, поскольку реальные Firebase credentials отсутствуют.
4. Удалены Firebase-specific ProGuard rules, не нужные без Firebase SDK.
5. Создан каталог `assets/images/`, объявленный в pubspec.
6. Добавлен отсутствовавший `core/utils/validators.dart` с email/phone/INN validation и formatters.
7. Исправлены Flutter widget tests: правильное имя package, правильный root widget, override auth state для deterministic tests.
8. Биометрический opt-in теперь хранится отдельным флагом, а не ошибочно определяется наличием user data.
9. Включена проверка биометрии перед её включением.
10. Добавлено разрешение Android 13+ на уведомления.
11. Подключён network security config.

## Что НЕ подтверждено

Поскольку Flutter/Android SDK отсутствуют, НЕ выполнены:

- `flutter pub get`
- `flutter analyze`
- `flutter test`
- `flutter build apk --release`
- `flutter build appbundle`
- установка APK на Android device/emulator
- Android runtime/E2E

Поэтому этот отчёт НЕ означает, что APK уже собран.
