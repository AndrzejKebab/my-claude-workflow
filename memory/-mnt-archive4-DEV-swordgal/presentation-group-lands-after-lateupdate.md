---
name: presentation-group-lands-after-lateupdate
description: "Entities' PresentationSystemGroup is appended AFTER MonoBehaviour LateUpdate, so it cannot feed a LateUpdate consumer the same frame"
metadata: 
  node_type: memory
  type: project
  originSessionId: ed4f6afe-17a9-4378-b57a-de840a7e455c
  modified: 2026-07-21T16:55:57.823Z
---

`PresentationSystemGroup` is appended to the **end** of the `PreLateUpdate` phase's subsystem list
(`ScriptBehaviourUpdateOrder.AppendSystemToPlayerLoop`), and MonoBehaviour `LateUpdate` is
`ScriptRunBehaviourLateUpdate`, **earlier in that same phase**. A value written from the
presentation group is therefore read by any `LateUpdate` consumer one frame late — every frame.

**Why:** the name and the phase both suggest it runs ahead of `LateUpdate`; it does not. The
resulting lag hides inside damping during continuous motion and only becomes visible at a
discontinuity, so it reads as a bug in whatever jumped rather than as an ordering fault.

**How to apply:** to hand ECS output to a MonoBehaviour that consumes it in `LateUpdate`
(Cinemachine's brain being the case here), write it from `SimulationSystemGroup` with
`[UpdateAfter(typeof(TransformSystemGroup))]` — the `Update` phase precedes every `LateUpdate` by
construction, and after that group `LocalToWorld` is final. Worked case, measurements and the
gate that catches it: `docs/camera-rig.md`, "PresentationSystemGroup is a frame too late for a
LateUpdate consumer" (fixed in `de44cc7`).

Related: [[netcode-6-inprocess-session-harness]].
