---
name: cdiff
description: "Open a git diff in a separate terminal window for a chosen scope—the repository root or a submodule. Use when the user asks to view or review a diff in a window, including a submodule's changes separately. Usage: /cdiff [scope] [range]."
---

# cdiff

Opens a git diff in a separate terminal window for a chosen scope, so a submodule's branch changes can be reviewed without the superproject's pointer-bump and import noise. It supports Windows Terminal on Windows and Ghostty or Kitty on Unix-like systems.

## Invocation

Locate `cdiff.sh` beside this `SKILL.md` and run it with Bash, forwarding the user's arguments verbatim. Do not hard-code a Claude- or Codex-specific installation directory.

```bash
bash "<installed-skill-directory>/cdiff.sh" [scope] [range]
```

- `scope` — `root`/`.`/empty for the superproject (default), or a submodule name or path (`gameplay-package`, `Packages/com.example.gameplay`). A bare name matches against `.gitmodules` by basename.
- `range` — any git diff range. The default shows the branch's own commits, excluding whatever it was rebased on top of: it uses the commit the branch was last replayed onto (read from the branch reflog's `rebase (finish): … onto <sha>` entry), falling back to the upstream tracking branch, then `main...HEAD`, and finally the uncommitted working-tree diff when HEAD has not diverged. The reflog base matters because a local `main` ref can be stale or on a line that does not even contain the rebase base, so a plain `main...HEAD` sweeps in the commits the branch was rebased onto.

Examples:

- `/cdiff` — the superproject's branch diff vs `main`.
- `/cdiff gameplay-package` — that submodule's branch diff vs `main`.
- `/cdiff root HEAD~3` — the last three commits at the root.
- `/cdiff gameplay-package d2a2e69..HEAD` — an explicit range in the submodule.

The window pages with `delta` when it is installed, otherwise `git diff --color | less -R`. Quitting the pager (`q`) closes the window.

## Notes

- Uses Windows Terminal (`wt.exe`) on Windows and Ghostty or Kitty when available on Unix-like systems. If no supported graphical terminal is available, it renders inline in the calling terminal.
- The script resolves the scope against the root of whatever checkout it is run from, so it works the same in the main clone and in a worktree.
- A submodule's branch diff is the work committed on its feature branch — the review unit before the superproject bumps its pointer. The default range computes that unit from the rebase base, so a feature branch replayed onto an in-flight sibling line shows only its own commits, never the sibling work beneath it.
