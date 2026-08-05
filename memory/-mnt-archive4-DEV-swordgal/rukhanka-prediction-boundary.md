---
name: rukhanka-prediction-boundary
description: "Rukhanka's netcode support predicts the Mecanim controller only — pose, root motion and IK run once per frame after prediction, and root motion is not rollback-safe"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d0351e90-f248-424e-8530-5b0c91c8f492
  modified: 2026-07-22T11:29:53.206Z
---

Rukhanka Animation System 2.9.1 (embedded at `Packages/com.rukhanka.animation`). Its documentation
says "full Unity Netcode for Entities support"; the code is narrower, and the boundary decides any
predicted-animation design.

**Predicted and rollback-safe:** the Mecanim `AnimatorController` state machine only.
`AnimatorControllerSystem<PredictedAnimatorControllerQuery>` runs in
`RukhankaPredictedAnimationSystemGroup` ⊂ `PredictedSimulationSystemGroup`, and
`AnimatorControllerLayerComponent.rtd` is a `[GhostField]`.

**Not predicted, with or without `RUKHANKA_WITH_NETCODE`:** pose evaluation
(`AnimationProcessSystem`), root motion (`ComputeRootMotionJob`) and all IK live in
`RukhankaAnimationSystemGroup`, which is `[UpdateAfter(PredictedSimulationSystemGroup)]`. **No shipped
configuration produces predicted root motion**, including the full Mecanim path.

**Root motion is stateful frame-differencing** — it subtracts the previous update's bone-0 pose from
`RootMotionAnimationStateComponent`, a plain non-ghost buffer a rollback does not restore. Re-running
a tick yields a near-identity delta; after a rollback it differences against a mispredicted future
pose. This is the entire re-entrancy defect: clip sampling itself takes an explicit absolute
normalised time and advances no internal clock, so **pose evaluation is already rollback-safe**.

The stateless alternative needs no package patch: `GetTrackGroupIndex`,
`ModifyBoneHashForRootMotion`, `NormalizeAnimationTime` and `BlobCurve.SampleAnimationCurve` are all
public, and root motion is a dense 7-track group in `clipTracks`. Sample at two absolute phases and
difference.

Nested blend trees without an `AnimatorController` asset are **not** available — the weight solvers
and the recursive tree walker are `internal`/`private`, and the one public nested path needs a
`ControllerBlob` only the Mecanim baker produces. `ScriptedAnimator` is a per-frame "here are the
clips and weights" submission API, not a state machine.

Grounded fact sheets, written 2026-07-22 against Rukhanka 2.9.1, DoubleL's 1820 clips, and this
project's prediction pipeline: `docs/orchestrate/character-rig/10-facts-rukhanka.md`,
`12-facts-doublel.md`, `11-facts-project.md`. Journals, not canon — verify at `file:line` before
relying on any claim. Related: [[presentation-group-lands-after-lateupdate]],
[[netcode-6-inprocess-session-harness]].
