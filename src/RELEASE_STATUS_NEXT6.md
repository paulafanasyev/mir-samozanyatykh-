# Release status — NEXT6

Date: 2026-08-17

## Confirmed locally

- Svetlana v13 source archive CRC/integrity: PASS.
- Web/mobile `model_base.glb`: byte-identical.
- Web/mobile Svetlana `app.js`: byte-identical.
- External Three.js CDN references: absent.
- Security hardening checks: PASS.
- JavaScript syntax checks: PASS.
- Python compilation: PASS.
- ZIP integrity: PASS.
- Vendor target path bug in `scripts/vendor_svetlana_three.mjs`: fixed.

## Intentionally not claimed as complete

- Real Three.js 0.179.1 vendor bytes are not present in this local environment.
- Local offline verifier therefore remains FAIL on the eight vendor-file checks.
- Web production build has not been executed locally because dependencies are not installed.
- Flutter analyze/test/APK/iOS builds have not been executed locally because Flutter/Xcode are unavailable.

## CI release path

GitHub Actions now installs the pinned `three@0.179.1`, vendors the exact four required files, runs the integrated verifier, and only then builds Web/Android/iOS artifacts.

Flutter stable 3.44 is used for the mobile build lane. Flutter's official release documentation lists 3.44 as a stable release. Three.js r179 is retained deliberately for compatibility with the validated Svetlana runtime.
