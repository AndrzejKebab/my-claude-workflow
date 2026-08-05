---
name: nographics-by-workload-not-by-tool
description: "Route Unity batchmode by whether the invocation puts work on the GPU — compile checks and profiler analysis take -nographics and skip the gpu queue; tests, player builds and capture runs must not"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 157e2511-3a7f-482c-88eb-1c8642a2153c
  modified: 2026-07-24T09:25:42.797Z
---

Ask **"does this invocation put work on the GPU?"** — not "is this Unity?", and
not "is this a build?".

| invocation | `-nographics` | `processqueue gpu` |
|---|---|---|
| `-runTests` / test-suite / test-player | never | yes |
| **player builds** (`profile/build.sh`, `build-run`) | **never** | **yes** |
| compile checks (`-quit` import) | yes | no |
| profiler analysis (`analyze.sh`) | yes | no |
| benchmark / capture runs | never | yes |

**Why compile checks changed:** the `gpu` queue is concurrency 1 by necessity,
so non-rendering work parked in it serialises behind whatever is rendering.
Measured 2026-07-24: the same URP17.5 compile check took **~10 min** queued
behind a Deck benchmark and **14.6 s** run directly with `-nographics`.

**Why player builds are the exception in THIS repo:** freezing a terrain's VT
archive is a *build step*, and it composites and reads back tiles on the GPU.
Under `-nographics` the package raises its own diagnostic — *"freezing needs a
graphics device — a -nographics batchmode run cannot composite or read back
tiles"* — plus `Kernel 'CSMain' not found` and `R32G32_UInt is not supported on
this platform`; the build dies with 13 errors. So "-nographics is fine for
builds" is true in general and false here, and the general form was applied
first and had to be walked back after a failed build.

Canonicalised 2026-07-24 in `AGENTS.md` (§batchmode, as a table) and the
`build-run` / `compile` / `profile` / `test-suite` / `test-player` skills and
their `run.sh`s. The old blanket "never `-nographics`" was wrong in the other
direction — it read as a law about Unity rather than about GPU work.
Related: [[single-editor-test-runs]], [[unity-run-liveness-ps-aux-lies]].
