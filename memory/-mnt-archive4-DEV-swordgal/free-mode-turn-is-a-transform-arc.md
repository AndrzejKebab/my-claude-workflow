---
name: free-mode-turn-is-a-transform-arc
description: "SUPERSEDED 2026-07-24 for the rotation split — free-mode turns are now SHARED with the content via CharacterFacing.ChaseRate. Still current for: the retired about-turn latch, the backward-travel clamp, and two harness gotchas"
metadata: 
  node_type: memory
  type: project
  originSessionId: d5380412-70fb-441c-9555-683830c3509a
  modified: 2026-07-24T11:47:21.432Z
---

Resolved 2026-07-24 (`docs/orchestrate/motion-matching/18..20`, commit `21a6de8`). The owner's
long-standing turn misbehavior — "forward walk propelled backward, stuck midway, specific left/right
foot cadence, worse sprinting" — was the **about-turn latch**, not a clip-selection flip (that
doc-16 flip was already fixed by the frame-rebase and stays fixed).

**Root cause, traced tick by tick:** a free-mode 180 (`TurnDemand ≥ 120°`) fired the latch onto
Synty's `Run/Start/About` = `Idle_ToRun180`. That idle-paced clip turns the body only part way,
**stalls the sprint** (it has no momentum to give), and in its tail its root translation goes
**negative — drags the character backward** while the facing is frozen part-turned. Footing-phase
dependent, far worse under sprint (11/16 sprint reversals collapsing < 55 % of speed).

> **Superseded 2026-07-24 (commit `1334951`), rotation split only.** The base pack changed from
> Synty to Kubold, which *does* ship momentum-bearing 180s (`RunFwdStart_L180`/`_R180` →
> `Run/Start/To:Forward/Turn:About`), so the premise "no momentum-carrying U-turn clip exists" no
> longer holds. A wide turn is now **shared**: `CharacterFacing.ChaseRate` is one derivation read by
> both the mover and the search query, full sharpness inside the yaw slack easing to
> `WideTurnSharpness` at a reversal, leaving residual curvature the plant content answers. Owner QA:
> "feels natural." The latch stays retired — this goes through the cost function, whose
> `BodyVelocityWeight` is the sprint guard the latch bypassed. See
> [[motion-matching-reference-split]]. Everything below is the 2026-07-24 *pre-Kubold* reasoning.

**The decision — who controls rotation:** the transform **arc**, not content. A turn-in-place must
stop to reverse in place, so it structurally cannot keep a sprint's momentum; the arc reverses at
speed with velocity always along facing (no stall, no moonwalk). A *crisp content-driven* turn would
need a momentum-carrying "running U-turn" clip the Synty pack does not ship. So:
- the about-turn latch is **gated off** (`CharacterAnimationTuning.LatchAboutTurn`, off by design,
  kept behind the flag for future turn content, not deleted);
- free mode **clamps** a clip's facing-forward root translation to ≥ 0
  (`AllowBackwardTravel` lifts it) — a structural "never propelled backward against facing" contract
  in `CharacterMovementSystem`, gated on `!committed` so rolls/dodges keep their heading.

Kept gate: `CharacterTurnSessionTests` (sprint cadence sweep; sabotage restores latch + lifts clamp
to prove the bounds bite). This is the one controller-feel property the owner asked to gate
(overriding [[character-controls-manual-qa-over-e2e]] for this task).

**Two harness gotchas that cost hours this session, both durable:**
- **`Box3DCharacterState.Velocity` is not populated on the predicting client** — reads ~0 every
  tick. Only the **server** velocity is authoritative for any speed/velocity measurement.
- **Measure turns in OPEN space with a precondition guard.** The old QA arena was a cramped 40×40
  box (walls ±20) cluttered with crates/teleporters at the spawn; a drive that runs the character
  into a wall or teleporter reads as a "freeze," and a moonwalk metric that needs motion goes
  **vacuous** over a non-moving sample. The arena is now 120×120 (commit `689ade9`); always steer to
  a clear patch and assert path-length / moving-tick fraction before trusting a turn metric.

**Pre-existing red suite (surfaced, not mine):** at HEAD `d83262d`, 6 PlayMode tests were already
red (gait `run==walk` speed, pogo rest height 1.089 vs 1.4, deoccluder, rollflick, rig-idle,
teleporter walk-back). The turn fix added 0 regressions; those 6 predate it and want separate
attention (gait + pogo look like Synty/capsule migration fallout). Recorded in `20-turn-fix.md`.
Related: [[rukhanka-prediction-boundary]], [[netcode-6-inprocess-session-harness]].
