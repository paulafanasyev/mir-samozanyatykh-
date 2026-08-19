# Svetlana v4.0 visual QA

All images in this directory are renders of the supplied `model_base.glb` only. No external/reference character images are used.

The shaded QA renders are software renders of the actual GLB with its embedded texture and native morph target deltas. They are used for geometry/expression QA. They are **not** evidence that the browser WebGL runtime has been successfully exercised on an Android GPU.

Primary checks:
- Base
- Blink
- Smile
- Surprise
- A
- O
- U
- MBP
- Smile + speech

The key correction in v4.0 is that the runtime now uses the native GLB names exactly as authored: `blink_L`, `blink_R`, `browUp_L`, `browUp_R`, `jawOpen`, `mouthOpen`, `mouthSmile_L`, `mouthSmile_R`, `mouthPucker`, `mouthFunnel`, `mouthClose`.
