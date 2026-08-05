---
name: Burst verification via unity-cli
description: "Burst errors only surface in the editor — use unity-cli console to check, not batchmode"
type: feedback
originSessionId: 0dde57e8-85e9-4f61-9aac-100450f5baee
---
When writing Burst-compiled code:
1. Never use managed types (arrays, strings, List<T>) — use NativeArray, NativeList, FixedString, EntityQueryBuilder
2. After any Burst code change: check `unity-cli console --filter error --lines 10` (Unity recompiles automatically)
3. Add `[assembly: BurstCompile(CompileSynchronously = true)]` to catch issues on first compile

**Why:** Burst compilation errors only appear in the editor console, not in test results. `unity-cli console --filter error` catches them immediately.

**How to apply:** After Burst code changes, always check `unity-cli console --filter error` before running tests. Never use unity-cli to trigger compilation — Unity handles that automatically.
