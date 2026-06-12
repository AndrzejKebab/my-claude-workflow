# Harness / environment quirks (binding)

Observed behaviours of the Claude Code execution environment — shell, bundled tools, Workflow dispatch. Global to every project and session, and the environment itself is not editable (per-session shell snapshots, hook-driven tooling), so the response is behavioural: do not "fix" these by editing the shell or settings. RTK is healthy and intentional ([[RTK.md]]); the one sanctioned RTK config change is the `ls` exclusion below.

## Shell + bundled grep

The Bash tool runs **zsh** (`SHELL=/usr/bin/zsh`) via a per-session shell-snapshot. In that snapshot `grep` is a **function** routing to Claude's bundled ripgrep-backed grep, falling through to real `command grep` only for a few flags.

- `grep --include='*.cs'` fails — ripgrep has no GNU `--include` (its flag is `-g`/`--glob`); unquoted `--include=*.cs` fails even earlier with zsh `no matches found`.
- Control flow is zsh, not fish or bash: `$(seq 1 5)` not `(seq 1 5)`. A wrong-dialect one-liner parse-errors, and in a parallel Bash batch that cancels the **whole batch**.

How to apply:
- Default to `rg -g '*.cs' pat path`, the `fff` MCP tools ([[FFF.md]]), or `Read`/`Glob`/`Edit`. Plain `grep -rn pat file` (no `--include`) also works.
- Never `grep --include`. For genuine GNU grep semantics use `command grep …` or `bash -c 'grep …'`, which bypass the wrapper.
- Quote every glob; write zsh-dialect loops, or wrap loops/heredocs in `bash -c '…'`.

## RTK `ls` swallowing — excluded by config

`rtk ls` swallowed output entirely (empty result, exit 0), so any hook-rewritten `ls` looked like an empty directory. Fix applied: `ls` is listed in `[hooks] exclude_commands` in `~/.config/rtk/config.toml` (machine-local — re-apply on a new machine). Plain `ls` now runs unfiltered; pipe potentially large listings through `| head -40`. If another command's output vanishes with exit 0, suspect the rtk filter for that command and exclude it the same way — `rtk proxy <cmd>` confirms the diagnosis.

## Tool-output reliability + Workflow dispatch

The environment intermittently **drops, reorders, and duplicates tool results** in the transcript (seen across Bash, Read, Workflow). A missing result is not evidence of failure — it often arrives a turn later, interleaved. Parallel Bash calls in one message amplify the dropping; single calls render more reliably.

- A `Workflow` first-invoke has returned **no result at all** (no Run ID, no error, no persisted script) — genuinely not launched — while an identical second invoke launched cleanly. Distinguish "didn't launch" from "result dropped" before re-invoking: a workflow that secretly launched, re-invoked, gives **racing writers**.
- Workflows do **not** appear in `TaskList` (background bash/agent tasks only). Confirm a launch by the **Run ID + output files on disk**, or `/workflows` — never by `TaskList`.

How to apply:
- After any background dispatch, verify by Run ID + on-disk artifacts. If a result is blank, check disk for the persisted script / output files **before** re-invoking.
- Have dispatched agents write their deliverable to a file and return a one-line status — disk is the durable channel when transcript results drop.
- Prefer single Bash calls over large parallel batches; if one result is blank, re-run that single call rather than assuming failure.
