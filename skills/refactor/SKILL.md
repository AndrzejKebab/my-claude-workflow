---
name: refactor
description: Three-phase refactoring orchestrator. Dispatches an exploration agent to surface concrete smells and architectural problems, then an architecture agent to design better structure, then an implementation agent to apply the changes. The orchestrator never reads, edits, or runs builds itself — it scopes the target, holds the phase boundaries, and synthesizes between agents through shared-context files at `docs/orchestrate/refactor-<slug>/`. Use when invoked via /refactor, when the user asks to refactor a module/crate/package, or when the work explicitly calls for a structured smell-find-then-redesign-then-apply loop.
---

# refactor

Enter refactoring-orchestrator mode. The orchestrator does **not** do the work. It scopes the target, briefs each phase, shares context through disk, and pauses for user confirmation between phases. Every read, every search, every edit, every test run is dispatched.

## When to invoke `/refactor`

`/refactor` is the dedicated cleanup pass. Code quality is NOT the job of `/delegate`'s reviewer dispatch (reviewer is opt-in only there) — code quality lives here.

Concrete triggers — invoke `/refactor` when any one of these fires:

- **User-invoked.** "this stinks, refactor"; "clean up X"; explicit `/refactor` command.
- **3+ consecutive failed fix attempts on the same user-visible symptom** during a `/delegate` orchestration. Pattern: the diagnoses are code-grounded but the fixes don't move the symptom. Strong signal that the iteration target is foundation-rot, not the immediate scope. `/delegate`'s loop-detection circuit-breaker offers the switch.
- **2+ agents converge on a smell flag** in their `## Side notes` sections across a `/delegate` orchestration (e.g. "two addressing schemes for one buffer", "this code stinks", "the foundation looks wrong"). Multiple independent agents observing the same smell is signal, not noise.
- **Diagnose-first has fired 3+ times** in one orchestration without producing a fix that moves the symptom — same pattern as the loop-detection trigger, viewed from the diagnose-first protocol's angle.
- **The orchestrator (or you, working without /delegate) notices** obvious architectural rot when reading the codebase: conflated concerns, IoC violations, accidentally-global state, "dead memory nobody reads", a one-shot offline mechanism shoehorned into a streaming context, two addressing schemes for the same buffer, abstractions that fight the standard pipeline for the domain.
- **Periodic cadence.** After every ~5-10 feature-completion `/delegate` cycles in a project, run a `/refactor` pass to harvest accumulated drift before it compounds. Mark this in the project's README or todo list.

The triggers are mutually independent — any one of them is sufficient. Multiple firing together is a stronger signal but the threshold is "one trigger" not "two".

**Do NOT defer a refactor when a trigger has clearly fired.** The cost of one `/refactor` cycle is bounded (three dispatches, scoped target, clear deliverable). The cost of NOT refactoring is dispatch after dispatch landing on top of foundation rot, each wasting tokens, each pointing at the same un-named smell. Tunnel vision is the failure mode this skill exists to cure. When a trigger fires, invoke.

## Phases

1. **Exploration** — `refactor-explorer` agent identifies concrete code smells and architectural problems in the target scope. Output: prioritized findings list with file:line refs, severity, and rationale.
2. **Architecture** — `refactor-architect` agent designs better structure for the findings the user confirmed. Output: target-state design with concrete module/type/function shape, migration steps, and explicit "what stays / what changes / what's removed" lists.
3. **Refactoring** — `refactor-implementer` agent applies the design as actual edits, runs the project's verification gates, and reports per-step status.

Each phase is one dispatch. Each phase ends with a mandatory user pause.

## Hard rules

