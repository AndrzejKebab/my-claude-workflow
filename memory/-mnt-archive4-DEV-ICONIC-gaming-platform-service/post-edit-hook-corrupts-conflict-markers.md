---
name: post-edit-hook-corrupts-conflict-markers
description: "The postEdit hook runs `biome check --write` on every edit, and on a file still holding conflict markers it can silently rewrite the unparseable region"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8ae36f4d-0c84-42f8-9001-f2bfd14c53b4
  modified: 2026-08-11T00:40:23.480Z
---

`.agents/hooks/hooks.json` `postEdit` runs `biome check --write …` after every Edit/Write. A file
mid-merge still holds `<<<<<<<` / `=======` / `>>>>>>>`, which biome cannot parse — and it does not
always leave that region alone. Observed during the SLOTS-166 nine-branch merge: it stripped the
object braces out of a `caseBlocked({…})` call inside a conflict hunk, turning it into
`caseBlocked(\n caseId: …,)`.

It also floods the transcript: every partially-resolved edit reports dozens of parse errors, which
is pure noise while the markers are the reason.

**Why:** a formatter rewriting text it could not parse means the conflict text you read a moment ago
may no longer be the conflict text on disk, so a resolution built from a stale read silently drops
somebody's hunk.

**How to apply:** during a conflicted merge, resolve markers with a script through Bash (not
hooked) rather than Edit, or re-Read a hunk immediately before resolving it. Verify with
`git grep -l '^<<<<<<< '` and a typecheck before concluding the merge. See
[[commit-gate-matcher-gaps]].
