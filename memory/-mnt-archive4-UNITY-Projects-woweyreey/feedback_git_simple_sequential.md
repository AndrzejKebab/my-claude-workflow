---
name: Dead-simple sequential git workflow on this project
description: No worktrees, no parallelism, no branching unless context demands it. Continue in the current branch by default; agents work in the live tree.
type: feedback
originSessionId: 0c8013cd-69a6-4fef-b80c-ef328fedf212
---
Git work on this project is dead simple:

- **No worktrees.** Sub-agents always run in the live working tree, against the live Unity editor. Never pass `isolation: "worktree"` to the Agent tool.
- **No parallelism.** One agent at a time. Sequential dispatch only. Edits land one after another in the same tree.
- **No branching unless context suggests it.** Stay in whatever branch is currently checked out. Don't proactively create feature branches, don't switch off `decal-vt-engine` (or whatever the current branch is) unless the user explicitly asks for a branch or the work is clearly a fork from current direction.
- **Everything lands sequentially in the same branch by default.** Multiple subtasks (Phase 1, Phase 2, recovery, fixes) all accumulate as commits or uncommitted edits on the same branch. No "land in a feature branch and merge later" — that's worktree-shaped thinking.
- **No "recovery" framing for prior work.** When a prior agent stops mid-flight, its edits are already on disk in the live tree. The next agent just continues. Do not brief it to "diff against HEAD" or "triage what's salvageable" — that implies reconstruction. Just say "continue from where the prior session stopped".

**How to apply** when briefing a sub-agent or planning work:
- Do NOT begin a brief with "diff against HEAD to see what's there" — the prior session's edits *are* the current state, of course they are.
- Do NOT propose a new branch unless the user explicitly asks ("can you do this on a new branch?") or context strongly suggests fork-and-merge (e.g. an experiment the user explicitly wants isolated).
- Do NOT use git as a coordination layer between parallel agents (because there are no parallel agents).

This rule supersedes any default Claude Code reflex toward worktrees, branching, or "safe rollback via git". Trust the live tree; commit when the user says commit; otherwise just keep editing.
