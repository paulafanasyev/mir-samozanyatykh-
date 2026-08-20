#!/usr/bin/env bash
set -euo pipefail

# Appcircle Android CI entrypoint for Мир Самозанятых.
# Project root: src/mobile
# Release variant: prod

PROJECT_DIR="${AC_FLUTTER_PROJECT_DIR:-src/mobile}"
cd "$PROJECT_DIR"

flutter --version
flutter pub get

# Build the production APK. Signing is supplied by Appcircle when configured;
# without signing variables the Android project falls back to the debug key.
flutter build apk --release --flavor prod

# Appcircle can collect artifacts from this directory.
mkdir -p "${AC_OUTPUT_DIR:-build/app/outputs/flutter-apk}"

printf '\n=== Android artifacts ===\n'
find build/app/outputs/flutter-apk -maxdepth 1 -type f -name '*.apk' -print
