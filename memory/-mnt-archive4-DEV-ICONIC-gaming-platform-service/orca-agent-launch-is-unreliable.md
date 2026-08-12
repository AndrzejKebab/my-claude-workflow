---
name: orca-agent-launch-is-unreliable
description: "Orca's --agent claude launcher emits a broken command, and terminal send races the shell profile; verify by process list, not by reading the terminal"
metadata: 
  node_type: memory
  type: project
  originSessionId: 33865d99-65e2-41f2-9153-25592e5b860a
  modified: 2026-08-11T00:41:36.847Z
---

Two ways an Orca-launched agent silently never starts, both seen on 2026-08-11 while fanning out
nine SLOTS-166 worktrees:

- `orca-ide worktree create --agent claude --prompt "..."` emitted `mise cude '--dangerously-skip-permissions' '...'`
  into the first terminal. fish answered `Unknown command: ude` and the session died at the prompt.
  Every one of seven worktrees failed identically. The CLI still returned `ok: true` with an
  `agentTerminalHandle`.
- `orca-ide terminal send` into a freshly created worktree races the shell profile. The EMSDK/mise
  banner is still printing, the keystrokes land mid-line (`Settinclaude --dangerously-skip...`), and
  nothing runs. Also returns `ok: true`.

**What works:** write the invocation to a shell script, then
`orca-ide terminal create --worktree path:<dir> --command "bash /path/launch.sh"`. No interactive
typing, no race.

**How to confirm a launch:** `pgrep -f claude` and match `/proc/<pid>/cwd` against the worktree.
Reading the terminal is not proof — a failed launch leaves the command text on screen and looks fine.

`claude` is on PATH at `/home/midori/.local/bin/claude`; nothing needs `mise` to reach it. New
worktrees also need `mise trust <dir>` or the first mise call blocks on a trust prompt.

Related: [[git-push-blocked-by-harness]].
