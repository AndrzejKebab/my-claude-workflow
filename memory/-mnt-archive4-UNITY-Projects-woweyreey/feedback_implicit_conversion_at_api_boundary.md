---
name: Pass float3/float4x4 directly to Unity APIs — no manual casts
description: Unity.Mathematics defines implicit operators between its types and UnityEngine.Vector*/Matrix4x4. When an API wants Vector3/Matrix4x4, pass the float* value directly — don't write `(Vector3)v` or `(Matrix4x4)m`.
type: feedback
originSessionId: 60fb3067-7f45-4e65-9083-e5b990f27c43
---
Unity.Mathematics defines implicit conversions in both directions:
- `float2 ↔ Vector2`
- `float3 ↔ Vector3`
- `float4 ↔ Vector4`
- `float4x4 ↔ Matrix4x4`
- `quaternion ↔ Quaternion`

**Rule:** When a Unity API takes a `Vector3` / `Matrix4x4` / etc., pass the `float3` / `float4x4` / etc. value directly. The implicit operator handles it.

Examples:
- `transform.position = myFloat3;` ✓
- `cmd.SetComputeMatrixParam(cs, id, myFloat4x4);` ✓
- `_material.SetMatrix(id, myFloat4x4);` ✓
- `Gizmos.DrawLine(floatA, floatB);` ✓ (DrawLine takes Vector3)
- `Quaternion.LookRotation(myFloat3, myFloat3);` ✓

**Exception — SetVector:** `Material.SetVector(int, Vector4)` / `MaterialPropertyBlock.SetVector` / `cmd.SetComputeVectorParam` / `cmd.SetGlobalVector` all take `Vector4`. `float4 → Vector4` is implicit, but `float3 → Vector4` requires two user-defined hops (`float3 → Vector3 → Vector4`), which C# forbids. Wrap manually:
- `SetVector(id, myFloat3)` — DOES NOT COMPILE.
- `SetVector(id, float4(myFloat3, 0f))` — ✓
- `SetVector(id, myFloat2)` — also doesn't compile; wrap as `float4(myFloat2.x, myFloat2.y, 0f, 0f)`.

**Why:** The implicit operators exist for exactly this case. Writing `(Vector3)myFloat3` adds noise and suggests the author didn't know about them. The chain limit on `float3 → Vector4` is the one sharp edge that bites — memorise it.

**How to apply:** When wiring a float* value into a Unity API, try passing it raw first. If the compiler complains, it's almost always the SetVector/Vector4-target case — wrap in `float4(...)` with explicit 0 padding.
