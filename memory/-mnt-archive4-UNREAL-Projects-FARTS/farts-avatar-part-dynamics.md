---
name: farts-avatar-part-dynamics
description: "FARTS avatar parts carry their own dynamics via Copy-Pose prefab actors, not Leader Pose — why, and the test suite"
metadata: 
  node_type: memory
  type: project
  originSessionId: caad7e56-b79e-4af6-b6b5-41951511bec5
---

Built 2026-06-25. Modular avatar customization parts (head/hair/outfit/cape/…) now preserve each
part's provisioned dynamics — RigidBody post-process AnimBPs, ChaosCloth, and any extra
components a designer adds. Supersedes the original Leader-Pose part attach in [[farts-als-character-foundation]].

**Why Leader Pose was wrong:** a `SetLeaderPoseComponent` follower's `ShouldTickPose()` returns
false (`Engine/.../SkeletalMeshComponent.cpp:1885`) → it never evaluates its own pose, so the
mesh's post-process AnimBP (cape/hair RigidBody) never runs and cloth is *bound* to the leader
instead of simulating. Cycling presets also crashed: leader-pose-bound Elf cloth (`SKM_*_Casual_04_FullSet`)
torn down/recreated mid-tick faulted in the world-tick task.

**How it works now:** each part is an `AFartsAvatarPart` actor (a "prefab" — the UE analogue of a
Unity prefab is a Blueprint Actor; extra components are Actor Components) attached to the visible
body and driven by **Copy Pose From Mesh** (`UFartsCopyPoseAnimInstance`). Because the part
evaluates its own pose, the mesh's post-process AnimBP + cloth run automatically — the dynamics
ride the **mesh asset** (Synty ships `post_process_anim_blueprint` + embedded cloth on the SKM), so
new parts/packs work with zero code. Config `Parts` is now `TMap<FName, FFartsAvatarPartDef{Prefab, Mesh}>`
(`Prefab` null → base actor + `Mesh`). Files: `Source/FARTS/FartsAvatarPart.*`,
`FartsCopyPoseAnimInstance.*`, reworked `FartsAvatarComponent::RebuildParts`. 6 presets re-authored
by `Scripts/reauthor_avatar_parts.py`.

**How to apply:** add a part = drop `{Mesh=<SKM>}` into a config's Parts (or a `BP_Part_*` child of
`AFartsAvatarPart` when it needs extra components). Never reach for Leader/Master Pose for a part
that must carry physics/cloth. Full architecture in `docs/avatar-system.md`.

**Tests** (`Scripts/run_avatar_tests.sh`, all green): headless automation `FARTS.Avatar.*`
(`PartsEvaluateOwnPose` = the leader-pose regression guard, `PresetCycleNoCrash`); real-session
probe `-FartsMeasureDynamics` (first-principles cape component-space motion range ~150cm +
36-switch crash repro through the Elf cloth); perceptual `-FartsCaptureAvatars` + numpy-SSIM vs
`Tests/Baselines/avatar/` (≥0.96). RigidBody/ChaosCloth only simulate in a real `-game` session,
not a bare commandlet world — that's why the motion/crash tier is a `-game -RenderOffScreen` probe.