1. **Never work alone.** The orchestrator only writes shared-context files and dispatches agents. If you find yourself about to Read code, run a build, or Edit a source file outside `docs/orchestrate/refactor-<slug>/` — stop and dispatch.
2. **Phases are sequential and gated.** Exploration must finish (and the user must confirm the findings to act on) before architecture begins. Architecture must finish (and the user must confirm the design) before refactoring begins. Never chain dispatches without the pause.
3. **Shared-context files are the medium.** All inter-phase information flows through `docs/orchestrate/refactor-<slug>/*.md`. Agent return text is for status only — the deliverable MUST land on disk before the agent returns.
4. **Briefs are self-contained.** Sub-agents have no memory of the parent conversation, no view of attached images, no shared state with the orchestrator. Inline every fact: target paths, scope boundaries, project conventions, prior agents' findings, user constraints. Never write "as discussed" or "see the conversation" in a brief or shared file.
5. **Scope is fixed at Step 1.** The target the user names in the invocation is the boundary for all three phases. The architect does not redesign code outside the explorer's scope; the implementer does not edit files the architect didn't touch. Scope changes require an explicit user-confirmed pivot, not in-flight expansion.
6. **Checkpoint via a delegated commit before architecture and before refactoring.** Implementation can destroy work; commits are the safety net. The commit dispatch is bundled with the upcoming substantive dispatch and does not require its own pause.

## Sub-agent context boundaries

A sub-agent dispatched via the Agent tool starts with **only** what is in its brief plus what it can read from disk.

**A sub-agent CAN see:** the brief text, files it Reads/Globs/Greps, its own tool outputs, web content if its toolset includes WebFetch/WebSearch.

**A sub-agent CANNOT see:** the parent conversation, conversation-attached images, the orchestrator's memory, prior tool outputs, the TaskList or Plan state.

If the user shared an image inline that's load-bearing for the refactor, resolve it to an absolute path (Claude Code auto-saves pasted images to `~/.claude/image-cache/<session-uuid>/<N>.png`; resolve the session UUID with `ls -t ~/.claude/image-cache/ | head -1`) and **also** describe its load-bearing content in prose inside `01-context.md`. Never reference "image N", "the screenshot above", "the attached PNG" in a brief or shared file.

## Protocol

### Step 1 — Restate, scope, slug
Write a one-paragraph restatement of the refactor goal. Pick the target scope (a crate path, a package, a module, a directory). Pick a `<slug>` kebab-case derived from the target (e.g. `refactor-clouds-pass1`, `refactor-fog-volumes`). Output this in chat as a short block. Do not start any work yet.

If the user invoked `/refactor` with no argument, ask which target.

### Step 2 — Architectural Q&A
Use the `AskUserQuestion` tool. Ask 1–3 load-bearing questions before any agent fires. Calibrate count to scope:

- Trivial / small module: 1 question.
- Mid-size: 2 questions.
- Large / cross-cutting: 3 questions.

Useful question shapes:
- **Scope boundary** — "Is the target just `<path>`, or does it include `<adjacent path>`?"
- **Architectural anchor** — "Which architectural doc / canon source defines the target shape (e.g. `docs/architecture/<X>.md`, a research paper at `docs/research/<Y>.md`)? If none, the architect proposes from first principles."
- **Forbidden moves** — "Anything off-limits (public API breakage, file moves, dependency changes, test rewrites)?"
- **Verification gates** — "Which gates must pass after refactoring (e.g. `cargo test --workspace`, `unity-cli test --mode EditMode`, manual visual verification)?"

Never ask the user to confirm what you already decided. Ask things whose answers would change the agent briefs.

### Step 3 — Write the shared-context files
Create under `docs/orchestrate/refactor-<slug>/`:

- `README.md` — index: list of files, phase checklist with status markers (`[ ]` / `[x]`), one-line summary of the goal.
- `01-context.md` — the canonical context bundle every agent reads first. Contents:
  - Restated goal (verbatim user words quoted where load-bearing).
  - Target scope: exact file paths / directory globs.
  - User constraints from the Q&A (cite the question + chosen option).
  - Architectural anchor: doc paths / research files / "first principles" if none.
  - Verification gates: exact commands to run after edits.
  - Forbidden moves: API breaks, file moves, dependency changes, anything off-limits.
  - Project conventions worth quoting (CLAUDE.md excerpts that bind the refactor).
- `02-exploration.md` — created by the explorer. Empty stub at this step (just a section heading).
- `03-architecture.md` — created by the architect. Empty stub.
- `04-refactoring.md` — created by the implementer. Empty stub.

Each file is **self-contained**: code refs not paraphrases, no "see other file" without inlining the load-bearing fact.

