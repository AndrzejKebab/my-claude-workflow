---
name: git-diff-redirect-is-empty
description: a git wrapper in this environment renders diffs to the terminal only — redirecting one to a file yields an empty file
metadata: 
  node_type: memory
  type: reference
  originSessionId: 153b55e5-a968-41be-a7dd-66d9b8858b40
  modified: 2026-07-21T13:55:00.337Z
---

`git diff`/`git diff-tree -p` output cannot be captured to a file here. `git diff A B > file` writes
**zero bytes** while the same command printed to the terminal shows the diff, and `git diff-tree -p
A B | head` emits `[rtk] git: process terminated by signal 13`. It is a git wrapper (`rtk`) on PATH;
using `/usr/bin/git` explicitly does not bypass it. Refs behave oddly too — `git diff A..origin/master`
came back empty where `git diff A..<sha-of-origin/master>` did not.

**Why:** several tool calls get burned believing a diff is empty, and an "empty" diff silently reads
as "nothing changed" — the wrong conclusion at exactly the moment (a rebase, a merge review) when
being wrong is expensive.

**How to apply:** pipe, never redirect — `git diff-tree -p -r A B | awk '…'` works and so does
`| wc -l`. Resolve refs to SHAs with `git rev-parse` before diffing. To get a diff into a file, have
a `node -e`/`awk` consumer do the work in the pipe instead.
