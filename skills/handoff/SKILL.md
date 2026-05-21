---
name: handoff
description: Write a handoff prompt for a future session. A handoff is a continuation-link — minimal context plus a kickoff line the user can copy-paste. Never a diagnosis, never an investigation script, never a prescribed deliverable.
---

# A handoff is a continuation-link, not a brief.

You are writing a handoff because **you didn't finish the task** — out of context budget, out of expertise, or out of time. That premise is binding.

- **An agent who couldn't finish the task cannot have diagnosed it.** Whatever you "think the bug is" is the same theory that just failed to land a fix.
- **An agent who couldn't finish the task cannot have scoped the next investigation.** Whatever shape you "think the next session should take" is unverified extrapolation of work you didn't solve.

The handoff is a **link**. It carries the minimum context the next session needs that isn't immediately obvious to a reader who already understands the task at hand, plus a kickoff line the user copy-pastes into the next session. Nothing else.

## Absolute prohibitions

- **No diagnosis.** No `Root cause`, no `Mode: Diagnosed`, no hedged "the likely cause".
- **No prescribed fix.** No "Three sites", no "Plan", no file:line refs that point at "where the fix goes".
- **No ranked hypothesis list** ("maybe it's A, maybe B"). Same trap, opposite shape — biases the next session toward your unverified hunches.
- **No prescribed deliverable shape.** Do NOT write "your reply must contain investigation + diagnosis + fix + verification, in that order". Do NOT enumerate required output sections. The next session decides shape from the task.
- **No prescribed investigation shape.** Do NOT write "investigate A first, then B, then C". Do NOT say "you'll likely want to start by reading X". The next session decides path from the symptom + context.
- **No file:line refs implying fix sites.** Refs that point at "the code that exhibits the symptom" are fine; refs that imply a prescribed change location are not. If you can't tell which kind a ref is, leave it out.
- **No `Already tried` justifications.** A bare `tried X — no change` is fine ONLY if X is unambiguous and the falsification is clean. `tried X because I thought Y` leaks the unverified theory and is forbidden.
- **No `Forbidden moves` lists invented for this handoff.** If there are project-level constraints the next session must respect, they live in the project's `CLAUDE.md` already — point at them (or rely on the next session reading the project CLAUDE.md), don't restate. Project rules belong with the project, not the handoff.

If you find yourself typing any of those — **delete it.**

## What the handoff contains

Two parts: a `.md` file on disk + a kickoff line you output in chat.

### Part 1: the `.md` file

Path is **always absolute**: `/tmp/<short-kebab-topic>-handoff.md`. If a prior handoff exists at a similar name, append `-v2` / `-v3` — never overwrite (prior file is evidence of what didn't work).

Contents — minimal:

1. **One-line task statement.** What the next session is picking up. One sentence. Brief.
2. **Minimal necessary context.** Only what is NOT immediately obvious to a reader who understands the task at hand. Worktree path, branch (if not obvious from worktree), anything in-flight that affects how the next session starts (mid-edit state, uncommitted artifacts, in-progress orchestration docs to read at specific paths). Be specific and short — the next session will read on-disk artifacts (`docs/orchestrate/<topic>/`, design docs, recent commits) to ground itself.
3. **Verbatim user citations (optional).** If a specific user statement is load-bearing for the task, quote it verbatim under a heading like `## User's stated direction (verbatim)`. **Quote, do not paraphrase** — paraphrase loses the load-bearing nuance.

No required-section template beyond the above. No prescribed headings. No "deliverable" section. No "investigation order" section. Write the link, stop.

### Part 2: the kickoff line

After writing the file, output the kickoff line in chat verbatim. **Pick exactly one launcher — `/delegate` or `execute` — never both as alternatives.**

```
/delegate /absolute/path/to/handoff.md [/worktree worktree-path]
```

OR

```
execute /absolute/path/to/handoff.md [/worktree worktree-path]
```

**Pick the launcher per this rule (binding):**
- **`/delegate`** — complex tasks. Multi-phase, design-needs-architecting, broad blast radius, or otherwise won't land in one session.
- **`execute`** — followups that can land in one session. Single-thread work that has clear context + a tractable scope.

If you're tempted to write `[/delegate]|[execute]` to "let the user pick" — that's a sign you haven't decided. Make the call from the task scope yourself. The user can override at paste-time by editing one word; that's cheaper than reading both options every paste.

Other formatting:
- The handoff path is **always absolute** — `/tmp/<topic>-handoff.md`, never `~/...` or relative.
- `[/worktree worktree-path]` is included **only if** the work lives in a worktree. Path is absolute or relative-from-repo-root, matching the project's convention.

Both halves of the handoff are required: the file gives the next session context, the kickoff line gives the user the literal shell-paste-able command with one launcher already picked.

## Why this matters

A handoff that prescribes shape — investigation order, deliverable structure, ranked hypotheses, fix sites — **convinces the next session not to think**. The receiving Opus iterates inside the orchestrator's framing instead of forming its own from the code.

This skill has addressed two failure modes in sequence:

1. **Diagnosis-shaped handoffs** (`Mode: Diagnosed`, "Root cause: X", "fix sites: Y, Z"). The receiving session iterates on the dead-end theory until the user redirects. The §"Absolute prohibitions" first-half list is the cure.

2. **Briefing-shaped handoffs** (`Deliverable: your reply must contain investigation + diagnosis + fix + verification, in that order`). Same anti-pattern at a higher level of abstraction — the orchestrator constrains the next session's deliverable shape instead of its hypothesis, but the constraint is still unverified, still forecloses the next session's own analytical surface, and still biases the work toward the orchestrator's mental model of "what the task is". The §"Absolute prohibitions" second-half list (no prescribed deliverable shape, no prescribed investigation shape) is the cure for this one.

The next session is the same flagship Opus you are. Trust it. The handoff is the link; the session is the work.

## Filename + path discipline

- File path: `/tmp/<short-kebab-topic>-handoff.md`. Absolute, always.
- Kickoff line: include the absolute path verbatim. The user copy-pastes; relative paths break.
- Prior handoffs at the same topic: append `-v2` / `-v3`. **Never overwrite** — the prior file is evidence of what didn't work for the prior session.
