---
name: Commits are checkpoints, not curated history
description: User commits frequently as recovery points; cleanliness/squashing is not a goal. Descriptive messages are still preferred. In delegate mode, commit must be delegated to a sub-agent to keep diff out of orchestrator context.
type: feedback
originSessionId: 42962e51-34e2-4a27-9eb4-f52e6dddfdb7
---
Commits serve as checkpoints / recovery points, not as a curated history. Solo project — no PR review audience to keep history clean for.

**Why:** User works alone on this codebase; no co-authors to read history. Recoverability beats aesthetics. Squashing, rebasing-for-cleanup, or hesitating to commit "noise" are all wasted effort.

**How to apply:**
- Don't squash, don't rewrite, don't worry about commit granularity. Many small commits is fine and expected.
- Descriptive messages are still wanted — the message is the index into the checkpoint, not a release note.
- In `/delegate` orchestration mode: every substantive dispatch is preceded by a checkpoint commit, and that commit MUST be delegated to a sub-agent (invoking the project's `/commit` skill). Reason: running `git commit` from the orchestrator pulls the diff into its context and burns tokens on text the orchestrator does not need.
- General sessions: still commit when explicitly asked; the checkpoint preference doesn't override the "only commit when asked" default.
