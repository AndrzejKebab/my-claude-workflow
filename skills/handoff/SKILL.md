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

### the `.md` file

Path is **always absolute**: `/tmp/<short-kebab-topic>-handoff.md`. If a prior handoff exists at a similar name, append `-v2` / `-v3` — never overwrite (prior file is evidence of what didn't work).

Contents — minimal:

1. **One-line task statement.** What the next session is picking up. One sentence. Brief.
2. **Minimal necessary context.** Only what is NOT immediately obvious to a reader who understands the task at hand. Worktree path, branch (if not obvious from worktree), anything in-flight that affects how the next session starts (mid-edit state, uncommitted artifacts, in-progress orchestration docs to read at specific paths). Be specific and short — the next session will read on-disk artifacts (`docs/orchestrate/<topic>/`, design docs, recent commits) to ground itself.
3. **Verbatim user citations (optional).** If a specific user statement is load-bearing for the task, quote it verbatim under a heading like `## User's stated direction (verbatim)`. **Quote, do not paraphrase** — paraphrase loses the load-bearing nuance.

No required-section template beyond the above. No prescribed headings. No "deliverable" section. No "investigation order" section. Write the link, stop.

## Filename + path discipline

- File path: `/tmp/<short-kebab-topic>-handoff.md`. Absolute, always.
- Kickoff line: include the absolute path verbatim. The user copy-pastes; relative paths break.
