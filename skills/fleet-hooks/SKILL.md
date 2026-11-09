---
name: fleet-hooks
description: Use when a tool call is refused with a message about FFF, a no-op or repeated command, a partial read of AGENTS.md or CONTEXT.md, or a comment wall, or when a reply is sent back for an offer, a tally or an unmeasured caveat.
---

# Fleet hooks

The owner's Claude Code hooks, ported to Hermes and run before your tool calls (`pre_tool_call`) and before you
finish a turn that edited code (`pre_verify`). Each refusal says what to do instead.

- **Search with FFF.** The first recursive `grep`, `rg`, `find -name` or `search_files` in a session is refused
  with the FFF tools to use: `mcp_fff_grep`, `mcp_fff_find_files`, `mcp_fff_multi_grep`. FFF indexes your
  workspace. The same command run again goes through, for paths FFF does not cover. `grep` on a pipe passes.
- **Read AGENTS.md and CONTEXT.md whole**: no `limit`/`offset`, no `head`/`tail` (from `bin/cc-whole-file-reads`).
- **No spin**: a command that does nothing (`echo .`, `true`) is refused; the same command more than 6 times in
  120 s is refused. Use `background: true` with `notify_on_complete: true` for long runs.
- **No comment walls**: a write or patch that adds 4 or more comment lines in a row to code is refused; walls
  already in the file do not block (rules from `bin/cc-comment-wall`).
- **No trailing offers** at the end of a turn that edited code: "want me to", "shall I", a tally ("three of
  the"), or a caveat with no number sends the reply back once (rules from `bin/cc-no-hedge`).

Not ported: `graphify hook-guard` (the bots have no graphify) and `cc-doctrine` (its list is empty).

`scripts/fleet_hooks.py pre-tool --state <file>` and `pre-verify`; per-bot state in
`Hermes/fleet-watchdog/hooks/`. These hooks fail open; the workspace guard (`fleet-workspace`) is the one that
fails closed. Tests: `python -m unittest discover -s scripts/tests`.

Example run:

```
$ echo '{"tool_name":"terminal","tool_input":{"command":"grep -rn ChunkMesh Assets/"},"session_id":"s"}' \
      | python scripts/fleet_hooks.py pre-tool --state .scratch/hooks.json
{"action": "block", "message": "Search code with the FFF tools, not grep, rg, find or search_files: ..."}
```
