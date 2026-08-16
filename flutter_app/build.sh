#!/bin/bash
set -e

echo "=== Building МИР Самозанятых APK ==="
cd "$(dirname "$0")"

flutter clean
flutter pub get
flutter build apk --release

echo "=== APK built successfully ==="
echo "Location: build/app/outputs/flutter-apk/app-release.apk"
