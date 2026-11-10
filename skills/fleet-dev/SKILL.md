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

Example run:

```
$ python patch_source.py --help
usage: patch_source.py [-h] [--find FIND] [--replace REPLACE] [--all] [--line LINE] [--insert-before INSERT_BEFORE] ...
$ python dirty_preserve.py --help
usage: dirty_preserve.py [-h] {save,check,restore,list} ...
```
