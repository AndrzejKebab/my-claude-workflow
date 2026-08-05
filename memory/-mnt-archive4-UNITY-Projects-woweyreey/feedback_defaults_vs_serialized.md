---
name: Script defaults don't override serialized asset values
description: When tuning numeric constants that live on a ScriptableObject/MonoBehaviour, the serialized .asset wins over C# defaults — changing Default => ... accomplishes nothing for existing scenes
type: feedback
originSessionId: 4885a0d9-5b1a-487c-9cd5-d7ee5b4bda74
---
Never "fix" a runtime value by editing the `Default` initializer in a C# struct/class when that value is serialized on a ScriptableObject, render feature, component, or other .asset/.prefab. Unity deserializes the asset and **overrides** any C# default, so the edit has zero runtime effect while looking like progress.

**Why:** Burned on volumetric clouds perf pass 2026-04-14 — changed `CloudSettings.Default.cloudHorizonMaxDistance = 45000 → 8000` twice and both bench runs showed zero movement because the VolumetricCloudsFeature .asset already had `45000` baked in. Also computed geometry using `planetRadius = 35000` (the C# default) when the asset had `6378100`, so the entire analysis of marchLen was off by orders of magnitude.

**How to apply:**
- Before tuning a numeric field to test a hypothesis, check what the **serialized** value is on the asset (inspector screenshot, `grep` the .asset YAML, or ask the user).
- To actually change a serialized value, either (a) ask the user to edit the asset in the inspector, or (b) change shader/code logic so the tuning lives in code, not in a field. Prefer (b) for perf experiments — iterate without asset churn.
- When the math depends on field values (planet radius, cloud heights, etc.), base it on the serialized numbers the user confirms, not on `Default` initializers.
- This also means: don't assume `Default` reflects what's running. It's a fresh-instance fallback, often stale.