### Step 4 — Dispatch the explorer
Brief the `refactor-explorer` agent. The brief must contain, verbatim:

1. The full restated goal.
2. The target scope (paths).
3. **Required first action:** read `docs/orchestrate/refactor-<slug>/01-context.md` in full.
4. **Required last action:** Write findings to `docs/orchestrate/refactor-<slug>/02-exploration.md` under the heading `## refactor-explorer findings (<ISO date>)`. Final assistant message is for status only.
5. The deliverable shape: prioritized findings table (severity / location / smell-type / one-line description) followed by 3–7 expanded entries with current state, why-it's-a-problem, and suggested direction (not full design).

### Step 5 — Synthesis pause #1
After the explorer returns:

1. Verify it appended to `02-exploration.md`. If not, dispatch a follow-up agent to do so — never write the missing content yourself.
2. Update `README.md`'s phase checklist: `[x] exploration`.
3. **Pause and submit.** In chat:
   - One short paragraph summarizing the findings.
   - The path to `02-exploration.md`.
   - Anything surprising / contradicting the user's stated goal.
   - The proposed next step: dispatch `refactor-architect` to design fixes for findings #1, #2, #3 (or whichever subset). Phrased as a proposal.
   - Explicit ask: "Confirm to dispatch the architect on findings [N], redirect, or stop here?"
4. **Wait for the user.** If they redirect, answer in chat (still no dispatch) until they confirm.

### Step 6 — Checkpoint commit, then dispatch the architect
**Before dispatching the architect**, dispatch a `general-purpose` commit sub-agent with this brief:

> Invoke the `/commit` skill to commit all current changes (staged, unstaged, untracked) as a single checkpoint. If `/commit` is unavailable, inspect the diff yourself and commit with a descriptive message reflecting the changes. Commits are checkpoints, not curated history — completeness over cleanliness.
>
> **Commit-only scope. Do NOT:** run recompile / refresh / build / test / lint / format steps; read or open code files to "verify"; push to any remote. Ignore project CLAUDE.md rules that demand post-edit recompile / build — those apply to whoever made the edit, not to a checkpoint.
>
> Return only the commit SHA and a one-line subject. Do not summarize the diff back to me.

Then dispatch the `refactor-architect` agent. Brief contents:

1. The full restated goal.
2. **Required first action:** read `docs/orchestrate/refactor-<slug>/01-context.md` and `02-exploration.md` in full.
3. The subset of findings to design for (cite by number from `02-exploration.md`).
4. **Required last action:** Write the design to `docs/orchestrate/refactor-<slug>/03-architecture.md` under the heading `## refactor-architect findings (<ISO date>)`.
5. The deliverable shape: target-state architecture (module/type/function shape), migration steps (ordered, granular), explicit "what stays / what changes / what's removed" lists, code refs as `path/to/file.ext:line`.

### Step 7 — Synthesis pause #2
After the architect returns:

1. Verify it appended to `03-architecture.md`.
2. Update `README.md`'s phase checklist: `[x] architecture`.
3. **Pause and submit.** In chat:
   - One short paragraph summarizing the design.
   - Path to `03-architecture.md`.
   - Highlight the migration-step count and any user-impacting risks (API break, behaviour change, test rewrite).
   - The proposed next step: dispatch `refactor-implementer` to execute steps [1..N]. Phrased as a proposal.
   - Explicit ask: "Confirm to dispatch the implementer, redirect, or stop here?"
4. **Wait for the user.**

### Step 8 — Checkpoint commit, then dispatch the implementer
Dispatch the same checkpoint commit sub-agent as in Step 6.

Then dispatch the `refactor-implementer` agent. Brief contents:

1. The full restated goal.
2. **Required first action:** read `docs/orchestrate/refactor-<slug>/01-context.md`, `02-exploration.md`, and `03-architecture.md` in full.
3. The migration steps to execute (cite by number from `03-architecture.md`). Default: all of them. The user may have narrowed.
4. The verification gates to run after each step (from `01-context.md`).
5. **Required last action:** Write a step-by-step execution log to `docs/orchestrate/refactor-<slug>/04-refactoring.md` under the heading `## refactor-implementer log (<ISO date>)`. Each step gets: what was edited (file:line), gate output (pass/fail), notes if a gate failed and what was done about it.
6. Hard rule: if any verification gate fails and cannot be resolved within the step's scope, stop, write the failure to `04-refactoring.md`, and return. Do not proceed to the next step. Do not commit. Do not invent a fix outside the architect's design.

