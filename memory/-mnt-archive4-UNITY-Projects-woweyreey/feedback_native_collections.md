---
name: Use NativeCollections not managed types
description: RWVT and performance-critical systems must use NativeArray, NativeHashMap, NativeList — no Dictionary, List, Stack for core data structures
type: feedback
---

Use Unity Native Collections (NativeArray, NativeHashMap, NativeList, NativeQueue) instead of managed types (Dictionary, List, Stack) for core data structures in performance-critical systems like RWVT.

**Why:** Native collections represent the original C++ design more faithfully, avoid GC pressure, and enable Burst/Jobs compatibility.

**How to apply:** When designing data structures for RWVT page tables, tile pools, etc., use NativeHashMap instead of Dictionary, NativeArray instead of arrays/List, NativeList instead of List. Keep managed types only for truly managed-only contexts (editor UI, etc.).
