---
name: `using static Unity.Mathematics.math` name collisions
description: `using static math` brings min/max/lerp/abs/clamp/dot/etc. into scope as free functions. If a local variable or method has the same name it shadows/collides — rename locals, not the import.
type: feedback
originSessionId: 60fb3067-7f45-4e65-9083-e5b990f27c43
---
`using static Unity.Mathematics.math;` pulls dozens of free functions into file scope: `min`, `max`, `lerp`, `abs`, `clamp`, `saturate`, `dot`, `cross`, `length`, `normalize`, `floor`, `ceil`, `round`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan2`, `exp`, `log`, `log2`, `pow`, `sqrt`, `radians`, `degrees`, `mul`, `inverse`, `transpose`, `any`, `all`, `select`, `step`, `smoothstep`, `frac`, `fmod`, `ceilpow2`, `distance`, `lengthsq`, ... plus all the factory functions `float2/3/4`, `int2/3/4`, `uint2/3/4`, `float2x2/3x3/4x4`, `quaternion`, etc.

**Collision risk:** if the file defines `var max = ...;` or a method `float min(...)`, ambiguity errors start firing. The fix is to rename the local (e.g. `maxValue`, `minBound`), not drop the import.

Common collisions observed in real code:
- Variables named `min` / `max` / `length` / `distance` — all are math functions.
- Variables using `saturate` as a color name.
- Local method `Lerp(a, b, t)` — collides with `lerp` (case-sensitive, but easy to miss when renaming).

**Why:** The `using static math` pattern is the whole point of adopting Unity.Mathematics; the upside of HLSL-style call sites outweighs the occasional rename.

**How to apply:** Before converting a file, grep for the identifier names in the math namespace. If any exist as local/field/parameter/method names, rename them before dropping the `using static`.
