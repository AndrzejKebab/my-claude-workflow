---
name: delegate
description: Multi-agent orchestration. The orchestrator scopes, briefs, and synthesizes — every other action is dispatched to sub-agents. The single most important rule: the orchestrator NEVER injects hypotheses, code-path references, or fix directions into briefs. Subagent context purity is the entire value proposition.
---

# delegate

## THE LAW: don't contaminate subagent context

The orchestrator does not read code. Any hypothesis about code it produces is hallucinated from training-data pattern-match. When a hallucination enters a brief, the subagent treats it as a directive and tunnels inside it instead of forming its own hypotheses from the actual code.

### DO: describe what is perceived

- What the user sees (visual description, spatial location in the rendered scene, conditions)
- How it is supposed to look (pointer to canon + behavioural target)
- What the user wants (goal + success criterion, verbatim)

### DON'T: locate the cause in the machinery

- No function names, pipeline stages, or named subsystems in the problemspace
- No "the issue is probably X" or "investigate Z first"
- No "the fix belongs at Y" or "the root cause is Z"
- No inferred code-path partitions dressed as topology ("X is the only mediator between A and B")
- No "therefore" connecting a symptom to a machinery location

**Test:** could the user see the term in the rendered output? If yes, relay it. If only a code reader would use it, it's forbidden in the problemspace section of the brief.

---

## When a fix fails: diagnose-first

The user reports the symptom didn't move → next dispatch is a **read-only diagnostic**. No "let me try option B." No Q&A. Diagnose is the only path.

**Before dispatching fix N+1:** write in chat what success would look like. When the user's report contradicts it, the hypothesis is falsified.

**3+ failed fixes on the same symptom → stop.** Offer `/diagnose-first` (scientific method), `/refactor`(reduce surface for clarity) or `/handoff`.

---

## Structural contracts

1. **Never work alone.** Every read, edit, build, test is dispatched.
2. **Checkpoint commit before every code-mutating dispatch.** Sonnet commit agent.
3. **Shared-context files on disk** (`docs/orchestrate/<topic>/`). One file per group. Agents read on entry, append on exit.
4. **Every deliverable ends with `## Side notes`.** Agent's channel to flag anything the brief missed.
5. **Compilation proves nothing.** Verify end-to-end. Visual work = user's eye = hard gate.
6. **Subagents are one-shot.** Context crosses between agents only via files on disk.

---

## Protocol

1. **Scope** — restate goal as behavioural problemspace (the three DO axes). Pick topic slug, name groups and files.
2. **Audit** — dispatch `delegate-auditor`. Read `00-reuse-audit.md` yourself.
3. **Mode** — distributed (default) or consolidated (bounded scope, low blast radius, tight design↔impl coupling).
4. **Brief** — present method to user. State recommendations and commit.
5. **Context files** — `README.md` + `01-context.md` (problemspace, constraints, audit summary, required reading, open questions, forbidden moves with hard provenance).
6. **Dispatch** — checkpoint commit → substantive agent. Brief leads with problemspace, suggests approach. Agent is Opus on equal footing.
7. **Synthesize** — verify group file written. Hard gate on visual QA / real choice / circuit-breaker. Soft gate otherwise.

---

## Brief template

```
You are working as part of a delegated orchestration. You have no memory of the parent conversation.

# Problemspace
<what is perceived, where in the scene, when, under what conditions>
<how it should behave — canon pointer + behavioural target>
<what the user wants — verbatim>

# Goal
<user goal>

# Suggested approach (not a script)
<2-3 bullets. "Phase however makes sense once you see the code.">

# Required reading
<paths + why each matters>

# Constraints
<user constraints, forbidden moves with hard provenance>

# Open questions (yours to resolve from code + canon)
<NOT pre-decided>

# Deliverable
<shape + path on disk>
End with ## Side notes / observations / complaints.
```

---

## Reference sections (load on demand)

- `execution-modes.md` — distributed vs consolidated, dispatch shapes, eligibility criteria
- `circuit-breakers.md` — diagnose-first, loop-detection, consolidated-mode handoff, brute-force protocol
- `context-boundaries.md` — what subagents can/cannot see, image protocol
- `askuserquestion.md` — when to ask vs brief, sticky amplification
- `e2e-gates.md` — gate authoring discipline for visual-capture gates
