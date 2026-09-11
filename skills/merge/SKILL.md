---
name: merge
description: Safely merge an approved Git worktree branch into its local base branch, verify the result, and clean up the worktree. Use only when the user explicitly asks to merge completed work.
---

# Merge a worktree branch

Merge locally and clean up only after the feature has been reviewed or verified. Do not fetch, pull, push, force-push, or assume the base branch is `main` unless the user explicitly chose those actions.

## Preconditions

Identify from Git state rather than path naming:

- the current worktree path and branch;
- the intended local base branch;
- the worktree containing that base from `git worktree list --porcelain`;
- uncommitted or untracked changes in both checkouts;
- submodules whose gitlinks differ between base and feature.

Require a named feature branch and a clean feature worktree. If changes are uncommitted, ask whether to commit, stash, or stop. Confirm the user has completed the required verification. Never merge a detached HEAD by guessing its intended branch.

If the workflow uses a preceding rebase, verify that the feature is based on the intended local base. Do not silently replace the local base with `origin/<branch>`.

## Protect submodule work

Apply this section only when `.gitmodules` exists and the feature changes one or more gitlinks.

Before merging or removing anything, determine each changed submodule SHA recorded by the feature branch. Confirm that the main checkout's submodule object store can resolve it:

```bash
git -C "<base-checkout>/<submodule>" cat-file -e "<feature-sha>^{commit}"
```

If it cannot, fetch that exact commit from the feature worktree's submodule checkout into the base checkout's submodule repository, then repeat `cat-file -e`. Stop if any SHA remains unavailable. The feature worktree may contain the only copy, so it must not be removed yet.

Do not force a submodule's local `main` branch to a gitlink SHA. The superproject records the required commit; changing a submodule branch is a separate decision.

## Merge and verify

From the base checkout:

1. Recheck that the base checkout is clean.
2. Merge the feature branch using the repository's documented strategy, or `git merge <feature-branch> --no-edit` when no different strategy is required.
3. If conflicts occur, stop and report the conflicted files. Do not guess at conflict resolution.
4. For changed submodules, run `git submodule update --init --recursive` and verify their checked-out SHAs match the merged gitlinks.
5. Run the agreed verification gates from the merged base checkout.
6. Confirm the expected commits and files are present and `git status --short` is understood.

If merge or verification fails, preserve both worktrees and report recovery options. Do not continue to cleanup.

## Cleanup

Resolve and verify the exact registered feature-worktree path before removal. Confirm it is not the base checkout, the repository root by mistake, or a directory containing uncommitted work.

Use ordinary `git worktree remove <path>` first. If Git refuses because of nested submodule worktrees or filesystem locks, diagnose the cause. On Windows, close applications holding the checkout; do not kill them automatically. Use `--force` only after proving all unique commits are reachable elsewhere, all worktree changes are disposable, and the user confirms forced removal.

After successful worktree removal, delete the merged local feature branch with `git branch -d <feature-branch>`. Do not use `-D` merely because safe deletion refuses. Prune stale metadata only when necessary.

Report the merge commit or fast-forward result, verification performed, removed worktree path, branch deletion status, and any remaining submodule or cleanup action. Do not push unless explicitly requested.
