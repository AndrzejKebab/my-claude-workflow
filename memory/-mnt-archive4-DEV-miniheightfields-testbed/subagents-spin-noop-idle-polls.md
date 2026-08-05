---
name: subagents-spin-noop-idle-polls
description: "Dispatched subagents waiting on long Unity runs spin `echo .` every ~3s; brief them to stop, it spams the owner's terminal"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4f26c060-09f8-4d4e-96ce-ef002cea51cc
  modified: 2026-08-05T02:28:41.644Z
---

A dispatched subagent waiting on a long Unity run will **poll with no-op Bash calls** — `echo .` /
`echo idle`, described as "Idle" — rather than simply stopping. Measured on one agent: **205 calls in
12 minutes, 17.2/min, median gap 2.9 s.**

**Why it matters:** each one renders in the owner's terminal as `● Background command "Idle" completed
(exit code 0)`. He noticed the wall of them and asked me to count them, which is how it surfaced. The
polling also buys nothing — the harness re-invokes an agent when a background command or tracked task
finishes.

**Now enforced by a hook**, so this is a backstop rather than a hope: `cc-nospin`
(`~/_dev/my-claude-workflow/bin/cc-nospin`, wired as the first `PreToolUse(Bash)` hook by that repo's
`install.sh`) refuses a whole command that does nothing, and any command repeated 7+ times in 120 s.
It fails open on bad input or missing `jq`. Full rationale in that repo's `docs/no-op-spin.md`.

**Still put this in the dispatch prompt** for any agent that will wait on a gate — the hook stops the
behaviour, the prompt prevents it:

> Do not poll with no-op commands to stay awake. When a background command or tracked task finishes,
> the harness re-invokes you automatically. If you must block, wait on the *subject* in one call —
> `while unity-ps -q <repo>; do sleep 30; done` — not four hundred calls that wait on nothing.

Two traps live in the same sentence: bare foreground `sleep` is blocked, and liveness must use
`unity-ps`, never `pgrep -f` (see [[unity-liveness-never-pgrep-f]]). Related:
[[research-background-jobs-need-setsid]] for the opposite failure, a background job that looks dead
but is not.

Counting them: the agent transcripts are symlinks under the session's `tasks/` dir pointing at
`~/.claude/projects/<slug>/<session>/subagents/agent-<id>.jsonl`. **Never Read or tail one** — they run
to megabytes. Count with `grep -oF` or a small python pass that parses each line and filters on
`tool_use.name == "Bash"`; `grep -o` with a `.\{0,60\}` window is catastrophic on those long JSON lines
and will time out.
