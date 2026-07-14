---
name: merge
description: Merge current worktree branch into main, cleanup worktree
---

> **Workflow context:** This is the final step after `/rebase` and manual verification.
> The full sequence is: `/rebase` → manual verification → `/merge`

Merge the current worktree's branch into main and remove the worktree. In a superproject with submodules, "into main" means main all the way down: the superproject's `main` advances, and each touched submodule's own `main` advances to the merged commit and is checked out — no submodule left in detached HEAD.

> **"main" = the LOCAL `main` branch (`${PROJECT_ROOT}`), never `origin/main`.** We push RARELY, so `origin/main` is routinely behind local `main`. The merge lands on local `main` and stays unpushed until you explicitly push (step 12) — never treat `origin/main` as the merge base or a verification reference, and never fetch/pull to "catch up" main before merging.

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
7. Sync main's submodule working trees to the merged gitlinks: `git submodule update --init <each-touched-submodule-path>` (the objects are present because step 4 fetched them). This leaves each submodule in **detached HEAD** at the gitlink SHA — the next step lands it on `main`.
8. **Land each touched submodule on its own `main`** — the submodule-main step below. `git submodule update` parks the submodule at a detached commit; merging the superproject without this leaves the submodule's `main` branch stale and its working tree detached. Fast-forward each touched submodule's `main` to the merged gitlink SHA and check it out, so the submodule's own `main` carries the feature and HEAD is attached to it. If a submodule's `main` has diverged (the merged SHA is not a descendant of `main`), leave it detached and surface it — never force `main` backward, which would orphan commits, and never substitute a merge commit, which would desync the superproject gitlink.
9. **Verify main is coherent before destroying anything:** each touched submodule is on `main` (not detached) at the merged gitlink SHA, the feature files exist in main, and `git status` shows the submodules clean (no `+`/`-` gitlink mismatch). Only on a clean verification proceed.
10. Remove the worktree: `git worktree remove <worktree-path>`. A worktree that contains submodules makes git refuse with `working trees containing submodules cannot be moved or removed`; clearing that guard needs `--force`. This is safe **only because** step 4 secured the submodule commit into main's store and step 9 confirmed coherence, so the worktree's now-redundant submodule clone carries nothing unique. (`--force` also covers discardable working-tree noise — confirm any such noise is genuinely discardable first.)
11. Delete the branch: `git branch -d <branch-name>`.
12. Do NOT push unless explicitly requested. When the user does push, the submodule's `main` (now advanced in step 8) goes first so its remote has the commit, then the superproject pointer that references it — pushing the superproject first would publish a gitlink the submodule remote cannot resolve. Both pushes are the user's.

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

## Landing submodules on main (step 8 in detail)

After the superproject merge and `git submodule update`, each touched submodule sits in detached HEAD at the merged gitlink SHA while its own `main` branch still points at the pre-merge commit. Fast-forward `main` to the merged SHA and attach HEAD to it, so the submodule is merged into its `main` the way the superproject was — not left detached. The fast-forward is clean in the normal flow because `/rebase` replayed the branch onto the latest submodule `main`, making the merged SHA a descendant of it.

```bash
MAIN=${PROJECT_ROOT}
for sub in $(git -C "$MAIN" config --file .gitmodules --get-regexp '\.path$' | awk '{print $2}'); do
  sha=$(git -C "$MAIN" ls-tree HEAD "$sub" 2>/dev/null | awk '{print $3}')   # merged gitlink
  [ -n "$sha" ] || continue
  cur=$(git -C "$MAIN/$sub" rev-parse -q --verify main 2>/dev/null || true)
  if [ -z "$cur" ]; then
    git -C "$MAIN/$sub" branch main "$sha"                       # no local main yet — create at the SHA
  elif [ "$cur" = "$sha" ]; then
    :                                                            # main already at the merged SHA
  elif git -C "$MAIN/$sub" merge-base --is-ancestor main "$sha"; then
    git -C "$MAIN/$sub" branch -f main "$sha"                    # fast-forward main (HEAD is detached, so -f is allowed)
  else
    echo "WARN: $sub main ($cur) is not an ancestor of merged $sha — left detached, resolve manually"
    continue
  fi
  git -C "$MAIN/$sub" checkout main                              # attach HEAD; no file change since main == current SHA
done
```

The fast-forward gate is `merge-base --is-ancestor main <sha>`: only advance `main` when the merged SHA is strictly ahead of it. A non-ancestor `main` means the submodule's branch diverged from the feature base; the superproject merge is still coherent (its gitlink resolves), but the submodule is left detached and the divergence is surfaced for the user to integrate by hand. `git branch -f main <sha>` works only because the submodule is in detached HEAD at this point — `main` is not the checked-out branch — so the force-update is not rewriting a live branch.

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
- **If a touched submodule's `main` has diverged (the merged SHA is not a descendant of its `main`), step 8 leaves that submodule detached and surfaces it rather than forcing `main`.** The superproject merge stays coherent because its gitlink still resolves; only the submodule's own `main` is left for the user to integrate. Forcing `main` backward would orphan its extra commits, and a merge commit would point `main` past the gitlink the superproject just recorded.
- A fast-forward merge still moves the superproject gitlink, so the submodule propagation + `submodule update` + landing the submodule on `main` are required even when no merge commit is created.
- Worktree submodule working trees can fail to materialise on `git submodule update --init` (files absent despite a clean status); a forced checkout inside the submodule (`git -C <wt>/<sub> checkout -f <sha>`) repopulates them. This is a worktree+submodule quirk, not corruption.
