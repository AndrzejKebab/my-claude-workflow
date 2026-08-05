---
name: Unity Object null check
description: UnityEngine.Object can be destroyed but not C# null — use implicit bool operator (if (obj)) not == null
type: feedback
---

UnityEngine.Object can be "missing" (destroyed native side) while the C# reference is non-null. Always use the implicit boolean operator `if (obj)` instead of `if (obj != null)` to detect both null and destroyed objects.

**Why:** After disable/enable cycles, RenderTextures and other Unity objects get destroyed but their C# wrappers remain non-null, causing "Property not set" errors when passed to GPU APIs.

**How to apply:** Any time you guard on a UnityEngine.Object (textures, materials, GameObjects, etc.) being valid, use `if (obj)` or `if (!obj)`, not null checks.
