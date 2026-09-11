---
name: worktree
description: Create or reuse an isolated Git worktree for feature, fix, refactor, or documentation work. Use when the user explicitly requests a worktree or isolated branch checkout.
---

# Create or reuse a worktree

Prefer a host-provided worktree facility when the user is working through Claude or Codex and that facility preserves the requested starting state. Otherwise use Git directly with the workflow below.

## Choose names and base

Derive a short kebab-case slug from the task unless the user supplied one. Use an appropriate branch prefix such as `feat/`, `fix/`, `refactor/`, or `docs/`.

Honor an explicit starting branch or ref. Otherwise determine the repository's local default branch rather than assuming it is always `main`:

1. use local `main` when it exists;
2. otherwise resolve `refs/remotes/origin/HEAD` and use its corresponding local branch when present;
3. otherwise use local `master` when it exists;
4. if none is available, ask which local branch should be the base.

Do not fetch, pull, or substitute a remote branch unless the user requests network synchronization. Record the selected base.

## Preflight

Resolve the repository root with `git rev-parse --show-toplevel` and inspect:

- `git status --short` for user changes;
- `git worktree list --porcelain` for an existing checkout;
- `git show-ref --verify refs/heads/<branch>` for an existing task branch;
- repository instructions governing branches, worktrees, submodules, and setup.

For direct Git use, default to `<repo>/.worktrees/<slug>`. Respect `AGENT_WORKTREE_ROOT` when set. The repository should ignore `/.worktrees/` so the container directory is never committed.

Do not reuse a directory merely because it exists. Confirm it is the worktree registered for the intended branch. If the path or branch conflicts with another task, stop and report the exact conflict.

## Create or switch

Conceptually:

```bash
repo_root="$(git rev-parse --show-toplevel)"
worktree_root="${AGENT_WORKTREE_ROOT:-$repo_root/.worktrees}"
worktree_path="$worktree_root/<slug>"
branch="<type>/<slug>"
base="<detected-local-base>"

git worktree add "$worktree_path" -b "$branch" "$base"
```

If the registered worktree already exists, use it without recreating the branch. Use absolute paths in subsequent operations and clearly report the selected worktree and branch.

## Initialize the checkout

Follow the repository's setup instructions. Do not assume every `package.json` project uses pnpm. When dependency installation is required, infer the command from the lockfile:

| Marker | Typical command |
| --- | --- |
| `pnpm-lock.yaml` | `pnpm install` |
| `yarn.lock` | `yarn install` |
| `package-lock.json` | `npm install` or documented `npm ci` |
| `bun.lock` / `bun.lockb` | `bun install` |

Install only when the user requested a ready-to-work checkout or repository instructions require it. Do not invent setup for an unfamiliar stack.

For Unity projects, do not copy `Library`, `Temp`, or other generated caches from another checkout. Let the selected Unity version import the worktree independently, and do not open two editors on the same worktree.

## Report

Return the absolute worktree path, branch, base branch/ref, whether it was created or reused, and any setup performed. Never push unless explicitly requested.
