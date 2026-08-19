# Светлана v13 — integration verification

## Factually verified

- The supplied `model_base.glb` from `svetlana-avatar-v13.0.zip` is a complete GLB file: header length equals actual file length (43,580,292 bytes).
- SHA-256 of the source model and both integrated copies is identical:
  `9a65654d5de83f73201f9577b3fb44478d7ef6d0412b81c2467724a4de1151f5`
- The GLB JSON chunk parses successfully and contains 1 mesh, 2 nodes, 1 material and 11 morph targets.
- The native morph target names are: `blink_L`, `blink_R`, `browUp_L`, `browUp_R`, `jawOpen`, `mouthOpen`, `mouthSmile_L`, `mouthSmile_R`, `mouthPucker`, `mouthFunnel`, `mouthClose`.
- The model is present in both Web and Flutter asset trees.
- The real TTS smoke-test WAV is present in both Web and Flutter asset trees.
- Svetlana's Web route and authenticated backend chat/history endpoints are present.
- Python application sources compile successfully with `python -m compileall`.
- Svetlana runtime JavaScript files pass `node --check`.
- The integrated ZIP passes `unzip -t`.

## Not claimed as runtime-verified

- React/Vite production build: dependencies are not installed in this isolated environment and external package download is unavailable.
- Flutter Android/iOS build: Flutter SDK is not installed in this environment.
- Real device WebGL/TTS performance and microphone/camera behavior.
- Live AI provider connectivity.

## Important implementation note

The avatar runtime imports Three.js and GLTFLoader from jsDelivr. Therefore the current avatar runtime requires network access to load those modules. The GLB itself is bundled locally. A fully offline mobile avatar would require vendoring the Three.js runtime into the app assets.


## Verification pass — 2026-08-17

- Replaced the previously truncated nested `svetlana-avatar-v13.0-1.zip` with the exact user-supplied `svetlana-avatar-v13.0.zip` source archive. The source archive now passes ZIP CRC/integrity testing.
- Web and mobile `index.html` are now byte-identical, so the two clients use the same bridge contract.
- Web and mobile `app.js` are byte-identical.
- Web and mobile `model_base.glb` SHA-256 values are identical: `9a65654d5de83f73201f9577b3fb44478d7ef6d0412b81c2467724a4de1151f5`.
- Added a deterministic verification script at `scripts/verify_svetlana.py`. It checks required assets, archive integrity, Web/Mobile parity, JavaScript syntax, and Python compilation. Current result: **PASS**.
- Added a `svetlana.ready` postMessage carrying the health snapshot after successful avatar load, plus a `svetlana.error` message on load failure. This gives the Flutter host a concrete runtime signal instead of assuming success.
- The avatar still loads Three.js 0.179.1 and GLTFLoader from jsDelivr. This remains an explicitly known network dependency; it has **not** been falsely marked as offline-ready. The official npm registry lists Three.js 0.179.1 as a published version, and GLTFLoader is part of the `three` package rather than a separate dependency.
- Full React/Vite build, Flutter Android/iOS build, and physical-device runtime remain unverified in this environment because the required dependency trees/SDKs are not installed here.
