---
name: vt-streaming-minimal-then-native-plugin
description: "VT packing/streaming ships minimal C# over StreamingAssets first; the optimisation target is a native plugin, never Burst+Jobs IO"
metadata: 
  node_type: memory
  type: project
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T16:13:26.837Z
---

Ruling, 2026-07-20, on how the VT archive packing/streaming track (roadmap F1) is built.

**Now:** the most minimal functional implementation, *even if significantly slower*. Offline
files written into `StreamingAssets`, read in C#, one archive file per terrain (not one file
per tile — that is Kühnert's shape and would put thousands of files into StreamingAssets).

**Explicitly rejected as an intermediate step:** an unmanaged filesystem interface driven
through Burst and jobs. It wins nothing over a native plugin and costs real complexity.

**The optimisation target is a cross-platform native plugin** branching directly to each
graphics backend for texture upload and owning the streaming loop. Any Rust/C++ codebase is
cleaner than Burst+Jobs for this task.

**Why this ordering is forced, not merely preferred:** Unity has no public API that uploads
user-supplied compressed bytes to a GPU texture off the main thread. The async upload pipeline
requires `isReadable == false` + data as a Unity streaming resource; `SetPixelData` requires
`isReadable == true`. Mutually exclusive. So the main-thread stall is not removable from C# at
any level of cleverness — which means clever C# buys a bounded win that the plugin would throw
away anyway.

**How to apply:** do not propose Burst/Jobs IO layers, custom allocators, or zero-GC gymnastics
for this track before the format and residency semantics are proven. Do rate-limit uploads per
frame (the admission budget already is this). Findings with evidence:
`docs/todo/terrain-io-packing-streaming-findings.md`. See [[wasm-defers-never-shapes-io]].
