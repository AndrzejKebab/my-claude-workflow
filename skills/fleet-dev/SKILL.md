---
name: fleet-dev
description: Use to replace text in a CRLF source file safely, or to park somebody else's uncommitted changes before a branch switch and put them back byte for byte. Moved from bot-tools/dev and bot-tools/git.
---

# Fleet dev

Under `F:/Programowanie/my-claude-workflow/skills/fleet-dev/scripts/`; the old `bot-tools/` paths are shims.

| Tool | What it does |
|---|---|
| `patch_source.py` | Line-ending-safe literal replacement: matches on CR-stripped text, dry-runs by default, first site only unless `--all`, writes back in the file's own newline style. spawns: none. |
| `dirty_preserve.py` | `save --repo <repo> --store <dir>` copies the dirty files out with an md5 each; `check`; `restore` copies back and verifies every md5; `list`. Never stash or `checkout --` the owner's work. spawns: git. |

## Rules

- **Delete and move code by member, never by line span.** In a file of any size the helpers
  (`IsSnowLayer`, `States`, `BorderTaper`, …) sit interleaved between the members you are removing, so a
  computed `del L[a:b]` cuts them out silently; the compiler then reports a dozen undefined names minutes
  later, and the real damage is invisible in the script that did it. Locate the signature, brace-match to
  its own closing brace, print the exact text you are about to delete, and confirm it holds no other
  member declaration before running it.
- **Compile between deletions, not after all of them.** One structural edit, one compile, one commit; a
  batch of four deletions across four files with one compile at the end turns four small mistakes into one
  unattributable 39-error wall.
- **When a scripted edit mangles a file, `git checkout -- <file>` and redo it.** Restoring the last
  committing state costs one edit; repairing half-deleted braces by hand costs a compile per guess.
- Prefer `patch`/`patch_source.py` with a unique anchor over any line arithmetic — line numbers drift with
  every earlier edit in the same session.

Example run:

```
$ python patch_source.py --help
usage: patch_source.py [-h] [--find FIND] [--replace REPLACE] [--all] [--line LINE] [--insert-before INSERT_BEFORE] ...
$ python dirty_preserve.py --help
usage: dirty_preserve.py [-h] {save,check,restore,list} ...
```
