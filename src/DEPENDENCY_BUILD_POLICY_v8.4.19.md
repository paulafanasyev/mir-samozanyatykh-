# Dependency & Build Policy

## Frontend
`package-lock.json` is currently absent from the supplied project. Until it is committed, CI and the frontend Docker build use `npm install` rather than `npm ci`.

Before production release, generate and commit `frontend/package-lock.json` from a network-enabled clean environment. After that, CI/Docker will automatically switch to `npm ci`.

## Mobile
`mobile/pubspec.lock` is not committed because this is an application package, not a published Dart library. CI always runs `flutter pub get` and `flutter analyze`.

## Backend
Python runtime and development dependencies are pinned in `requirements.txt` and `requirements-dev.txt`. CI runs `pip-audit` and Bandit.
