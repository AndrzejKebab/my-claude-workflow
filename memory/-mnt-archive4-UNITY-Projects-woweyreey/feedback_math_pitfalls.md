---
name: Unity.Mathematics pitfalls
description: Gotchas when replacing Mathf.*/Vector* with Unity.Mathematics — operator overloads differ, some Mathf helpers have no math equivalent, implicit conversion chains are limited.
type: feedback
originSessionId: 60fb3067-7f45-4e65-9083-e5b990f27c43
---
Gotchas hit during the atmospherics + heightfields modernisation pass:

1. **`float4x4 * float4x4` is component-wise, NOT matrix multiplication.** Unity.Mathematics overloads `*` elementwise on every `float*x*` type. Matrix-multiply requires `math.mul(a, b)`. Unity's `Matrix4x4 * Matrix4x4` DOES multiply, so expressions that mix types via implicit conversion can silently do the wrong thing. **Rule:** whenever both operands are `float4x4`, write `mul(a, b)` explicitly.

2. **`math.log` is natural log.** `Mathf.Log(x, b)` has no one-arg equivalent — use `log(x) / log(b)`. For `log(x, 2f)` use `log2(x)` instead. Similarly `log10(x)` exists.

3. **`saturate` replaces `Mathf.Clamp01`** — it's scalar and vector-overloaded uniformly, which is nicer than Clamp01.

4. **`Mathf.Approximately` has no math equivalent.** Use a project-local helper (e.g. `AtmosphericsMath.Approximately(a, b, eps)`) that does `abs(a - b) <= eps`. Same for `Mathf.LerpAngle` / `Mathf.DeltaAngle` — write local helpers using `(((b-a) % 360 + 540) % 360 - 180)` for shortest signed angle.

5. **`Mathf.CorrelatedColorTemperatureToRGB` is a Unity color utility, not a math op.** No equivalent in Unity.Mathematics. Keep as-is and document the exception.

6. **`Mathf.PerlinNoise` ≠ `noise.cnoise`.** `Mathf.PerlinNoise(x, y)` returns `[0, 1]`; `noise.cnoise(float2(x, y))` returns approximately `[-1, 1]`. When swapping, scale + bias the output (`cnoise * 0.5f + 0.5f`).

7. **Implicit conversion chains are forbidden.** Unity.Mathematics defines `float3 ↔ Vector3` but *not* `float3 → Vector4`. C# allows only one user-defined implicit conversion per expression, so `material.SetVector(id, float3)` does NOT compile. Wrap in `float4(x, 0f)` or `float4(f3, 0f)` when passing to an API that takes `Vector4`.

8. **`float3.zero` works as type-member access** because the compiler disambiguates `float3` as a type in that position. But `using static math` also imports lowercase `float3()` as a constructor method, so use `float3(x, y, z)` (call style, no `new`) for creation and `float3.zero` for the static field.

9. **Unity.Mathematics default Euler order is ZXY** (matches Unity's `Quaternion.Euler`). `float4x4.Euler(radians(eulerDegrees))` is a drop-in for `Matrix4x4.Rotate(Quaternion.Euler(eulerDegrees))`.

10. **`ceilpow2` is the direct replacement for `Mathf.NextPowerOfTwo`** (no need for hand-written bit twiddling).

11. **`Mathf.Lerp` clamps t to [0,1]; `math.lerp` does NOT.** To preserve Mathf.Lerp behaviour when t may be outside [0,1], wrap with `saturate(t)` in the caller. In preset/animation-curve blending this often matters (curves can return values > 1 at overshoot).

12. **`using static Unity.Mathematics.math` shadows `float3.zero` / `float4x4.identity` / `quaternion.identity` static-member access.** The `using static` directive brings `math.float3(x,y,z)`, `math.float4x4(AffineTransform)`, etc. into scope as methods. When resolving `float3`/`float4x4`/etc. the compiler picks the method group over the type, so `float3.zero` gives `CS0119: math.float3(float, float, float) is a method, which is not valid in the given context`.

**Fix for zero vectors:** write the literal `0`. Unity.Mathematics defines `implicit operator float3(float)` (and same for float2/float4/int2/3/4), so `float3 v = 0;` produces `float3(0,0,0)`. This is the preferred idiom — `0` reads as "zero vector" in context and beats `default(T)` for terseness. `default(T)` is the fallback when type inference needs help (e.g. inside `any(d != 0)` where `d` is `float2`, the `0` literal infers to `float2` automatically).

**Fix for identity matrices/quaternions:** implicit conversion via Unity types — `float4x4 m = Matrix4x4.identity;`, `quaternion q = Quaternion.identity;`. For `.Translate/.Scale/.Euler/.TRS` factory calls, use `Unity.Mathematics.float4x4.Translate(...)` fully qualified.

**`var` trap:** `var x = 0;` makes `x` an `int`, not the target math type. Write the explicit type (`float3 x = 0;`) or use `(float3)0` cast when `var` is mandatory.

**Bounds ctor / Unity API with Vector3 param:** `new Bounds(0, size)` doesn't work — `int` has no implicit to `Vector3`. Use `Vector3.zero` for these Unity API call sites.

Only arises in files that have BOTH `using Unity.Mathematics;` and `using static Unity.Mathematics.math;`. Files that need only type declarations (no math functions) can skip the `using static` and then `float3.zero` resolves normally.

**Why:** Each of these failed silently or loudly during a mechanical mass conversion of the atmospherics + heightfields packages. Documenting them up-front saves future modernisations from re-discovering each one.

**How to apply:** Before writing new Unity.Mathematics code, skim this list. Specifically: always think twice before writing `*` between two `float4x4` values; always wrap `Mathf.Lerp` calls with `saturate(t)` during mechanical replacement.
