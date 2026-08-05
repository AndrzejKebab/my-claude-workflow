---
name: orca-orchestration-mail-pull
description: Orca orchestration mail is pull-based; terminal send is the reliable push to a live agent
metadata: 
  node_type: memory
  type: reference
  originSessionId: b80714c8-46af-42f3-a410-2ce222db09fc
---

`orca orchestration send --to <handle>` only ENQUEUES to a runtime-global mailbox — it does not surface in the recipient agent's session. It is a pull channel, distinct from the harness teammate/SendMessage system (which auto-delivers).

- `orca orchestration check [--terminal <h>]` pulls messages to **whoever runs the command** and **marks them read** — running it to "verify a message queued" drains the unread state so a later `check --inject` finds nothing. Don't check-to-verify.
- A queued message enters an agent's actual session only when injected as an input turn: the recipient runs `check` itself, `--inject` at check/dispatch time feeds a recognized agent CLI, or `dispatch --inject` seeds a preamble. None happen automatically for a plain (non-dispatch-loop) agent.
- Reliable cross-terminal delivery to a **live** agent = `orca terminal send --terminal <h> --text "…" --enter` — types into its TUI as a user turn. Strip shell-dangerous chars (quotes/parens/backticks/`$`) in case the terminal is at a shell, not a TUI. `terminal read` scrollback can look like a fish prompt even when a Claude TUI is live — don't trust it to declare the agent dead.

Requires the orchestration experimental feature on + a running Orca runtime (`orca status --json`). See [[hypertino-continuation-state]] for the multi-worktree api-haus/* orchestration setup this came up in.
