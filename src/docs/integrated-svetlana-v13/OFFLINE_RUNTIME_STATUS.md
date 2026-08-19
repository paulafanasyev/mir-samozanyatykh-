# Светлана v13 — offline runtime status

## Architecture change

The avatar runtime no longer references a CDN. `app.js` now imports:

- `./vendor/three/0.179.1/three.module.js`
- `./vendor/three/0.179.1/examples/jsm/loaders/GLTFLoader.js`

The same vendor tree is required for Web and Flutter assets. The ESM dependency graph requires `three.module.js`, `three.core.js`, `examples/jsm/loaders/GLTFLoader.js`, and `examples/jsm/utils/BufferGeometryUtils.js`; the browser import map maps the bare `three` specifier to the local module.

## Build procedure

From `ms/src/frontend` after installing dependencies:

```bash
npm install
npm run vendor:svetlana
npm run build
```

The vendor script copies the pinned Three.js 0.179.1 runtime from `node_modules/three` into both Web and Mobile Svetlana asset trees.

## Current verification limitation

The current execution environment has no Flutter/Dart SDK and no external DNS/network access, so the actual npm download and Flutter build cannot be honestly claimed as completed here. The source now has a deterministic local-vendor path and a reproducible command for completing it in a connected build environment.

Three.js 0.179.1 is an existing published version; the current npm latest is newer, but this project intentionally pins 0.179.1 to preserve the tested Svetlana runtime. citeturn0search8

The mobile WebView dependency is pinned to `webview_flutter 4.14.1`; this version requires Dart 3.10 and supports Android/iOS through the platform WebView. citeturn0search1turn0search2

## Upstream lock

The vendor process is pinned to Three.js `0.179.1` / upstream ref `r179`. The verifier records the upstream Git blob SHAs in `THREE_VENDOR_LOCK.json`. Three.js documentation confirms that GLTFLoader is an addon imported explicitly, and the migration guide documents the r178→r179 changes. citeturn0search4turn0search0


## CI release path (added in NEXT5)

The repository now contains `.github/workflows/build-release.yml`, which performs the missing connected-environment steps: install the pinned frontend dependency, vendor the exact Three.js 0.179.1 runtime into both Web and Flutter assets, run the Svetlana verifier, build the Web bundle, run Flutter analyze/tests, build a release APK, and produce an unsigned iOS release app.

The older Android workflow was also corrected to use Flutter 3.44.7 and to vendor Svetlana before building. `webview_flutter 4.14.1` requires Dart 3.10 and the package documentation identifies Android SDK 24+ / iOS 13+ support; the previous Flutter 3.24.5 workflow was therefore incompatible with the pinned WebView dependency. citeturn0search0turn0search1

Current local environment status remains `OFFLINE READY = NOT VERIFIED`: the real vendor bytes are not present locally, so no local production build is claimed. The CI workflow is the reproducible path that can obtain the pinned package in a connected runner and then prove the build.
