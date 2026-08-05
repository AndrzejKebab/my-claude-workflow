---
name: farts-offhand-grip-ik
description: "Off-hand (left) grip IK for two-handed armaments runs post-retarget on the visible body, not in a source-side AnimBP"
metadata: 
  node_type: memory
  type: project
  originSessionId: 1b6664a3-3384-4478-9e5c-88b95ab0569a
---

The character's left hand grips the two-handed hammer haft via an explicit two-bone IK pass, added
2026-06-26 on branch `armaments-loadout`.

Key non-obvious architecture (verify at `file:line` before relying on it): the **visible body**
(`FartsBodyMesh` / `SKM_BodyA`, what the player sees and what the weapon attaches to) is posed
**entirely by a C++ retarget node** — `UFartsRetargetAnimInstance` whose proxy custom-root is a single
`FAnimNode_RetargetPoseFromMesh`. There is **no AnimBP asset** for the visible body. So any cosmetic
hand/limb IK on the visible mesh goes in that proxy's `Evaluate` *after* `RetargetNode->Evaluate_AnyThread`
— NOT in `ABP_FartsBodyUB` (that's a source-side linked overlay layer; its standalone AnimGraph doesn't
even run, and source-side IK inherits retarget proportion drift).

The grip is NOT a fixed socket the hand is pulled to — that bug (first cut) over-pulled the naturally
separated off-hand into the right hand (cramped) or, on the far side, left it floating unreachable. The
Gruzzam upper-body anims were authored for the original weapon, so animated `hand_l` lands ~30-50cm off
`SM_Grz_Hammer`'s haft and flips sides between idle (hand_r-local Z≈+23) and locomotion (Z≈-42). The haft
geometry (measured via `[FARTS-HAFT]`): mesh is axis-aligned with `hand_r`, origin at `hand_r`, handle
along hand_r-local **Z**.

Working approach (`SolveOffHandIk`): each frame, **project** the animated `hand_l` onto the haft line
(through `hand_r`, along the `GripL`-derived direction) and use that as the two-bone-IK effector — the hand
keeps its animated height down the shaft and only nudges radially onto it (matches the user's ask: "just
nudge a little to grip"). Two guards stop the through-body/180-flip the user hit while MOVING (walk cycle
flings the off-hand to the BACK/-Z side): (1) the slide clamp is **one-sided** — `[GripSlideMin,GripSlideMax]`
on the front/+Z side only (GripL now at +Z), so a back-side animated hand is pinned to the front band, never
chased behind the body; (2) **reachability disengage** — after the solve, scale alpha down by how far the
solved hand missed the target (`ReachEngage`→`ReachRelease` cm), so when the front grip is out of arm reach
mid-stride the IK fades out and the off-hand rides the animation instead of dragging through the torso. Net:
grips when idle, lets go while moving. `GripL` marks the haft direction + "weapon has off-hand grip", not the
grip point. Alpha gates on `Definition->Wield == TwoHanded`.

Tune `GripSlideMin/Max` (`FartsRetargetAnimInstance.h`) for two-handed spread → rebuild → check with the
`-FartsGripShot` SIDE screenshot; the off-hand should sit on the haft centerline (`[FARTS-IK]` solved
residual <1cm when it was instrumented). Full doc: `docs/armaments/07-off-hand-ik.md`. The hammer mesh
extraction context is [[grz-weapon-mesh-extraction]]; foundation is [[farts-als-character-foundation]].
