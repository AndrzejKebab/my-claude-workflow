---
name: commit-gate-matcher-gaps
description: "The agent commit gate matches the literal string `git commit`, so heredoc commits and `git merge --continue` slip past it while an innocent grep triggers it"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8ae36f4d-0c84-42f8-9001-f2bfd14c53b4
  modified: 2026-08-11T00:58:43.805Z
---

`preCommit.commandPatterns` in `.agents/hooks/hooks.json` is `\bgit\s+commit\b`, matched against the
Bash tool's **command string**. Three consequences, all observed:

- **`git commit -F - <<'MSG' … MSG` does not fire the gate.** Neither does `git commit --amend`,
  nor `git merge --continue`, which is how a conflicted merge is concluded. All three observed on
  2026-08-11: the commit lands instantly, no gate.
- **A command that merely *mentions* the string fires it.** `grep -n "git commit" file` ran the
  entire multi-minute gate.
- The gate is a PreToolUse matcher, not a git hook, so a person in a terminal is never gated.

**Why:** the gate is the single thing that blesses a branch, and a form that quietly evades it turns
a milestone into a checkpoint nobody checked.

**How to apply:** do not rely on the hook to have run — check. When the commit is meant to be gated
and the hook stays silent, run `pnpm test:precommit` by hand against the committed tree and say in
the handover which of the two happened; AGENTS.md prescribes exactly that for a host where the hook
does not fire. When it is *not* meant to be gated — an intermediate merge commit where the tree is
inconsistent by construction — `git merge --continue` is the honest route, but say so. Avoid the
literal words in unrelated commands; use a Read or a character class instead. See
[[git-push-blocked-by-harness]] for the sibling gap on push.
