---
name: motion-matching-reference-split
description: "which reference each swordgal motion-matching mechanism actually comes from — \"the reference\" in comments means MxM, and some citations are wrong"
metadata: 
  node_type: memory
  type: reference
  originSessionId: b1d18ea3-5e04-4cd5-9bfe-185c86944e87
  modified: 2026-07-24T11:46:59.344Z
---

Sources live locally: MxM plugin at `Assets/Plugins/MotionMatching/Code/MxM/` (169 files), Unreal
PoseSearch at `/mnt/archive4/UNREAL/UE_5.8.0/Engine/Plugins/Animation/PoseSearch/`, Clavet's GDC
2016 talk at `/mnt/archive4/PAPERS/Prepared/clavet-2016-motion-matching.md`.

"The reference" in this codebase's comments means **MxM**. Verify before trusting a citation —
at least one was wrong: `MotionCalibration.FootingTolerance` says "the reference ships 0.3 and so
does the seed", but MxM has no footing/stride-phase concept in any file. The mechanism is Unreal's
`UPoseSearchFeatureChannel_FilterCrashingLegs` (`AllowedTolerance = 0.3f`, marked Experimental),
which `MotionClipSampler` cites correctly. Clavet explicitly rejects a phase measure — pose-match a
few bones instead, because phase is "ill-defined" exactly at starts, stops and turns.

Where the project diverges from MxM on purpose or by accident:

- MxM has **no commitment latch**. It re-searches every interval and suppresses churn by asking
  whether the incumbent still satisfies the goal (`NextPoseToleranceTest`) plus a 0.95 incumbent
  cost discount. This project latches structurally (`Committed`, `FadeSettled`) — see
  [[two-channel-blend-buffer]].
- The turn split is the project's own inversion, since corrected: Clavet's `TrajectoryPoint`
  carries a per-point facing (`m_Sight`) and content is chosen to match path *and* facing, residual
  closed by rotation warping. `CharacterFacing.ChaseRate` now shares a wide turn with the content.

Kubold does ship momentum-bearing 180 content — `RunFwdStart_L180` / `_R180` map to
`Run/Start/To:Forward/Turn:About`. The retired about-turn latch reached exactly those clips, so the
note calling what it entered "idle-paced" is inaccurate; what it really showed is that run-paced
content stalls a *sprint*. The cost function's `BodyVelocityWeight` is the guard the latch bypassed.
