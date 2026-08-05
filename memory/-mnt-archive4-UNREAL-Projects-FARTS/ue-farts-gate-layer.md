---
name: ue-farts-gate-layer
description: "FARTS gates run through zori_skills/plugins/unreal runners, not raw engine invocations; the avatar SSIM gate is knowingly RED"
metadata: 
  node_type: memory
  type: project
  originSessionId: b50e515b-7098-4268-93e9-262ab2c101de
  modified: 2026-08-05T00:52:01.008Z
---

Do not compose raw `UnrealEditor` / `Build.sh` invocations for FARTS. The runners are
`~/_dev/zori_skills/plugins/unreal/skills/{seat,build,test,capture,run,validate}/run.sh`,
bound by `FARTS/.agents/project.sh`. Law: that plugin's `DOCTRINE.md`.

Three Unreal-specific traps the runners absorb, each verified 2026-08-05:

- **UE commandlets exit 1 on success.** Both FARTS validators PASS on their `[FARTS-TEST] PASS`
  sentinel while the process exits 1. Any gate reading `$?` reports green work as red.
- **`Automation RunTests <filter>` is a raw prefix match.** Demonstrated: narrowing the bound
  filter to `FARTS.Avatar` yields 2 tests, both green — "2/2 PASS" to a naive gate. The counted
  baseline (`.agents/test-baselines/expected-counts.tsv`, currently `FARTS 7`) correctly failed
  it 5 short.
- **`-RenderOffScreen` is not `-nullrhi`.** It runs the full renderer on the real GPU and takes
  a `gpu` queue slot; `-nullrhi` runs take the project queue only.

**Known-red on purpose:** the avatar capture gate. Two capture runs of the same unchanged tree
differ by SSIM 0.923–0.977 against each other, so the 0.96 threshold sits *inside* the noise
band — it has always been a coin flip. Cause: `Source/FARTS/FartsAvatarCapture.cpp:20`'s fixed
`SettleFrames{24}` samples the idle animation, its shadow and eye adaptation mid-flight. The
baselines are additionally stale (they predate the three `TargetDummy_*` actors in
`L_CharacterSandbox`). **Do not re-bless to make it green** — that hides the defect behind fresh
numbers. Fix is `docs/todo/capture-determinism.md`.

Seats: [[ue-nested-compositor-seats]]. The missing rig instrument that let
[[farts-offhand-grip-ik]] go unlooked-at is designed in `docs/todo/rig-measurement-harness.md`.
