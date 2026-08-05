---
name: character-controls-manual-qa-over-e2e
description: "swordgal project law: the owner's manual QA sessions replace e2e gate batteries — the loop is 'complete a bit of work, the owner tests it'; keep only the invariant battery plus minimal cheap oracles"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d0351e90-f248-424e-8530-5b0c91c8f492
  modified: 2026-07-23T14:17:07.595Z
---

For **this project (swordgal)**, agreed with the user 2026-07-23 and refined the same day:
the working loop is **"complete a bit of work → the owner tests it."** The gate/manual split
is a two-condition criterion, not a blanket preference:

- **Write and KEEP an e2e gate when both hold:** the property is *durable* (invariant-shaped,
  survives intended change — determinism, replication agreement, role-presence over a scripted
  drive) **and** *more-or-less trivial to author* against the existing session harness. Motion
  matching partially qualifies — its determinism/coverage session gates are written and kept.
- **Manual QA instead when either fails:** controller feel, tuning judgments, anything whose
  gate would need invented thresholds or heavy fixture engineering. Overengineering a
  character controller with e2e gates is more pain than testing it by hand.
- **Never unit tests** (global law, unchanged). Pipeline/bake structural checks live as
  bake-time diagnostics (asserts + printed counts at every bake), not test fixtures; a
  genuinely protective oracle stays minimal — one fixture, not a family; sabotage
  demonstrations run once with evidence in the log, not committed as permanent tests.

The owner enjoys watching the PlayMode session tests run in the live editor (real characters
driving through the real scene) — keep session fixtures visually observable; when the editor
is live, test runs double as an informal QA glance.

The bar, in the owner's words: gates "just confident enough where it won't waste the user's
time" — a minimal e2e correctness proof before any handoff, so the owner never QAs a broken
build, and no more. The handoff writeup gives **minimal** guidance on what to test — what
changed, a few pointed things to try, the tunables and where; never a walkthrough script.
Recorded in-repo at `AGENTS.md` §Testing.

**Why:** the user's own reading of the evidence, which the wave logs confirm — the actual
solutions were essentially one-shot once the spec was agreed (locomotion-C: a config default plus
one unification; locomotion-D: one product commit), while the bulk of each ~390k-token wave went
to gate fixture engineering (sabotage arms, detectors, thresholds; locomotion-D lost three
iterations to sabotage-arm placement alone), and feel-scenario gates premise-broke on the very
next design change (2 re-derivations in 3 waves). Too much surface to cover; overspeccing the
controller is too slow and too restrictive — the leeway is wanted, controller design being the
part that iterates most.

**How to apply:**
- Waves touching controls/feel ship product + writeup. No new feel-scenario acceptance gates, no
  sabotage batteries for behavior the owner's eye judges.
- The **invariant battery stays**: resimulation purity/determinism, replication agreement, style,
  boot smoke — no eye can see determinism, so those are not waived.
- A pre-existing feel-scenario gate that premise-breaks on a design change is **retired** (with a
  log note), not re-derived — per the standing refactor-box entry "scenario magnitudes in the
  session battery re-baseline on every movement change".
- This narrows, for this project's controller domain, the global readiness law's "problem
  statement fully covered by e2e tests" — the owner's QA session is the acceptance instrument, by
  their explicit instruction.

Recorded in-repo at `docs/orchestrate/character-rig/01-context.md` (dated amendment) and spec §10.
Related: [[netcode-6-inprocess-session-harness]].
