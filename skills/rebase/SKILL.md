---
name: rebase
description: Rebase current worktree branch onto latest main
---

> **Workflow context:** This is step 1 of completing a feature. The full sequence is:
> `/rebase` → manual verification → `/merge`
>
> Rebasing ensures clean, linear history on main by replaying feature commits on top of the latest main.

Rebase the current worktree's branch onto the latest main branch.

> **CRITICAL — "main" = the LOCAL `main` branch, never `origin/main`.** We push RARELY, so `origin/main` is routinely stale/behind local `main` (merged branches sit on local `main` unpushed, sometimes for days). Run `git rebase main` — NEVER `git fetch` and rebase onto `origin/main`, which replays onto an old base and silently drops merged work (e.g. a math-library migration that's on local `main` but not pushed). Worktrees share the `.git`; `git worktree list` shows the `[main]` worktree, directly reachable. If local `main` and `origin/main` disagree, local `main` wins — that gap is expected, not something to "fix" by fetching.

## Pre-flight checks

1. Run `git status` to check for uncommitted changes
2. If uncommitted changes exist:
   - Ask user whether to commit, stash, or abort
   - Do NOT proceed until working tree is clean
3. Fetch latest from main worktree (no network fetch needed - it's local)

## Rebase

1. Get current branch name: `git branch --show-current`
2. Rebase onto main: `git rebase main`
3. If conflicts occur:
   - Show conflicted files: `git status`
   - Do NOT auto-resolve - ask user how to proceed
   - Options: fix manually, `git rebase --abort`, or `git rebase --skip`

## Post-rebase

1. Run `git status` to confirm clean state
2. Show new commit position: `git log --oneline -3`
3. Remind user: "Ready for manual verification. Test the feature, then run `/merge` when satisfied."

## Notes

- Rebase from the LOCAL `main` branch (same repo, different worktree) — NEVER `origin/main`, which is stale because we push rarely.
- No `git fetch` needed, and don't — worktrees share the same `.git`, and fetching only tempts rebasing onto a stale `origin/main`.
- Never use `--no-edit` with rebase (it's not a valid option)
- Never force-push without explicit user request
