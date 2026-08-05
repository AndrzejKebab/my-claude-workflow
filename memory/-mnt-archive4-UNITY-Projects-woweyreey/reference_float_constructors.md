---
name: unity.js float2/float3/float4 constructor reference
description: How float2/float3/float4 constructors work in unity.js — runtime implementation and type declarations
type: reference
---

## Runtime (JS glue in `JsECSBridge.cs:300-336`)

All three constructors support these call patterns:
- **Splat**: `float3(5)` → `{x:5, y:5, z:5}`
- **Components**: `float3(1, 2, 3)` → `{x:1, y:2, z:3}`
- **Copy**: `float3(otherFloat3)` → copies `.x`, `.y`, `.z` from the object
- **Zero**: `float3()` → `{x:0, y:0, z:0}`

The copy path uses `typeof x === 'object'` — works with any object that has `.x`/`.y`/`.z`/`.w` properties.

## Type declarations (`Assets/StreamingAssets/unity.js/types/modules.d.ts:4-6`)

```typescript
export function float2(x?: number | float2, y?: number): float2;
export function float3(x?: number | float3, y?: number, z?: number): float3;
export function float4(x?: number | float4, y?: number, z?: number, w?: number): float4;
```

## Prototypes (`F2P`, `F3P`, `F4P` in JsECSBridge.cs)

Each type has `.add()`, `.sub()`, `.mul()`, `.div()`, `.equals()` methods and full swizzle accessors (e.g., `.xy`, `.xz`, `.xyz`, `.xyzw`).

Static constants: `float3.zero`, `float3.one` (same for float2/float4).
