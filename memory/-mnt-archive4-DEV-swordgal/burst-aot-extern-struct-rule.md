---
name: burst-aot-extern-struct-rule
description: Desktop Burst AOT rejects ALL by-value struct params/returns in externs; editor JIT accepts them — player builds are the only gate that catches it
metadata: 
  node_type: memory
  type: project
  originSessionId: ed62fdaa-80a8-4140-90b5-7452588fa52e
  modified: 2026-07-20T23:32:23.950Z
---

Desktop Burst AOT (player builds) fails BC1064/BC1067 for **every** extern (`DllImport` or compiled callback) that passes or returns a struct by value — including 8-byte ids and `float3`. Editor Burst JIT compiles the same signatures fine (except >64-byte by-value returns, which crash the SysV classifier with BC0101), so the entire editor test suite stays green while the player build is broken.

**Why:** box3d's C ABI passes ids/vectors by value; the `com.box3d.entities` binding layer therefore cannot be called from `[BurstCompile]` code in player builds. The glue systems run managed by design (commit `c9cadc6` in box3d-unity).

**How to apply:**
- Any new system calling `B3Api.*` must NOT be `[BurstCompile]` until the native `b3w_*` pointer-shim layer exists (see package README "Runtime/Native" note). Shims must ship in rebuilt binaries for Linux+Windows+macOS together, or the platforms without them break with EntryPointNotFound.
- A Linux player build (`unity <proj> -batchmode -quit -buildLinux64Player <out>`) is the cheap AOT gate; run it before claiming Burst-adjacent binding work done.
