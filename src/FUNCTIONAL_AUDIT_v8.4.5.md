# Functional hardening v8.4.5

## Исправлено
- Removed broken legacy Flutter screen tree and duplicate API client.
- Main Flutter entrypoint now uses the active Riverpod + GoRouter architecture.
- Fixed all active Flutter relative imports.
- Removed dependency on generated Freezed/json_serializable files from UserModel/AuthState.
- Added `flutter_secure_storage` and moved mobile access/refresh credentials out of Hive.
- Fixed missing `apiBaseUrl` compatibility constant.
- Fixed mobile API client refresh flow and retry loop.
- Fixed notification list/read-all/read-one flow.
- Fixed referral code/stats to use backend APIs and clipboard.
- Fixed profile editing to load/save real user data.
- Raised mobile login/register minimum password length to 12.
- Removed mandatory Firebase initialization from application startup so the app can run without generated Firebase configuration.
- Fixed broken router imports.

## Verification performed
- Python compileall: PASS
- Mobile relative import audit: 0 missing
- No collapsed legacy Dart files remain under `mobile/lib`
- Legacy duplicate mobile tree removed
- Release artifacts will be cleaned before packaging

## Runtime gates
Flutter SDK/build, `flutter pub get`, Android Gradle build, backend integration tests, and frontend npm build require their external toolchains/dependencies and must be run in a network-enabled build environment.
