# Design / Brand pass v8.4.39

## Implemented
- Brand logo supplied by the user is integrated into web and mobile assets.
- The brand name is explicitly rendered as `Мир Самозанятых` next to/below the logo where appropriate.
- Light theme uses warm white + orange/gold brand colors.
- Dark theme is variant #2: deep navy/charcoal surfaces with orange/gold accents.
- React web layout has a persistent theme toggle with localStorage persistence.
- React Home and Downloads pages use the new brand system.
- React SvetlanaAvatar now uses the recovered real Svetlana model asset instead of the placeholder `С` glyph.
- Legacy Svetlana page now displays the same recovered Svetlana asset.
- Flutter light/dark theme palette was aligned with the web brand system; dark theme is variant #2.
- Flutter Home now uses the brand header and a real Svetlana card.
- Download status endpoint reports Android/iOS availability without pretending binaries exist.

## Svetlana asset provenance
The uploaded `svetlana-avatar-v13.0-1.zip` is truncated and has no central ZIP directory, so standard extraction fails. Its intact local ZIP entries were recovered directly from the archive stream. The recovered `qa/Base.png` and face crop are used as the Svetlana visual asset.

## Runtime status
- Python syntax check: passed for changed backend files.
- Jinja template rendering check: passed for changed legacy templates.
- TypeScript transpilation/syntax check: passed for changed React files.
- Full React build: NOT verified because npm dependency installation timed out in the available environment.
- Flutter build: NOT verified because Flutter SDK is not installed in the available environment.
- Android APK: NOT claimed as built or published; the project currently exposes a truthful unavailable state until a real APK is placed under `downloads/`.
