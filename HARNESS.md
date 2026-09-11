# Harness / environment quirks (binding)

This section applies only when running inside Claude Code. Codex and other
harnesses must ignore it.

Observed behaviours of the Claude Code execution environment — shell, bundled tools, Workflow dispatch. Global to every Claude Code project and session, and the environment itself is not editable (per-session shell snapshots, hook-driven tooling), so the response is behavioural: do not "fix" these by editing the shell or settings. RTK is healthy and intentional ([[RTK.md]]); the one sanctioned RTK config change is the `ls` exclusion below.

## Shell + bundled grep

The Bash tool runs **zsh** (`SHELL=/usr/bin/zsh`) via a per-session shell-snapshot. In that snapshot `grep` is a **function** routing to Claude's bundled ripgrep-backed grep, falling through to real `command grep` only for a few flags.

- `grep --include='*.cs'` fails — ripgrep has no GNU `--include` (its flag is `-g`/`--glob`); unquoted `--include=*.cs` fails even earlier with zsh `no matches found`.
- Control flow is zsh, not fish or bash: `$(seq 1 5)` not `(seq 1 5)`. A wrong-dialect one-liner parse-errors, and in a parallel Bash batch that cancels the **whole batch**.

How to apply:
- For codebase questions, query an existing Graphify graph first. Otherwise use the `fff` MCP tools when available ([[FFF.md]]), then `rg -g '*.cs' pat path` or normal file tools. Plain `grep -rn pat file` (no `--include`) also works.
- Never `grep --include`. For genuine GNU grep semantics use `command grep …` or `bash -c 'grep …'`, which bypass the wrapper.
- Quote every glob; write zsh-dialect loops, or wrap loops/heredocs in `bash -c '…'`.

