---
name: no-sabotage-arms-tdd-instead
description: "Sabotage arms / biters are prohibited; use red-first TDD, and for graphics make it work before gating it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 25c8b7ab-4f71-4e41-9e10-b61528accdba
  modified: 2026-07-26T16:55:43.885Z
---

Do not author, regenerate, or extend **sabotage arms** ("biters") — patches that break the subject so
a gate can be watched going red. Write the test **red first**, then implement the feature or fix.
For graphics work, **make the thing work first** — get it on screen and look at it — and gate it
afterwards.

**Why:** the arms are an unbuilt second copy of the subject, kept in sync by hand. In this repo 20 of
49 arms had rotted against HEAD and 11 more applied at a slid offset, so `sensitivity.tsv` was
asserting demonstrated-red for gates nothing had tested (`docs/orchestrate/P1/06-patch-rot.md`). A
test observed failing before the code existed proves the same sensitivity for free, with nothing left
to rot. On graphics, a threshold invented before the first human look measures whichever channel was
convenient to read — which is how R-5d stayed green across a material boundary the owner could see
was broken.

**How to apply:** installed globally at `~/_dev/my-claude-workflow/VERIFY.md` (imported by
`~/.claude/CLAUDE.md`). In-repo, `docs/specs/ROADMAP.md` W-1 and `docs/specs/00-foundations.md` §7
were amended to mandate red-first only. The ~59 arms already committed under `Native~/tests/` and
`gates.sh`'s applicability preflight are **legacy, left running** — retiring them is the owner's
call, not a cleanup to do unasked. See [[voxelworld-foundations-spec]].
