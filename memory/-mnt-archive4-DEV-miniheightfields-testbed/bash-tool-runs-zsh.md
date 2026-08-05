---
name: bash-tool-runs-zsh
description: "The Bash tool executes zsh, not bash or fish — unmatched globs abort the command instead of passing through"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 473fac03-6fd5-444d-a174-fe2bfbfd7695
  modified: 2026-07-21T19:00:26.758Z
---

The Bash tool runs `/usr/bin/zsh -c 'source ~/.claude/shell-snapshots/snapshot-zsh-*.sh && setopt
NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL && eval "<command>"'` — despite the tool's name and despite the
session brief reporting the shell as `/bin/fish`.

Consequences that actually bite:

- **An unmatched glob aborts the whole command.** `grep --include=*.cs …` dies with
  `(eval):1: no matches found` before grep ever runs; so does `[ -f /tmp/dir-*/x.xml ]`. Quote the
  pattern or use `find`/explicit paths.
- Errors are prefixed `(eval):N:` — that string is the tell you are in zsh, not bash.
- `#!/usr/bin/env bash` scripts are unaffected: they are executed, not sourced. Anything non-trivial
  is safer written to a file and run than inlined.

Do not verify "is anything still running" with `pgrep -f <pattern>`: the tool's own wrapper embeds
the full command, so the pattern matches the checking shell itself. A watcher loop written as
`until ! pgrep -f "…"; do sleep; done` never exits for the same reason — observed spinning for
90 minutes. Match on `/proc/<pid>/exe` instead; see [[unity-native-crash-forensics]].