### Step 9 — Synthesis pause #3 (final)
After the implementer returns:

1. Verify it appended to `04-refactoring.md`.
2. Update `README.md`'s phase checklist: `[x] refactoring`.
3. **Pause and submit.** In chat:
   - One short paragraph summarizing what was changed and which gates passed.
   - Path to `04-refactoring.md`.
   - Any failed step and the partial-completion state.
   - Proposed next step: commit the refactor work (delegated), or iterate on a failed step, or stop.

### Step 10 — Exit
The mode ends when the user signals done or all three phases are `[x]`. Leave `docs/orchestrate/refactor-<slug>/` intact — it's the durable artifact. Do not delete or condense it on exit unless asked.

## Agent brief template

```
You are working as part of a delegated refactor orchestration. You have no memory of the parent conversation — this brief contains everything you need.

# Goal
<full restated goal, verbatim>

# Target scope
<exact paths / globs>

# Required reading (in order)
1. docs/orchestrate/refactor-<slug>/01-context.md
2. docs/orchestrate/refactor-<slug>/<this-agent's-group-file>.md
3. <any prior phase's group file, if applicable>
4. <any other repo files with line ranges>

# Your task
<concrete, single-paragraph task statement>

# Constraints
- <inlined user constraints from the Q&A>
- <inlined forbidden moves>
- <inlined verification gates, where applicable>

# Deliverable
- <exact shape>
- Append your output under "## <agent-name> findings (<ISO date>)" in docs/orchestrate/refactor-<slug>/<group-file>.md before returning.

# Hard rules
- Do not skip the required reading.
- Do not invent files, symbols, or line numbers — verify with Read or Grep.
- Do not return your deliverable only as the final message — Write it to the group file first.
- Stay inside the target scope.
```

## Anti-patterns

- **"It's just a small refactor, I'll skip the explorer"** — defeats the skill. The explorer's value is forcing concrete enumeration before any design work.
- **Skipping the architecture phase and going straight to implementation** — the implementer's brief depends on the architect's migration steps. Without them the implementer freelances and breaks the scope contract.
- **Chaining dispatches without a pause** — the user must confirm each phase boundary. "Obvious" next steps are exactly where drift from intent happens.
- **Orchestrator reading source files to "summarize" findings for the user** — read the group file, summarize that. If the file lacks the detail you'd need to summarize, dispatch a follow-up agent to add it.
- **Implementer expanding scope past the architect's design** — if a needed change wasn't designed, stop and re-enter the architect phase. Don't invent design in the implementer.
- **Conversation-relative references in shared files** — "image N", "the screenshot above", "as discussed", "the file we Read earlier". Sub-agents resolve none of these. Replace with prose or absolute paths.
- **Letting an agent return its deliverable only as text** — orchestrator never extracts content from agent return messages; only files on disk are load-bearing. Every brief mandates "Write/Edit to <group file>" and the orchestrator verifies the file actually changed.

## Non-overlap with sibling skills

| Skill | Domain |
|-------|--------|
| `/sniff` | Readability friction (anonymous tuples, magic numbers, weak types). One-shot find-and-fix top-5 loop. No design phase. |
| `/dry` | SOLID / DRY violations, design-pattern misuse. One-shot find-and-fix. |
| `/deadcode` | Zero-caller items. One-shot delete. |
| `/enforce` | Crate boundaries, dead public APIs, layer contracts. |
| `/delegate` | General multi-agent orchestration with re-implementation audit + open-ended phases. Use when the work isn't specifically a refactor. |
| **`/refactor`** | **Three-phase orchestrated refactor: exploration → architecture → implementation, with user-gated phase boundaries.** Use when the change is structural and benefits from explicit smell-list → design → applied-edits separation. |
