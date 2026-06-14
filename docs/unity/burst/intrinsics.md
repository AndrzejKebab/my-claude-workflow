# `Unity.Burst.Intrinsics` — SIMD intrinsics and ISA guards

The CPU intrinsic surface available inside `[BurstCompile]` code, and the runtime-guard pattern for portable code.

## Layout

```
Runtime/Intrinsics/
  X86/
    X86.cs            — IsX86Supported
    Sse2.cs           — Sse2.IsSse2Supported + ~150 SSE2 intrinsics
    Sse4_1.cs         — Sse4_1.IsSse41Supported + SSE4.1 intrinsics
    Sse4_2.cs         — Sse4_2.IsSse42Supported + SSE4.2 intrinsics
    Avx.cs            — Avx.IsAvxSupported + AVX intrinsics
    Avx2.cs           — Avx2.IsAvx2Supported + AVX2 intrinsics
    F16C.cs / Fma.cs / Bmi1.cs / Bmi2.cs / Popcnt.cs (sub-features)
  Arm/
    Neon.cs           — Neon.IsNeonSupported + ~600 Neon intrinsics
    NEON_AArch64_*.cs — crypto, dotprod, fp16, rdma extensions
  v64.cs              — 64-bit SIMD vector
  v128.cs             — 128-bit SIMD vector (the canonical Neon / SSE width)
  v256.cs             — 256-bit SIMD vector (AVX width)
```

## Vector types

```csharp
public struct v64  { ... }     // 64-bit  — Neon-D, MMX-style
public struct v128 { ... }     // 128-bit — Neon-Q, SSE/AVX
public struct v256 { ... }     // 256-bit — AVX/AVX2
```

These are POD structs. Inside a Burst-compiled function, the optimizer maps them onto the matching CPU register class and the field-by-field accessors compile to no-ops.

Outside Burst (managed/mono), they exist as plain memory structs — the intrinsic functions return false-positive scalar results or throw. Always wrap intrinsic use in an `IsXyzSupported` guard.

## The `IsXyzSupported` guard pattern

Every intrinsic namespace has a static `IsXyzSupported` boolean property:

```csharp
[BurstCompile]
static unsafe void Add4Floats(float* a, float* b, float* dst, int count) {
    if (X86.Avx2.IsAvx2Supported) {
        // AVX2 path — process 8 floats per iteration.
        for (int i = 0; i + 8 <= count; i += 8) {
            var va = X86.Avx.mm256_loadu_ps(a + i);
            var vb = X86.Avx.mm256_loadu_ps(b + i);
            X86.Avx.mm256_storeu_ps(dst + i, X86.Avx.mm256_add_ps(va, vb));
        }
    } else if (Arm.Neon.IsNeonSupported) {
        // Neon path — process 4 floats per iteration.
        for (int i = 0; i + 4 <= count; i += 4) {
            var va = Arm.Neon.vld1q_f32(a + i);
            var vb = Arm.Neon.vld1q_f32(b + i);
            Arm.Neon.vst1q_f32(dst + i, Arm.Neon.vaddq_f32(va, vb));
        }
    } else {
        // Scalar fallback.
        for (int i = 0; i < count; i++) dst[i] = a[i] + b[i];
    }
}
```

Inside Burst, the compiler resolves `IsAvx2Supported` etc. **at compile time per build target**: when compiling for `x86_64-avx2`, the AVX2 branch is selected and the others are stripped. This means a single source kernel produces tight per-target native code, no runtime CPU-feature dispatch unless you wrote it explicitly via fat-binary mechanisms outside the scope of this doc.

Outside Burst (managed/mono), `IsAvx2Supported` returns `false` — falls through to the scalar path. This makes the same code safe to call from non-Burst code paths.

## Naming convention

Intrinsics use the **canonical names from the vendor reference**:
- X86 SSE/AVX intrinsics use the `_mm_*` / `_mm256_*` prefix dropped, with `mm_` / `mm256_` retained as `mm_*` / `mm256_*` static members of the class. e.g. `_mm256_add_ps` → `X86.Avx.mm256_add_ps`.
- Arm Neon intrinsics use the canonical `vaddq_f32` etc. names directly. e.g. `vaddq_s8` → `Arm.Neon.vaddq_s8` (cited `Runtime/Intrinsics/Arm/Neon.cs:41`).

This mirrors the ISA reference manuals so existing C/asm intrinsic knowledge transfers.

## Steam Deck targeting

Steam Deck is x86_64 with AVX2 + FMA + BMI1/2 (Zen 2 architecture). Project canon (`docs/unity/burst/empirical-examples.md`) prefers the AVX2 path for Deck builds. The fallback paths handle older Linux desktops (SSE4.2 baseline) and ARM (e.g. mobile, M1/M2 if ever targeted).

When writing a Burst kernel targeted at Deck, gate on `X86.Avx2.IsAvx2Supported` first; fall back to `X86.Sse4_2.IsSse42Supported` for the broader Linux baseline; then scalar.

## Inspecting generated code

Window → Analysis → Burst Inspector. Pick your target (e.g. `x86_64_sse4`, `x86_64_avx2`, `arm64_neon`), pick your job, view the assembly. The `IsXyzSupported` branches are visible: the unselected branches are gone, the selected branch is inlined.

## When NOT to use intrinsics

- **Default**: write scalar code with `Unity.Mathematics` types and let Burst auto-vectorise. Modern Burst is good at this for straight-line numeric code over `float3` / `float4` / `float4x4`.
- **Use `Loop.ExpectVectorized` to guard auto-vectorisation** instead of hand-writing intrinsics. Same perf, less code, portable.
- **Hand intrinsics** are warranted when:
  - Burst's auto-vectoriser fails (e.g. data-dependent control flow, masked stores, gather/scatter).
  - You need a specific instruction (e.g. `pcmpestrm` for string search, `aesenc` for crypto).
  - You're porting a known-good intrinsic kernel from C.

## Source citations

| Symbol                       | File                                                       |
|------------------------------|------------------------------------------------------------|
| `v64`, `v128`, `v256` types  | `Runtime/Intrinsics/v64.cs`, `v128.cs`, `v256.cs`          |
| `X86.IsX86Supported`         | `Runtime/Intrinsics/X86/X86.cs`                            |
| `X86.Sse4_2.IsSse42Supported` | `Runtime/Intrinsics/X86/Sse4_2.cs:17`                     |
| `X86.Avx2.IsAvx2Supported`   | `Runtime/Intrinsics/X86/Avx2.cs`                           |
| `Arm.Neon.IsNeonSupported`   | `Runtime/Intrinsics/Arm/Neon.cs:22`                        |
| `Arm.Neon.vaddq_s8`          | `Runtime/Intrinsics/Arm/Neon.cs:41`                        |
| `Arm.Neon.vadd_s8`           | `Runtime/Intrinsics/Arm/Neon.cs:30`                        |
