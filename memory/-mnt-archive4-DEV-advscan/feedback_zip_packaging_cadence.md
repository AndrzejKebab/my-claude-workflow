---
name: feedback-zip-packaging-cadence
description: "Don't repackage the submission ZIP after every iteration in the advscan/feedback-improvements orchestration — ZIP is final step only"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 065abfa1-fc37-424e-a893-af7c000c1ed2
---

Don't re-run `pnpm pack:submission` (or rebuild the submission ZIP) after every merge during the OX Security home-assignment feedback-improvements orchestration. There's iteration work pending beyond the named six-item list (e.g., visual-review bug fixes the user catches in screenshots after the initial pass merges). ZIP packaging is the **final step**, run once at the very end when the user signals "done, ship it."

**Why:** the user said verbatim on 2026-05-25, after WT-F's UI-filter bug fix merge: "dont repackage zip all the time, theres a lot to work on still - thats final step". Repackaging every cycle wastes time AND creates stale ZIP artefacts the user has to mentally discard. The user is also signalling that more iteration is expected — don't conflate "we hit a milestone, merge it" with "we're shipping, build the artefact".

**How to apply:**
- In any iteration-style worktree fix → merge cycle inside this orchestration, the merge dispatch verifies code gates (tsc/lint/tests) but does NOT call `pnpm pack:submission`.
- When the user signals the orchestration is genuinely done (e.g., "ship it", "build the final ZIP", "submission is ready", or after a final user-visual round of approvals), THEN dispatch the packaging step.
- This rule is for the iteration phase. WT-E's initial packaging dispatch was correct because the user-visible plan at that time treated WT-E as the last worktree.

[[01-context]] for the orchestration's canonical context. The `dist/advscan-ox-submission.zip` produced after WT-E's merge is the current artefact; later merges supersede it but don't regenerate it.
