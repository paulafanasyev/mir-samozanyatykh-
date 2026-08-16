#!/bin/bash
set -e

echo "🚀 Building Мир Самозанятых Flutter APK..."
cd "$(dirname "$0")"

# Get Flutter
if ! command -v flutter &> /dev/null; then
    echo "Installing Flutter..."
    git clone https://github.com/flutter/flutter.git -b stable --depth 1
    export PATH="$PATH:$(pwd)/flutter/bin"
fi

flutter doctor
flutter pub get

# Build APK
echo "Building release APK..."
flutter build apk --release

echo "✅ APK built: build/app/outputs/flutter-apk/app-release.apk"

# Build iOS (requires macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Building iOS..."
    flutter build ios --release --no-codesign
    echo "✅ iOS built: build/ios/iphoneos/Runner.app"
fi
