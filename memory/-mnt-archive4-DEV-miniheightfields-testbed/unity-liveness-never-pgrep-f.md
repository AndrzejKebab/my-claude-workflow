---
name: unity-liveness-never-pgrep-f
description: "Check for a running Unity editor with `unity-ps`, never `pgrep -f` — the pattern matches the checking shell itself"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4f26c060-09f8-4d4e-96ce-ef002cea51cc
  modified: 2026-08-05T02:28:34.836Z
---

`pgrep -f "Editor/Unity -projectPath …"` **matches the shell running the pgrep**, because that
pattern sits in the shell's own command line. Every liveness check written that way reports a
phantom editor, and the report is then relayed as fact.

**Why:** it produced a false "unity RUNNING" three separate times in one session, twice in messages
to the user. The user's words: *"can you please stop pgrepping pgrep? every day we have this issue,
deserves a custom script."*

**How to apply:** use `unity-ps`. It matches the executable name with `pgrep -x Unity`, which a shell
cannot satisfy. It lives in the workflow repo at `~/_dev/my-claude-workflow/bin/unity-ps` (on PATH
via that repo's `bin/`), documented in that repo's `docs/no-op-spin.md` — **not** in `~/.local/bin`,
which nothing tracks and no machine rebuild restores.

    unity-ps                        # pid + project path per running editor; exit 1 if none
    unity-ps -q <substring>         # silent; exit 0 if a matching editor is live
    until unity-ps -q myrepo; do sleep 30; done    # wait for a run to start
    while  unity-ps -q myrepo; do sleep 30; done   # wait for a run to finish

The general rule behind it: **match the executable, not the command line**, for any liveness check
whose pattern the checking process also contains. See [[unity-run-liveness-ps-aux-lies]] for the
other direction of the same trap — `ps aux` under-reporting concurrent batchmode runs.
