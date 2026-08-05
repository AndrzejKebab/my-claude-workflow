---
name: Slime movement E2E test is a verification gate
description: JsSlimeMovementE2ETests must always pass — it loads the real scene with subscenes and proves JS Component tick pipeline works end-to-end
type: feedback
---

Always run `JsSlimeMovementE2ETests` as part of verification.
**Why:** A large ISystem refactor appeared to pass all unit tests but broke the actual gameplay — slimes didn't move. This E2E test catches that class of regression by loading the real scene (Le3DScene), waiting for subscene streaming + fulfillment, and asserting that at least one entity's `LocalTransform.Position` changes.
**How to apply:** Include in the EditMode verification gate alongside other UnityJS tests. Uses `SceneSystem.LoadSceneAsync` with `BlockOnImport | BlockOnStreamIn` for batchmode.
