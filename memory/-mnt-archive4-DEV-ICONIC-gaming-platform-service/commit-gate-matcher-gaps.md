---
name: commit-gate-matcher-gaps
description: "The agent commit gate matches the literal string `git commit`, so `git merge --continue` slips past it while an innocent grep triggers it — but an ordinary commit IS gated"
metadata:
  node_type: memory
  type: project
  originSessionId: 8ae36f4d-0c84-42f8-9001-f2bfd14c53b4
  modified: 2026-08-15T03:01:54.511Z
---

`preCommit.commandPatterns` in `.agents/hooks/hooks.json` is `\bgit\s+commit\b`, matched against the
Bash tool's **command string**.

**An ordinary `git commit -m` fires the gate and runs the whole of `pnpm test:precommit`.** Measured
2026-08-15 two ways: driving `.agents/scripts/hook-runner.mjs pre-tool-use` with the payload a commit
sends still ran past a 25 s `timeout` (exit 124), while `git status --short` returned instantly; and
three consecutive commits landed 2 min 25 s apart, which is one full gate each. `--amend`, `-F -` and
a heredoc all contain the string and fire too.

**`time git commit …` does not measure the hook.** The hook runs in the harness, outside the shell,
before the command. A sub-second `time` reading says nothing, and a phase-7 handoff that read it as
"the commit returned without running the gate" propagated the mistake through four sessions, each of
which then ran the gate a second time by hand.

What genuinely evades it: **`git merge --continue`** and `git rebase --continue`, which conclude a
commit without naming one. What genuinely over-fires: any command that merely *mentions* the string,
so `grep -n "git commit" file` runs the whole multi-minute gate.

The gate is a PreToolUse matcher, not a git hook, so a person in a terminal is never gated.

**Why:** the gate is the single thing that blesses a branch. Believing it silently skipped costs a
redundant gate run per commit; believing it fired when it did not turns a milestone into a checkpoint
nobody checked.

**How to apply:** trust an ordinary commit to be gated. Where the form evades it —
`git merge --continue` — run `pnpm test:precommit` by hand and say which of the two happened.
Avoid the literal words in unrelated commands; use a Read or a character class instead. See
[[git-push-blocked-by-harness]] for the sibling gap on push.
