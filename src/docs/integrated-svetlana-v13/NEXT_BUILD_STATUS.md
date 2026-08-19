# Next build status — local Three.js runtime

## Completed in source

- CDN imports removed from both Svetlana runtimes.
- Both Web and Flutter now reference the same pinned local runtime path.
- `three` is pinned to `0.179.1` in the frontend package manifest.
- `vendor_svetlana_three.mjs` reproducibly copies the pinned runtime from `node_modules/three` into both application asset trees.
- Flutter `webview_flutter` updated to `4.14.1` and Dart minimum raised to 3.10, matching the current package requirements. citeturn0search1turn0search2

## Verification result

The verifier intentionally FAILS at the moment because the actual Three.js vendor files are not present in this build environment. This is deliberate: claiming offline runtime readiness without the real library bytes would be false.

The blocker is environmental: the execution environment has no external DNS/network access, and it has no existing Three.js 0.179.1 installation to copy.

## Completion command in a connected build environment

```bash
cd ms/src/frontend
npm install
npm run vendor:svetlana
cd ..
python scripts/verify_svetlana.py
```

Only after that verifier returns `PASS` should the package be treated as offline-runtime ready.
