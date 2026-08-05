---
name: delegate-checkpoint-commit
description: "/delegate checkpoint commit agent must do straightforward git add -A + commit (submodules then root), never stash/selective-stage/revert"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c432bf6d-5efa-40a0-94c3-6539035f2fb8
---

The `/delegate` checkpoint-commit sub-agent must do exactly one thing: read the diff *only* to compose messages, then `git add -A .` + `git commit` — **submodules first, then root**. NEVER `git stash`/`stash pop`, NEVER selective/partial staging (`git add <path>`, `git add -p`), NEVER `git checkout`/`restore`/`reset` a file.

**Why:** on 2026-05-14 a parallel `/delegate` session's checkpoint flow swept an unrelated session's in-flight `/research` extracts into its commits. The working tree is shared between concurrent Claude sessions; any "selective-stashing-popping" attempt to isolate one session's work WILL clobber or orphan the other session's uncommitted changes. The user was explicit and emphatic: "STRAIGHTFORWARD ADD AND COMMIT ONLY". Sweeping the whole tree into one checkpoint is correct-by-design, not a bug to work around.

**How to apply:** the fix is already baked into `/home/midori/_dev/my-claude-workflow/skills/delegate/SKILL.md` (Hard rule 7, Step 6 checkpoint brief, and an anti-pattern entry) — the checkpoint brief no longer invokes `/commit` (which has no submodule handling) and instead spells out the submodule-then-root `git add -A .` sequence with an explicit forbidden-verbs list. If editing the delegate skill again, preserve that brief. The root cause (two sessions, one working tree) also argues for separate worktrees per concurrent session.

Related: [[feedback-commits-as-checkpoints]], [[feedback-git-simple-sequential]].
