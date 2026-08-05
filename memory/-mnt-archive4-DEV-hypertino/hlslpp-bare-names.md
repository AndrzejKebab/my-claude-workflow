---
name: hlslpp-bare-names
description: "hlslpp types are used with bare names (float3, float4x4) — never hlslpp:: prefixed; bring them into scope ambiently"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 02766960-5f90-462d-a8a3-24b63f55ff2a
---

hlslpp math is written with **bare names** — `float3(x,y,0)`, `float4x4::translation(t)`, `mul(...)`, `normalize(...)` — never `hlslpp::`-prefixed. User (2026-07-04, sharp): "please quit doing this 'hlslpp::float3' crap, just use 'float3()' syntax — import it somehow ambiently" / "thats the whole point of using it — avoid this prefixing, it should not be used unless absolutely necessary".

**Why:** the clean HLSL/shader vocabulary is the entire reason hlslpp was adopted over glm; a `hlslpp::` prefix at every use site defeats the point and reads worse than glm did.

**How to apply:** bring the hlslpp compute types into scope ambiently — a using-declaration set in the math home (hypertino: `src/core/gpumath.hpp`), scoped so it doesn't leak `using namespace hlslpp;` out of a header into unrelated TUs. Prefix only on a genuine name clash, and even then alias to a bare name instead of writing the prefix at the site. The known clash: `hlslpp::float3` (16 B SIMD compute) vs `hlslpp::interop::float3` (12 B POD storage) — both named `float3`; give the POD a distinct bare alias (e.g. `packed_float3`). See [[suite-may-be-vacuous]] for the parallel gate discipline on this same port.
