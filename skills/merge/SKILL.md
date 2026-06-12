---
name: merge
description: Merge current worktree branch into main, cleanup worktree
---

> **Workflow context:** This is the final step after `/rebase` and manual verification.
> The full sequence is: `/rebase` → manual verification → `/merge`

Merge the current worktree's branch into main and remove the worktree.

## The submodule hazard (read before removing any worktree)

A worktree that was populated with `git submodule update --init` holds its submodules as **separate clones with their own object stores** (under `.git/worktrees/<wt>/modules/<path>`), distinct from main's submodule object store (`.git/modules/<path>`). A commit made inside the worktree's submodule therefore exists **only** in that worktree's clone. The superproject branch records a gitlink to it, but main's submodule cannot resolve it.

`git worktree remove` deletes the worktree's submodule clone. If you remove the worktree before propagating that submodule commit into main's submodule, **the commit is gone and main's superproject points at an unresolvable gitlink — the feature's submodule work is lost.** This is silent: the superproject merge succeeds, `git status` looks plausible, and the loss only surfaces later when someone runs `git submodule update` and it fails to find the commit.

The rule that prevents it: **never `git worktree remove` until every submodule commit the branch references is confirmed present in main's submodule object store** (`git -C <path> cat-file -e <sha>` returns success). Fetch-and-verify first; destroy the worktree last.

## Prerequisites

Before running `/merge`, ensure:
1. Branch has been rebased onto latest main (`/rebase`)
2. User has manually verified the feature works as expected
3. All changes are committed — in submodules first, then the superproject pointer (the project's submodule commit order)

## Process

1. Ensure all changes are committed (prompt the user if uncommitted changes exist). In a superproject with submodules, that means each touched submodule is committed and the superproject has committed the updated gitlink.
2. Detect the current branch and worktree path, and `${PROJECT_ROOT}` (the main checkout).
3. Extract the slug from the branch name (e.g. `feat/player-collision` → `player-collision`).
4. **Secure every submodule commit the branch references into main's submodule object store** — the propagation step below. Do this BEFORE the merge and BEFORE any removal. Abort the whole `/merge` if any submodule commit cannot be secured.
5. Switch to the main repo: `cd ${PROJECT_ROOT}`.
6. Merge the branch: `git merge <branch-name> --no-edit`.
7. Sync main's submodule working trees to the merged gitlinks: `git submodule update --init <each-touched-submodule-path>` (the objects are present because step 4 fetched them).
8. **Verify main is coherent before destroying anything:** each touched submodule is checked out at the branch's SHA, the feature files exist in main, and `git status` shows the submodules clean (no `+`/`-` gitlink mismatch). Only on a clean verification proceed.
9. Remove the worktree: `git worktree remove <worktree-path>` (add `--force` only if the worktree carries discardable working-tree noise — confirm that noise is genuinely discardable first).
10. Delete the branch: `git branch -d <branch-name>`.
11. Do NOT push unless explicitly requested. Pushing the superproject pointer without the user also pushing the submodule's commit to its remote would publish an unresolvable gitlink — submodule pushes are the user's, same as superproject pushes.

## Submodule propagation (step 4 in detail)

For each submodule that the branch advanced, fetch its commit from the worktree's clone into main's clone and verify it landed, before the merge:

```bash
WT=<worktree-path>; MAIN=${PROJECT_ROOT}
# every submodule path declared in .gitmodules
for sub in $(git -C "$MAIN" config --file .gitmodules --get-regexp '\.path$' | awk '{print $2}'); do
  # the commit the branch's gitlink points at for this submodule
  sha=$(git -C "$WT" rev-parse "HEAD:$sub" 2>/dev/null) || continue
  if git -C "$MAIN/$sub" cat-file -e "$sha" 2>/dev/null; then
    continue   # main already has it (shared objects / nothing new) — safe
  fi
  # main lacks it: fetch from the worktree's own submodule clone
  git -C "$MAIN/$sub" fetch "$WT/$sub" HEAD
  git -C "$MAIN/$sub" cat-file -e "$sha" \
    || { echo "ABORT: could not secure $sub@$sha into main — DO NOT remove the worktree"; exit 1; }
done
```

`cat-file -e` returning success on every referenced submodule SHA is the gate. If any fetch fails to make the SHA resolvable in main, stop — the worktree is still the only home of that commit and must not be removed.

## Naming Convention

| Component | Format |
|-----------|--------|
| Worktree | `.claude/worktrees/<slug>` |
| Branch | `<type>/<slug>` |

The slug is extracted from the branch name after the prefix.

## Edge Cases

- If currently on main, ask the user which branch to merge.
- If uncommitted changes exist, prompt before proceeding.
- **If a submodule commit cannot be secured into main (step 4 fails), abort and surface it — never remove the worktree.** The worktree's submodule clone is the only copy.
- A fast-forward merge still moves the superproject gitlink, so the submodule propagation + `submodule update` are required even when no merge commit is created.
- Worktree submodule working trees can fail to materialise on `git submodule update --init` (files absent despite a clean status); a forced checkout inside the submodule (`git -C <wt>/<sub> checkout -f <sha>`) repopulates them. This is a worktree+submodule quirk, not corruption.
