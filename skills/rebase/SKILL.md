---
name: rebase
description: Safely rebase a clean feature worktree onto its intended local base branch before verification and merge. Use only when the user explicitly requests a rebase or the agreed workflow requires one.
---

# Rebase a worktree branch

Rebase the current feature branch onto its intended local base while preserving user work and making conflicts visible. Rebasing rewrites commit identities; do not start it implicitly during unrelated work.

## Determine the target

Identify from Git state and the worktree task context:

- repository root and current worktree path;
- current named feature branch;
- intended local base branch or explicit base ref;
- commits that would be replayed;
- whether the feature branch has an upstream that was previously pushed.

Honor a base explicitly chosen by the user. Otherwise use the base recorded when the worktree was created. If that is unavailable, apply the same local-default detection used by the `worktree` skill: local `main`, the local branch named by `origin/HEAD`, then local `master`. Ask when the result remains ambiguous.

Do not assume `main`, and do not replace a local base with `origin/<branch>`. Fetch or pull only when the user explicitly requests synchronization with a remote.

## Preflight

Before rebasing:

1. Run `git status --short` and require a clean feature worktree. If it is dirty, ask whether to commit, stash, or stop; do not choose automatically.
2. Confirm the current checkout is a named feature branch and is not the base branch or detached HEAD.
3. Confirm the base ref resolves locally.
4. Show the commits to be replayed, for example with `git log --oneline <base>..HEAD`.
5. Inspect submodule status when `.gitmodules` exists. Do not rebase a superproject while unique or uncommitted submodule work is unresolved.
6. Record the pre-rebase feature commit so recovery is straightforward.

If the feature branch was already pushed, warn that rebasing changes published commit IDs and ask for confirmation before proceeding. Permission to rebase does not imply permission to force-push afterward.

## Rebase

Run:

```bash
git rebase <local-base-ref>
```

Do not add interactive, autosquash, rebase-merges, or onto behavior unless the user requested it or repository instructions require it.

If conflicts occur:

- report `git status` and the conflicted paths;
- preserve the in-progress rebase;
- do not guess at semantic conflict resolution;
- offer to resolve with the user's direction or abort with `git rebase --abort`.

Never use `git rebase --skip` merely to clear a conflict: it drops a commit. Use it only when the user explicitly confirms that the affected commit is intentionally discarded.

## Verify

After a successful rebase:

1. Confirm `git status --short` is clean.
2. Show the new branch tip and recent commits.
3. Verify the recorded pre-rebase changes are still represented, using an appropriate range comparison or `git range-diff` when useful.
4. Run only the verification gates already requested or required by repository instructions.
5. Report the exact base used and whether commit IDs changed.

The next step is manual or automated feature verification, followed by the `merge` skill when the user asks to merge. Do not merge, remove the worktree, push, or force-push as part of this skill.

## Safety boundary

- Preserve unrelated user work and existing recovery refs.
- Do not fetch, pull, merge, or push without separate authorization.
- Do not use destructive reset or delete the feature branch.
- If the intended base or conflict resolution is ambiguous, stop with the repository left in a recoverable state.
