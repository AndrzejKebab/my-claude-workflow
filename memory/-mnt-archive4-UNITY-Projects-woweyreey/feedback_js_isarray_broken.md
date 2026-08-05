---
name: JS_IsArray returns 0 for P/Invoke-returned arrays
description: QJS JS_IsArray P/Invoke returns 0 for arrays obtained via JS_GetPropertyStr — don't use it as a gate
type: feedback
---

`QJS.JS_IsArray(ctx, val)` returns 0 for arrays that were obtained via `JS_GetPropertyStr`. Use `QJS.IsObject(val)` + `JS_GetPropertyUint32` iteration instead.

**Why:** The project's `qjs.so` exports `JS_IsArray(ctx, val)` (old API), but newer QuickJS changed the signature to `JS_IsArray(val)` (no ctx). The P/Invoke passes `ctx` where `val` should go, causing it to always return 0. This was the root cause of the withNone query bug — the "all" array from `{all:[...], none:[...]}` was correctly obtained via `JS_GetPropertyStr` but then rejected by the `JS_IsArray` guard.

**How to apply:** When reading JS arrays in C# QJS bridge code, don't gate on `JS_IsArray`. Check `IsObject` and iterate with `JS_GetPropertyUint32` until undefined.
