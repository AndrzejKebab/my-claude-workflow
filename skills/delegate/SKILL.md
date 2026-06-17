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

1. **Never work alone.** Every source read, edit, build, test, format, compile-fix is dispatched. Orchestrator reads only canon/spec and the group files. "Too small to dispatch" is the trap — a one-liner, config tweak, package install, "just run the build" all still dispatch. The test is *touches repo code/build?*, not *how small?*.
2. **Checkpoint before every code-mutating dispatch — and commit WIP often during the work; never hold a large uncommitted tree.** A committed WIP with a known-red gate is recoverable; an uncommitted pile is not, and under concurrent editors it invites clobbers and racing-writer loss (an agent's `git checkout`/`restore` on a shared file destroys a sibling's uncommitted edits with no copy to restore). Not commit purists: never gate a commit on all-green — commit at each meaningful step (a piece that passes, before a risky diagnostic, before a handoff), labelling WIP as WIP with the known-red gate named. **Each completed step checkpoints as its own commit before the next step dispatches** — when an agent returns its gate green, commit that deliverable immediately, never batch several green steps into one deferred commit, and never defer checkpointing to the user's own final commit ("the user commits at the end" is not a licence to hold a multi-step green tree; the user's commit is the end state, the orchestrator's per-step checkpoints are the recovery trail to it). Recovery, not tidiness, is the reason: git edits get botched, and a committed step is the only state a bungled `Edit`/`restore`/`checkout` can roll back to — an uncommitted multi-step tree has no floor. Edits revert via selective `Edit` from the diff, never `git checkout`/`restore` on a shared file. Sonnet commit agent for orchestrator checkpoints; substantive agents commit their own progress.
3. **Shared-context files on disk** (`docs/orchestrate/<topic>/`). One file per group. Agents read on entry, append on exit.
4. **Every deliverable ends with `## Side notes`.** Agent's channel to flag anything the brief missed.
5. **Verification is a dispatch — the validating agent.** Compilation proves nothing; verify end-to-end (visual = user's eye = hard gate). After the (often parallel) implementation dispatches, one validating agent owns the gate: runs build + tests, fixes what they surface (impl vs test bug, decided from spec/design), iterates to green, writes a log. Orchestrator relays build/test output as symptom, reads back green/red — never runs the gate or hand-fixes errors itself.
6. **Scope teammates to reusable topics, not one-shot tasks.** Agents here are persistent, addressable, resumable teammates — `SendMessage` by name continues one with its context intact; a fresh `Agent` call starts clean. The lever is the `name` parameter on the `Agent` call: pass a `name` to spawn a durable addressable teammate (resumable by `SendMessage` to that name); omit `name` for a one-shot subagent that runs, returns, and is gone. The roster is flat — a teammate cannot spawn named teammates, so any dispatched agent that itself fans out must omit `name` on its children (a named child spawn fails with "Teammates cannot spawn other teammates"). Scope one teammate to a live topic (an area that will take several related tasks) and route the topic's follow-ups back to it, so it keeps the code context instead of re-reading the area every dispatch. The purity LAW still governs: keep a FRESH agent for any job that needs unbiased eyes — verification/review (an implementer cannot review its own work), observe-first diagnosis, anything a prior task's conclusions would bias. Topic-reuse buys context economy; it never smuggles a prior brief's hypotheses into a job that needs fresh eyes. Retire a teammate when its topic closes (idle teammates otherwise linger on the roster), and re-scope fresh when its context bloats — a long-lived teammate's early hallucination hardens into its own later canon, and it runs slow and expensive. Disk group files stay the durable record, the cross-topic handoff, and the recovery channel when the transcript drops.
7. **Build publish-grade from the first line — fold in `/shipshape`.** Early (with the context files), commit the `CODESTYLE.md` inclusion into the target repo and add a shipshape-calibrated shape-discipline section to `01-context.md`, binding every substantive agent: the negative-space test (no deletable comment, no defensive check the types rule out, no doc restating a name); architectural courage (the right abstraction the cohesion points at — a type or seam, never a flag-threaded helper, and never a deep *wrong* one; duplication beats the wrong abstraction); the platform's domain idioms; the tell blacklist; reachable-citation discipline (cite what the shipped artifact's reader can reach, never the spec path or this journal); behavioral (not compile-only) gates. Briefs point agents at both. Canon: `~/.claude/skills/shipshape/STYLE.md` + `CODESTYLE-INCLUSION.md`.
8. **Sibling orchestrations are journals, not canon — don't cross-reference, inherit, or re-record them.** Another session's `docs/orchestrate/<other-topic>/` is its working memory and the lowest source-of-truth tier, below code at HEAD and research papers: a load-bearing claim grounds in code (`file:line`) or a paper, never a sibling journal. The orchestrator never lists sibling-session docs in required reading, and no brief points a sub-agent at one as canon. A sub-agent that reaches for a sibling journal on its own and inherits its conclusion — reading "session N rejected X" as "X is impossible" — has violated this; such a claim enters chat only after it is verified against the code, and an unverified sibling-journal conclusion never reaches the user as a wall (that is how a false dichotomy is manufactured). Do not re-record another session's claim into the current log as a corroborating fact — a tier-4 claim copied forward is noise that later reads as canon. When the user explicitly names a sibling session, the brief frames it as "what an agent thought once — verify every load-bearing claim against the code before acting; do not inherit its conclusions." Never amend another orchestration's docs from inside the current one (the "poisoning the well" cascade).

---

## Protocol

1. **Scope** — restate goal as behavioural problemspace (the three DO axes). Pick topic slug, name groups and files.
2. **Audit** — dispatch `delegate-auditor`. Read `00-reuse-audit.md` yourself.
3. **Mode** — distributed (default) or consolidated (bounded scope, low blast radius, tight design↔impl coupling).
4. **Brief** — present method to user. State recommendations and commit.
5. **Context files** — `README.md` + `01-context.md` (problemspace, constraints, audit summary, required reading, open questions, forbidden moves with hard provenance).
6. **Dispatch** — checkpoint commit → substantive agent. Brief leads with problemspace, suggests approach. Agent is Opus on equal footing.
7. **Verify & synthesize** — dispatch the validating agent (contract 5) to drive the build/test gate to green; confirm the group files were written. Hard gate on visual QA / real choice / circuit-breaker; soft gate otherwise.

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
Sibling-orchestration docs (any other docs/orchestrate/<topic>/) are not canon — do not inherit their conclusions; verify any claim against the code (file:line) before acting on or recording it.

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
