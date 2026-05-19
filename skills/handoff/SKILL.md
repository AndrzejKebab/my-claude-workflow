---
name: handoff
description: Write a handoff prompt for a future session. Use when the user asks to write a handoff, prepare a handoff, or document context for a next agent to pick up the investigation.
---

# A handoff is a context briefing. Never a diagnosis.

You are writing a handoff because **you didn't finish the task** — out of context budget, out of expertise, or out of time. That premise is binding. **An agent who couldn't finish the task cannot have diagnosed it.** Whatever you "think the bug is" is the same theory that just failed to land a fix.

So the handoff carries **context cues only**: the symptom, where the next agent should start looking, what's already been tried and ruled out. Nothing else.

## Absolute prohibitions

- **No `Mode: Diagnosed`.** No mode field of any kind.
- **No "Root cause" section.** Not even hedged. Not even "the likely root cause."
- **No "Fix" / "Three sites" / "Plan" section.** No prescriptive change recipes.
- **No ranked hypothesis list** ("maybe it's A, maybe B"). Same trap, opposite shape — biases the next session toward your unverified hunches.
- **No file:line refs that point at "where the fix goes."** File:line refs are allowed ONLY for "here is where the code that exhibits the symptom lives — start your investigation here."

If you find yourself typing any of those — **delete it.** Your theory is unverified by definition.

## Required sections (only these)

```
# Handoff: <short topic>

## Why this handoff exists
One short paragraph. What you attempted, why you ran out (context / expertise / time). Be honest that you did NOT solve this.

## Symptom
Concrete user-visible behaviour. Exact repro steps. Absolute image paths if relevant.

## Where to start reading
File paths + line ranges + one-line "this is where the symptom surfaces". Orientation, not a guided tour to a predetermined answer.

## Already tried (do not revisit)
Bulleted, one-line each. ONLY things actually attempted and falsified, with the evidence in one phrase. NOT a list of "things I considered."

## Forbidden moves
Project-level constraints the next agent must respect (e.g. "no `cargo run --bin foo` as verification", "no edits to <module>", "no commits without user instruction").

## Deliverable
What the next session's reply must contain — investigation findings + diagnosis + proposed fix + verification, in that order. This forces the next session to investigate, not extend your guess.

## Repro / env
Worktree path. Branch. Minimal repro. Asset/config versions if material.
```

## Why this matters

The single most expensive failure this skill exists to prevent: **a handoff that looks diagnosed convinces the next session not to investigate.** They iterate on your dead-end hypothesis until the user redirects, having burned an entire orchestration cycle on the wrong layer.

The handoff that triggered the rewrite of this skill (`/tmp/taa-streaming-hash-handoff.md`, May 2026) claimed `Mode: Diagnosed`, gave three load-bearing file:line "fix sites", and was wrong about the root cause. Two iterations of agents trusted the framing and never investigated. The actual bug was one layer deeper. ~Half the orchestration's cost was wasted because the handoff *looked* authoritative.

If you genuinely have evidence pinning a root cause, **you wouldn't be writing a handoff** — you'd be landing the fix or telling the user directly. The act of writing a handoff is itself the evidence that your theory is unverified. Treat it accordingly.

## Filename

`/tmp/<short-kebab-topic>-handoff.md`. If a prior handoff exists at a similar name, append `-v2` / `-v3`. **Never overwrite** — the prior file is evidence of what didn't work.
