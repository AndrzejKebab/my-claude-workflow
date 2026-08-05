---
name: shipped-arm-measurement-channels
description: "On the shipped rotation arm only the drawn body's own yaw can show content behaviour — the transform is content-blind by construction and the root track is flat in all six packs"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0dea0b5e-5c2c-44aa-95dc-1a57e852cc29
  modified: 2026-07-25T13:36:41.074Z
---

Measured 2026-07-25 while chasing the owner's steering-regression report. Two of the three yaw
channels a fixture might grade **cannot move with the content** on the shipped arm
(`ContentOwnsRotation == 0`, which is every baked character — the field is not in
`CharacterAnimationAuthoring` at all, so only test sabotage ever sets it).

- **The transform** is chased toward the stick at `TurnSharpness` and the search is deliberately
  turn-blind there (`HeadOnOnly`, yaw demand pinned flat). A transform-channel metric reads the
  chase's step response and nothing else: mean facing lag came back **11.39° on every flicked leg of
  every one of six datasets, on both the guarded and the sabotaged arm**, to two decimals. Same
  failure as the camera family's `FixedOffAxisLook`, found independently.
- **The root track** is flat. All six packs carry their rotation in the hips, so
  `RootMotionSampler.YawSwing` is structurally zero — summed net root yaw read **0.0° on all 24
  legs, including sabotaged ones selecting 19% `Turn` content**. This is the MxM oracle's finding
  ("Kubold's turns rotate through the pose and not on the root track") seen from the runtime side,
  and it means `CharacterMovementSystem`'s `root.YawSwing` term is inert in practice on this arm.
- **What works: the drawn body's own yaw**, `CharacterRootMotion.BodyYaw` via
  `CharacterAnimationQueries.TraceOf`. Sabotage moves it 9.7° → 47.4° and 10.4° → 45.3° where
  guarded legs never exceed 16.9°.

**Why:** two fixtures were written and thrown away before this was noticed, because both looked like
they were grading the animation and both were grading the rig around it. A green from either would
have been a claim about the channel, not the content.

**How to apply:** before choosing a metric for anything about *what the search selected*, ask which
of the three channels the quantity actually lives in on the arm under test, and confirm the sabotage
arm moves it. On the referential arm the transform is the counter-swung one and the split differs —
see [[free-mode-turn-is-a-transform-arc]] and [[motion-matching-reference-split]].

Related: [[transition-regimen-reproduce-first]], [[character-controls-manual-qa-over-e2e]].
