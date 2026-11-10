---
name: fleet-hooks
description: Use when a tool call is refused with a message about FFF, a no-op or repeated command, a partial read of AGENTS.md or CONTEXT.md, or a comment wall, or when a reply is sent back for an offer, a tally or an unmeasured caveat.
---

# Fleet hooks

The owner's Claude Code hooks, ported to Hermes and run before your tool calls (`pre_tool_call`) and before you
finish a turn that edited code (`pre_verify`). Each refusal says what to do instead.

- **Graph first, then FFF.** The first recursive `grep`, `rg`, `find -name` or `search_files` in a session is
  refused. Inside a repository with `graphify-out/graph.json` it points you at `graphify query "<question>"`
  for how things connect; for literal text, at `mcp_fff_grep`, `mcp_fff_find_files`, `mcp_fff_multi_grep`
  (FFF indexes your workspace). The same command run again goes through, for paths neither covers. `grep` on a
  pipe passes. Worker graphs are rebuilt daily by the watchdog. A search of `Docs`, `.memory`, `.project-state`
  or `.md` files is pointed at the document graph first: `mcp_semantica_query_graph`, `query_decisions`,
  `find_precedents` (read-only; the watchdog rebuilds it when a document changes).
- **Look before you write a script.** The first `write_file` of a new script into a scratch folder is refused
  with where to look (the skill list, the game's `.agents/skills`); writing it again goes through.
- **Read AGENTS.md and CONTEXT.md whole**: no `limit`/`offset`, no `head`/`tail` (from `bin/cc-whole-file-reads`).
- **No spin**: a command that does nothing (`echo .`, `true`) is refused; the same command more than 6 times in
  120 s is refused. Use `background: true` with `notify_on_complete: true` for long runs.
- **No comment walls**: a write or patch that adds 4 or more comment lines in a row to code is refused; walls
  already in the file do not block (rules from `bin/cc-comment-wall`).
- **No trailing offers** at the end of a turn that edited code: "want me to", "shall I", a tally ("three of
  the"), or a caveat with no number sends the reply back once (rules from `bin/cc-no-hedge`).

`graphify hook-guard` is folded into the search nudge (a Hermes hook cannot add context to a call it lets run).
Not ported: `cc-doctrine` (its list is empty).

`scripts/fleet_hooks.py pre-tool --state <file>` and `pre-verify`; per-bot state in
`Hermes/fleet-watchdog/hooks/`. These hooks fail open; the workspace guard (`fleet-workspace`) is the one that
fails closed. Tests: `python -m unittest discover -s scripts/tests`.

Example run:

```
$ echo '{"tool_name":"terminal","tool_input":{"command":"grep -rn ChunkMesh Assets/"},"session_id":"s"}' \
      | python scripts/fleet_hooks.py pre-tool --state .scratch/hooks.json
{"action": "block", "message": "Search code with the FFF tools, not grep, rg, find or search_files: ..."}
```
