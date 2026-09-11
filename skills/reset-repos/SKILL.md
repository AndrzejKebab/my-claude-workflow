---
name: reset-repos
description: Inspect and safely synchronize multiple Git repositories beneath a user-specified root without discarding local work.
---

# Repository synchronization

Operate only beneath the exact root directory supplied by the user. If no root was supplied, ask for it; never infer a home directory, drive, or collection of repositories.

Despite the historical skill name, do not run `git reset`, force a checkout, delete branches, discard changes, or push.

## Plan first

Resolve the root to an absolute path and discover Git repositories beneath it with read-only checks. Respect the requested depth or repository list; otherwise avoid scanning unrelated large trees.

For each repository, collect:

- resolved path;
- current branch or detached HEAD;
- remote and its advertised default branch;
- staged, unstaged, and untracked changes from `git status --porcelain`;
- ahead/behind state after a fetch, but only if the user requested network synchronization;
- worktrees that could make a branch unavailable for checkout.

Present a compact plan before mutations. Classify repositories as clean and current, clean and behind, dirty, divergent, detached, missing the expected remote, or failed to inspect.

## Safe synchronization

The user's synchronization request authorizes fetching and fast-forwarding clean repositories within the supplied root. Use the remote's actual default branch; do not assume `main` or `master`.

- Clean repository already on the default branch: fast-forward only.
- Clean repository on another branch: leave it there unless the user explicitly asked to switch branches.
- Dirty repository: skip and report it. Do not stage, commit, stash, switch, or clean automatically.
- Diverged branch: stop for that repository and report the divergence.
- Detached HEAD, missing remote, failed fetch, or occupied worktree: report and continue with other independent repositories.

If the user explicitly asks to preserve dirty work, inspect each repository separately and agree on the preservation method appropriate to it. A stash, checkpoint commit, or new branch changes repository history/state and must not be chosen generically across unknown work.

Never use `git pull` without controlling the integration mode. Prefer `git fetch` followed by an explicit `git merge --ff-only <remote>/<default-branch>` when the requested repository is clean and on that branch.

## Report

List every repository and outcome, including skipped dirty repositories and failures. Name branches or commits created only when the user separately authorized those actions. Do not claim that all repositories are synchronized when any were skipped, divergent, or unverified.
