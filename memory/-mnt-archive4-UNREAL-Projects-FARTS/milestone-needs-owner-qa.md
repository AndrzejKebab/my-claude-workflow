---
name: milestone-needs-owner-qa
description: "Never commit a work milestone without the user's confirmation — usually a manual QA session on their part"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 36b456e7-251c-43d9-87bd-9faf0942996e
  modified: 2026-08-05T03:13:28.920Z
---

Never submit (commit) a work milestone without the user's explicit confirmation. Confirmation is
usually **a manual QA session they run themselves** — open a seat, hand them the note, wait for the
verdict. Green gates are permission to *ask*, not permission to submit.

**Why:** the agent cannot see. Every gate measures something narrower than "is this right" — a
measured play rate of 1.083 is a fact, but whether the motion now reads correctly is the owner's
judgement. An agent that commits on green has promoted its own instrument to the oracle, which is
the exact failure that produced the un-looked-at hand-IK work this project is still repairing.
Batching two unaccepted milestones is the same error, slower.

**How to apply:** bring the work to a state worth looking at, run the cheap gates first, then stop
and hand over — naming the change, the measurement, the artifact to look at, and what you could not
verify. Commit only after they say yes. Intermediate scratch (a diagnostic script, a probe that
does not work yet) is not a milestone and needs no ceremony. Written into the shared doctrine at
`~/_dev/zori_skills/plugins/unreal/DOCTRINE.md` §"A milestone is not submitted until the owner has
accepted it"; see [[ue-farts-gate-layer]] and [[ue-nested-compositor-seats]].

Note the global instruction "Always commit before submitting the work" is about not leaving work
uncommitted *when submitting* — it does not authorise submitting without acceptance.
