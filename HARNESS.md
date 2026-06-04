# Harness / environment quirks (binding)

Observed behaviours of the Claude Code execution environment itself — shell, bundled tools, Workflow dispatch. These are global (every project, every session), and the environment is not editable (per-session shell snapshots, hook-driven tooling), so the response is behavioural, not configuration. Do not "fix" these by editing RTK, the shell, or settings — RTK is healthy and intentional ([[RTK.md]]); the shell snapshot regenerates each session.

## Shell + bundled grep

The Bash tool runs **zsh** (`SHELL=/usr/bin/zsh`) via a per-session shell-snapshot (`~/.claude/shell-snapshots/snapshot-zsh-*.sh`). In that snapshot `grep` is a **function** routing to Claude's bundled ripgrep-backed grep (`claude -G …`), falling through to real `command grep` only for a few flags.

- `grep --include='*.cs'` fails — the backend is ripgrep, which has no GNU `--include` (the flag is `-g`/`--glob`). Unquoted `--include=*.cs` fails even earlier with zsh `no matches found`.
- Control flow is zsh, not fish or bash: `$(seq 1 5)` not `(seq 1 5)`. A wrong-dialect one-liner parse-errors, and in a parallel Bash batch that cancels the **whole batch**.

How to apply:
- Default to `rg -g '*.cs' pat path`, the `fff` MCP tools ([[FFF.md]]), or `Read`/`Glob`/`Edit`. Plain `grep -rn pat file` (no `--include`) also works.
- Never `grep --include`. For genuine GNU grep semantics use `command grep …` or `bash -c 'grep …'`, which bypass the wrapper.
- Quote every glob; write zsh-dialect loops, or wrap loops/heredocs in `bash -c '…'`.
- RTK is a shell-independent `PreToolUse` hook (`rtk hook claude`), not the cause of any of the above. Leave it alone.

## Tool-output reliability + Workflow dispatch

The environment intermittently **drops, reorders, and duplicates tool results** in the transcript (seen across Bash, Read, Workflow). A missing result is not evidence of failure — it often arrives a turn later, interleaved. Parallel Bash calls in one message amplify the dropping; single calls render more reliably.

- A `Workflow` first-invoke has returned **no result at all** (no Run ID, no error, no persisted script) — genuinely not launched — while an identical second invoke launched cleanly. Distinguish "didn't launch" from "result dropped" before re-invoking: a workflow that secretly launched, re-invoked, gives **racing writers** (two agents editing the same file).
- Workflows do **not** appear in `TaskList` (that lists only background bash/agent tasks). Confirm a launch by the **Run ID in the result + output files appearing on disk**, or `/workflows` — never by `TaskList`.

How to apply:
- After any background dispatch, verify by Run ID + on-disk artifacts, not `TaskList`. If a result is blank, check disk for the persisted script / output files **before** re-invoking.
- Have dispatched agents write their deliverable to a file and return a one-line status — disk is the durable channel when transcript results drop (this is already the orchestrate-discipline norm).
- Prefer single Bash calls over large parallel batches here; if one result is blank, re-run that single call rather than assuming failure.
