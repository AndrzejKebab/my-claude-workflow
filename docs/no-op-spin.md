# No-op spin loops, and the two scripts that stop them

A dispatched subagent waiting on something long — a Unity suite, a build, a remote queue — will
sometimes poll *itself* awake with commands that do nothing, rather than simply stopping. Measured on
one agent waiting out a PlayMode run: **205 `echo .` calls in 12 minutes**, 17.2 per minute, median
gap 2.9 s.

Two things are wrong with that, and only one of them is the agent's.

**It buys nothing.** When a background command or a tracked task finishes, the harness re-invokes the
agent automatically. There is no wakefulness to maintain, so every poll is pure cost.

**It lands in the human's terminal.** Each one renders as `● Background command "Idle" completed
(exit code 0)`. The agent pays a tool call; the person watching pays a screenful. That asymmetry is
why this is worth a hook and not just a line of advice — advice only reaches agents that read it, and
the failure mode is invisible to the agent producing it.

## `cc-nospin` — the hook

`bin/cc-nospin`, wired as the **first** `PreToolUse(Bash)` hook by `install.sh` so a refusal
short-circuits before the other Bash hooks do any work. Two rules, deliberately asymmetric:

1. **A whole command that does nothing is refused on first use** — `echo .`, `echo idle`, `true`, `:`,
   bare `echo`/`printf`. There is no legitimate reason to run one of these as an entire command, so
   this rule has no false positives. A command that merely *contains* `echo` (`echo hi > f`,
   `echo "$(date)" && git log`) is untouched.
2. **Any command repeated ≥ 7 times inside 120 s is refused as a spin.** This is the rule that catches
   spins rule 1 cannot enumerate. The threshold is set high on purpose: a few repeated `git status`es
   while iterating is normal work, and a hook that blocks real work is worse than the spam it prevents.

Both refusals carry the fix rather than just a "no" — wait on the subject in one call, use `unity-ps`
for liveness, and remember the harness re-invokes you anyway.

**It fails open by construction.** Malformed JSON, absent `command`, and a missing `jq` all exit 0
with no output. A broken `PreToolUse` hook blocks *every* Bash call in *every* session, so failing
open matters more than catching every case.

State lives in `/tmp/cc-nospin-$UID/`, one file of timestamps per command hash, trimmed to the window
and capped at 64 entries.

## `unity-ps` — because `pgrep -f` reports phantoms

`pgrep -f "Editor/Unity -projectPath …"` **matches the shell running the pgrep**, because that pattern
sits in the shell's own command line. Every liveness check written that way reports an editor that
isn't there, and the report then gets relayed as fact. This produced three false "unity RUNNING"
claims in a single session before it was caught.

`bin/unity-ps` matches the *executable* instead — Unity's process comm is exactly `Unity`, and
`pgrep -x` cannot match a shell.

    unity-ps                        # pid + project path per running editor; exit 1 if none
    unity-ps -q <substring>         # silent; exit 0 if a matching editor is live
    until unity-ps -q myrepo; do sleep 30; done    # wait for a run to start
    while  unity-ps -q myrepo; do sleep 30; done   # wait for a run to finish

The general rule behind it: **match the executable, not the command line**, for any liveness check
whose pattern the checking process also contains.

## What to put in a dispatch prompt

The hook is the backstop, not the teaching. Any agent that will wait on a gate should be told:

> Do not poll with no-op commands to stay awake. When a background command or tracked task finishes,
> the harness re-invokes you automatically. If you must block, wait on the *subject* in one call —
> `while unity-ps -q <project>; do sleep 30; done` — not four hundred calls that wait on nothing.
> Use `unity-ps` for liveness, never `pgrep -f`. Bare foreground `sleep` is blocked; wait on a
> condition.

## Counting them after the fact

Subagent transcripts are symlinks under the session's `tasks/` dir pointing at
`~/.claude/projects/<slug>/<session>/subagents/agent-<id>.jsonl`. **Never read or tail one** — they
run to megabytes and will bury the reader's context. Count with `grep -oF`, or a small Python pass
that parses each line and filters on `tool_use.name == "Bash"`. Note that `grep -o` with a
`.\{0,60\}` context window is catastrophic on those very long JSON lines and will time out; and that
`stat -c%s` on the `tasks/` entry reports 145 bytes, which is the symlink, not the file.
