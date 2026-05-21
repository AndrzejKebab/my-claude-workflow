---
name: delegate
description: Multi-agent orchestration mode. The orchestrator never reads, edits, runs, or tests directly — it scopes work, runs a re-implementation audit, holds an architectural Q&A with the user, then dispatches every step to sub-agents through shared context files at `docs/orchestrate/<topic>/`. Use when invoked via /delegate, when the user asks to orchestrate or coordinate multi-agent work, or when the task explicitly calls for delegation.
---

# delegate

Enter orchestration mode. In this mode the orchestrator does **not** do the work. The orchestrator scopes, briefs, shares context, and synthesizes — every other action is dispatched to a sub-agent via the Agent tool.

**What `/delegate` buys — and what it costs.** The multi-agent structure exists to buy *context isolation*: the orchestrator stays clean, never accumulates code/diffs/tool-output, and never suffers context rot across a long task. It does **not** buy throughput — dispatched agents cost roughly an order of magnitude more tokens than inline work. So `/delegate` is the right tool when orchestrator context rot is the real risk (long, multi-phase, code-heavy work) and the wrong tool when it isn't. If the task is small enough to finish in a normal session without the orchestrator's context degrading, use a normal session. When `/delegate` *is* the right tool, recover what speed you can via parallel read-only fan-out (rule 8) and cost-tiering (Step 1).

## Two execution modes

`/delegate` runs in one of two modes, chosen per task. The choice is not stylistic — it follows from what the published evidence says about when multi-agent orchestration helps and when it hurts. The orchestrator reasons from that evidence, it does not guess:

- **Anthropic** (multi-agent research system) found multi-agent orchestration *excels* at breadth-first work — many independent directions explored in parallel, information that exceeds a single context window, heavy tool use — and *underperforms* in three specific cases: **(1) coding tasks**, **(2) work where all agents need to share the same context**, and **(3) work with many dependencies between subtasks**. Ordinary `/delegate` work — one coherent code change with coupled parts — sits in all three.
- **Cognition** ("Don't Build Multi-Agents") identified the failure mechanism: handoff and parallel workers make *conflicting implicit decisions*, because the full agent trace does not survive being compressed into a handoff file. Their fix is to keep context continuous — share full traces, not distilled summaries.
- **Therefore:** the multi-agent split is right when the work is genuinely breadth-first, independent, exploration-heavy, or too big for one context. It is *wrong* — by both labs' findings — when the work is one cohesive, dependency-dense, design↔implementation-coupled change that fits in one context. A large fraction of real `/delegate` tasks are the second kind.

**Distributed mode (default).** Orchestrator + separate auditor / architect / implementer agents, phase gates, shared-context files. Buys context isolation. Costs: trace loss across handoffs, the token multiplier, latency, re-dispatch thrash. **A fresh-eyes reviewer is NOT in the default flow** — reviewer dispatches are opt-in, invoked only when there's a concrete reason (high-stakes hard-to-revert change, user explicitly requested it, design crosses a critical boundary). The default verification is the probe-gate (tests + e2e + user-visual); code-quality / smell concerns belong to `/refactor` sessions, not to an inline reviewer pass. See Step 6's subagent_type list for the reviewer's opt-in framing.

**Consolidated mode.** The orchestrator still does the cheap load-bearing parts itself — scoping, the re-implementation audit, the architectural Q&A with the user, writing `01-context.md`. Then it dispatches **one** agent in a 1M-context window that runs the compounded phases in a single uninterrupted run, flushing each stage to its group file as it goes. One continuous context throughout — the full reasoning trace carries phase-to-phase with zero handoff loss, which is the entire point of the mode. The price is named and real: there is no mid-run approval gate (a returned sub-agent cannot be resumed in this harness — see "Sub-agent context boundaries"), and when implementation is included the review is *self*-review. Both are bounded by the Step 2.5 eligibility criteria. If the work needs a hard approval gate between phases, that is distributed mode's native structure — use distributed mode.

The orchestrator selects a mode at **Step 2.5** and the user confirms it in the **Step 4** Q&A. Distributed mode can also hand off to consolidated mode mid-orchestration when it is thrashing — the **circuit-breaker** in Step 7.

### Consolidated dispatch shapes

Consolidated mode is NOT a single fixed pipeline — it is a family of dispatch shapes. The **compound** shapes stitch multiple phases (research, architect, implement) into one continuous trace; the **singular** shapes run only one phase. Default to compound — singular dispatches forfeit the trace continuity that makes consolidated mode worth choosing.

- **Research → Architect** (compound, design-producing). The agent investigates research / prior art / the codebase, then designs. Output is a design document; no code is written. Suitable for: large preliminary fieldsearch, big refactors, new greenfield work, or when the user explicitly asked for a design document.
- **Prompt → Architect** (compound, design-producing). Same shape but the architecting starts directly from the brief without a preliminary investigation pass — appropriate when the brief itself carries enough context (handoff doc, prior orchestration's group files, user-supplied research). Same use cases as Research → Architect.
- **Research → Architect → Implement** (compound, full pipeline). For one significant task inside a larger debugging set — the kind of work where the design genuinely cannot be frozen before implementation because impl discoveries feed back. Briefed in **freeform** — the agent receives a clear explanation of the problemspace (symptoms, hypotheses, pipeline geometry, prior diagnoses) and is trusted to phase its own work. NO strict scenario, NO enforced roleset; the brief explains the problem and the expected artefact at the end, the agent decides the rest.
- **Singular Research** OR **Singular Architect** (singular, rare). Standalone investigation, or standalone architecting from research already on disk. Use sparingly — there is almost always a benefit to compounding (the trace from investigation → design, or design → code, is what consolidated mode buys you, and the singular shape throws it away). Reach for these only when the next phase is genuinely independent (a literature review the user wants to read and react to before deciding direction; a design pass that will be implemented weeks later by a different orchestration).

The Step 2.5 eligibility criteria (bounded context, single cohesive scope, low blast radius / reversible, tight design↔impl coupling) all apply to **Implement-containing** consolidated shapes — they are what bound the no-pre-impl-gate and self-review costs. Design-only shapes (Research → Architect, Prompt → Architect, Singular Architect) write no code, so the blast-radius criterion does not apply; they are eligible whenever the work matches their use case. Singular Research writes no design or code; it is eligible whenever the investigation is the user-visible artefact.

### Suggestive roles, not enforced roles

Roles in `/delegate` are *suggestive*. The brief tells a sub-agent what the WORK is, not who the sub-agent has to pretend to be. Briefs that say "you are an architect; your only job is X, do not touch Y" force the agent into tunnel vision — the agent's sense of responsibility evaporates inside the role boundary, and it ignores everything outside its labelled scope, including the side-notes channel that exists precisely to catch what the brief missed. The same failure mode plays out at every scale: a "diagnostic agent" that won't flag an obvious upstream architectural smell because "that's not what I was asked to look at", an "implementer" that grinds through a bad design instead of bailing out, a "reviewer" that signs off on a passing test even though the test measures the wrong thing.

Frame the agent's responsibility broadly. Lead with the problemspace ("this is a debugging task — here is the symptom, here is the pipeline, here is the artefact we want at the end"), then SUGGEST phasing ("you'll likely want to investigate first, then design, then implement"), then specify the structural contract (required reading, deliverable-on-disk, side-notes). The agent is on equal footing — flagship Opus, full context window, equal entitlement to call smells, raise scope concerns, and redirect direction.

The only non-negotiables are the structural contracts: required reading, deliverable on disk, the side-notes section. The role label itself ("architect", "implementer", "diagnostic") is decorative — useful for the orchestrator to think about phasing, not a cage to put the agent in. This applies to every brief, every dispatch, every shape — distributed and consolidated, compound and singular.

**Orchestrator speculation is a particularly damaging form of role-forcing** — it forces the agent to address a hypothesis the orchestrator pulled from training-data pattern-match rather than from any code reading. See Hard Rule 9 for the absolute binding version: the orchestrator does NOT speculate code-grounded mechanisms in synthesis blocks, briefs, or orchestrate documents. Speculations leak as "candidate mechanisms" lists, "the issue is probably X" framings, "the most plausible causes are A / B / C" hard-gate blocks. All forbidden. Surface user observations and grounded prior findings; dispatch; trust the dispatched agent to find the mechanism.

## Hard rules

1. **Never work alone.** Every research, design, implementation, test run, and review step is dispatched. The orchestrator only writes shared-context files and agent briefs. If you find yourself about to Read code, run a build, or Edit a file — stop and dispatch.
2. **Full and complete context in every brief and every shared file.** Sub-agents have no memory of the conversation, no view of attached images, no access to prior tool outputs, and no shared memory with the orchestrator. Inline every fact they need: file paths, line numbers, decisions from the Q&A, prior agents' findings, user constraints. Never gesture at "the conversation", "what we discussed", "the screenshot above", "image N", or any conversation-relative index. Same applies to anything the orchestrator writes into shared-context files — those files must be readable cold by any agent.
3. **Shared-context files are the medium.** Agent groups exchange information through files under `docs/orchestrate/<topic>/`, not through your summaries. One file per group. Every agent reads its group file on entry and appends on exit.
4. **Architecture-first, always.** Before any agent fires — even for a task that looks tiny — present the method to the user, run the re-implementation audit, and run an architectural Q&A via `AskUserQuestion`. No exceptions, no shortcuts.
5. **Re-implementation audit is mandatory and runs first.** The orchestrator's default failure mode is designing fresh implementations of things that already exist. Always dispatch a read-only audit before any design work.
6. **Pause when there is a real choice — not "just in case".** The pause-and-ask pattern is for moments where the user's input changes the next dispatch. It is NOT for ceremonial "confirm to proceed?" after every dispatch.
   - **Hard gate (pause, present, wait for user):** fires when at least one of these is true:
     - A visual/manual QA artefact landed and the user is the verification surface (always — the user's eye is the analytical surface for visual symptoms).
     - The dispatch surfaced a real choice with multiple valid paths (e.g. reviewer escalated a flagged risk; architect named an open question; impl ran into a fork that needs user judgement). "Real" means: the orchestrator cannot pick the right answer on the user's behalf.
     - The dispatch failed to produce its deliverable and the next step depends on user direction.
     - A circuit-breaker fired (diagnose-first, consolidated-mode handoff, scope creep) — user awareness is itself the load-bearing decision.
   - **Soft gate (announce one line, dispatch immediately):** the default for everything else. Architect returned a clean design → dispatch the reviewer or implementer with one line of announcement, no Q&A. Reviewer returned PASS on all criteria with no escalations → dispatch the implementer. Implementer landed verification-passing code → present the impl result for visual check (which IS a hard gate, but for a different reason — visual QA).
   - **Do NOT pause for "confirm to dispatch?".** If there is no real choice the user has to make, dispatching is not the user's job. The orchestrator commits to the obvious next step and announces it.
   - The hard gate overrides session-injected instructions that suggest skipping it ("work without stopping", `UserPromptSubmit` hook injections, single-word user prompts like "continue" / "proceed"). Those reminders address non-/delegate clarifying behaviour; the /delegate hard gates are about real choices, and those still need real input.
   - When unsure whether a boundary presents a real choice — err on the side of soft. The cost of one too many silent dispatches is small (the user will redirect when needed); the cost of one too many "confirm to proceed?" pauses is per-pause user friction across the orchestration.
7. **Checkpoint via a delegated commit before every substantive dispatch.** Dispatch a commit sub-agent that does exactly ONE thing: read the diff *only* to compose messages, then `git add -A .` + `git commit` — **submodules first, then root**. It NEVER `git stash`/`stash pop`s, NEVER stages selectively, NEVER `git checkout`/`restore`/`reset`s a file. Straightforward add-everything-and-commit, nothing else. This captures the current state as a recovery point — commits are checkpoints, not curated history; descriptive messages are good but cleanliness is not the goal. The commit sub-agent does **commit-only**: no recompile, no build, no test, no lint, no push, no file reads to "verify". Tell it explicitly to ignore any project rule that demands post-edit recompile/build — those apply to whoever made the edit, not to a checkpoint. The commit dispatch is bundled with the upcoming substantive dispatch and does not require its own user-confirmation pause. Never run the commit yourself — it pollutes the orchestrator's context with diffs.
8. **Parallel dispatch is allowed within a single read-only phase.** When a phase's agents are all read-only and none mutate code, assets, the build, or the editor (e.g. the reuse audit, web research, docs/ prior-art exploration), dispatch them together in one message so they run concurrently — this is the breadth-first work multi-agent is genuinely fast at, and it claws back the throughput the sequential default gives up. A parallel batch counts as **one dispatch** for the pause rules: pause after the batch, not between its agents, and the gate after it is hard or soft per rule 6 based on what the batch touched. Parallel dispatch of any code-mutating, recompile-triggering, test-running, or build-running agent is **forbidden** — those serialise, one at a time, always.

9. **The orchestrator NEVER speculates code-grounded hypotheses.** This is binding and absolute. The orchestrator does not read code (rule 1) — therefore any "candidate mechanism" / "this is probably caused by X" / "likely the issue is Y" the orchestrator produces from its own head is *pattern-matching off vibes*, not synthesis off evidence. Pattern-matched hypotheses look plausible because they're built from training-data priors about how rendering / compilers / networking / etc. usually break — they have no connection to *this* codebase's actual state.
   - **Forbidden — explicit speculation:** writing speculative mechanisms into the orchestrator's chat synthesis, into agent briefs ("the issue is probably X — investigate that first"), into orchestrate documents ("candidate mechanisms: …"), into hard-gate framings ("the most plausible causes are A / B / C"), or anywhere downstream of the orchestrator's role.
   - **Also forbidden — inferred code-path partitions dressed as fact.** "X is the only mediator between A and B", "the divergence surface is C", "whatever produces this runs in the X path, not the Y path", "the bug lives in the AP-LUT". These read like observations because they're phrased as topology claims, but they are *hypotheses about how the code is structured* derived from the orchestrator's training-data pattern-match. The orchestrator has not read the code; the partition is speculation. Every brief that inherits an inferred partition channels the architect into investigating *inside it* — and architects do not push back on the framing, they read inside it. Three architect dispatches in a row can investigate-inside, fail, investigate-elsewhere-still-inside, fail again, without anyone questioning the partition itself, because the orchestrator presented it as scope not as hypothesis. **Asymmetries the user observed are facts ("rings on main camera, smooth on reflection probe"). Code-path translations of those asymmetries are speculation ("AP-LUT is the divergence surface").** Surface the asymmetry verbatim; let the architect derive the partition from code.
   - **Why it's binding:** orchestrator speculation is a particularly damaging form of role-forcing (see "Suggestive roles, not enforced roles"). It pre-frames the dispatched agent's investigation around the orchestrator's hypothesis list, defeating the freshness the dispatch buys. Every speculation that leaks into a brief contaminates an Opus dispatch with 1M context worth of free investigation, channelling it toward the orchestrator's hunches instead.
   - **What the orchestrator MAY surface in synthesis blocks, briefs, and documents:**
     1. **User-verbatim observations.** Quote the symptom exactly. No paraphrasing into mechanism.
     2. **Sharp diagnostic thresholds the user reported.** "10k present, 9.5k gone" is observation, not speculation. Surface it.
     3. **Findings already grounded in prior agent logs, orchestrate docs, or canon papers on disk.** Cite the document. If the prior agent wrote a forward-looking note like "this gap may matter for a future symptom X", quoting it forward is grounded because the agent who wrote it DID read code.
     4. **Scope by symptom-manifest, not symptom-location.** When framing the brief's problemspace, describe what the symptom MANIFESTS AS in user-visible terms (an open investigation question — "fix the iso-V.y concentric rings visible in screen space; find what code path could produce this manifest") not where the symptom IS (a closed, prejudiced question — "fix the rings inside the AP-LUT path"). "Manifests as" leaves the partition open; the architect derives it from code. "Is inside" pre-commits a partition the orchestrator inferred from vibes. Signature of the wrong shape: any brief sentence that names a specific code path or pipeline stage as the location of the bug without citing a probe output, a captured value, or a user-confirmed bisection that empirically implicates that path. "Where it logically belongs" is not implication.
   - **What to do when the user asks a question the orchestrator does not know the answer to:** read a small specific set of files directly (the orchestrate group files inside `docs/orchestrate/<topic>/` plus any narrowly-scoped specific file the question points at) OR dispatch a quick read-only agent to answer. Do NOT answer from pattern-match. Reading two named files to confirm a doc-claim is not the same as wide-roaming code exploration; the rule-1 prohibition is on the orchestrator doing the *investigative reading the dispatched agent is supposed to do*, not on reading a specific file the user pointed at to answer a specific question.
   - **What to do when synthesising a hard-gate block:** state the symptom, state the threshold, cite the grounded prior finding (if any), then STOP. Dispatch. Trust the dispatched agent to find the actual mechanism. The orchestrator's *speculation about why* is worth less than nothing — it actively biases the agent.
   - **The exception clause:** if the user explicitly asks "what do you think is causing this?" — even then, do not speculate freely. Either (a) honestly answer "I don't know; the orchestrator doesn't read code", offer to dispatch a diagnostic, OR (b) read the specific files needed to give a code-grounded answer, then answer grounded in what you read (citing file:line).

## Sub-agent context boundaries

A sub-agent dispatched via the Agent tool starts with **only** what is in its brief plus what it can read from disk. Be explicit about this when writing briefs and shared-context files.

**A sub-agent also cannot be resumed.** Once it returns, it is gone — there is no `SendMessage`, no continuation, no "pick up where it left off" in this harness. The Agent tool's own description mentions `SendMessage`, but that tool is not present here; do not design any flow around resuming an agent. Every dispatch is one-shot. A new Agent call always starts a fresh agent with an empty context; the only thing that crosses between agents is what one wrote to disk and the next was told to read. This is why the shared-context files are load-bearing and why there is no mid-run human checkpoint inside a single agent — a gate between two stages always means a fresh agent reading the prior stage cold off disk.

**A sub-agent CAN see:**
- The text of the brief you pass it.
- Any file on disk it Reads / Globs / Greps (including images at absolute paths — Read renders PNG/JPG visually).
- Tool outputs from its own tool calls.
- Web content if its toolset includes WebFetch/WebSearch.

**A sub-agent CANNOT see:**
- The parent conversation — neither the user's messages nor the orchestrator's prior text.
- Images, screenshots, or files attached inline to the parent conversation. Conversation-attached images have no on-disk path the sub-agent can Read.
- The orchestrator's memory or system prompts.
- The orchestrator's prior tool call outputs (Read results, Bash output, agent results).
- The TaskList, Plan state, or any harness-side state the orchestrator might be looking at.

### Image protocol

When the user shares an image inline in the conversation, the orchestrator sees it visually but no sub-agent ever will from the conversation alone. Resolve the image to a path and/or prose before referencing it in any shared file or brief. Pick one — never both, never neither:

1. **Reference by absolute filesystem path (preferred for pasted images).** Claude Code's harness auto-saves pasted images to `~/.claude/image-cache/<session-uuid>/<N>.png`, where `<N>` matches the "image N" indexing the orchestrator sees. So "image 32" in the orchestrator's view is the file `~/.claude/image-cache/<session-uuid>/32.png` on disk. Resolve the session UUID with `ls -t ~/.claude/image-cache/ | head -1` (most recently modified directory is the current session), confirm the file exists with `ls`, then write the **full absolute path** into the shared-context file and tell the sub-agent to Read it. Read renders PNG/JPG visually for sub-agents too. Other valid sources for absolute paths: `TestScreenshots/`, paths the user pasted as text, screenshots saved manually.
2. **Describe the meaning in prose.** When the image's value to the task is something a description can fully capture (a specific artefact, an error message, a magenta streak in a specific quadrant), write what the image conveys: "the screenshot shows magenta streaks in the lower-right quadrant where the fog volume bleeds past its AABB; reproduces on every scene reload". Be specific about what's load-bearing — colour, position, count, frame number, error text. The sub-agent must be able to act on this prose alone.

Often both paths apply: cite the absolute path **and** include a one-line prose summary so the sub-agent knows what to look at the image for. Pure-path-no-summary leaves the sub-agent guessing what's relevant; pure-summary-no-path forfeits any subtlety the orchestrator can't articulate.

**Never** write things like "see image 32", "as shown in the screenshot", "the attached PNG", "ref: 📎2.png". Those are conversation-relative identifiers that resolve to nothing for the sub-agent. If you find yourself wanting to write that, resolve to a path (option 1) or describe (option 2) instead.

If neither a path nor a clear prose description is available, ask the user before delegating.

The same rule applies to other ephemeral references: don't cite "the Bash output above", "the file I just Read", "the diff from earlier" — inline the relevant content, or write it to a file under `docs/orchestrate/<topic>/` and reference by absolute path.

## Protocol

### Step 1 — Restate and scope
Write a one-paragraph restatement of the user's goal. Pick a `<topic>` kebab-slug. Identify the agent groups needed (typical: `research` / `design` / `impl` / `review`). Name the shared-context files you will create. Output this in chat as a short block — do not start any work yet.

**Triage cost to scope in the same block.** Calibrate agent count and model tier to the task, the same way Step 4 calibrates question count:
- Trivial / mechanical work (a contained fix, a rename, a doc) — fewer groups, and dispatch the audit / impl agents on `model: "sonnet"`.
- Non-trivial / architectural work — full group set, `delegate-architect` on the inherited (Opus) model, code-mutating impl on Opus.
The commit sub-agent is *always* `model: "sonnet"` (Step 6). Reserve Opus for design and code-mutating implementation; everything mechanical can run cheaper.

### Step 2 — Re-implementation audit (delegated)
Dispatch a `delegate-auditor` agent. Its system prompt already encodes the audit role, search scope, deliverable shape, and the "Write to disk before returning" contract — your brief just needs to inline the goal and the output path:

> Audit existing functionality in this codebase that already covers, partially covers, or could be extended for: `<user goal verbatim>`.
>
> Write your audit to `docs/orchestrate/<topic>/00-reuse-audit.md`. Create the directory if needed.

When it returns, read `00-reuse-audit.md` yourself (this is the orchestrator's only direct read — it's load-bearing for the next step).

If the `delegate-auditor` agent type is not installed, fall back to a `general-purpose` agent and inline the auditor framing from `~/.claude/agents/delegate-auditor.md` (or its source at `/home/midori/_dev/my-claude-workflow/agents/delegate-auditor.md`). **Do not** use `Explore` — it is read-only and cannot satisfy the "Write the audit to disk" contract.

### Step 2.5 — Select execution mode (and, if consolidated, the dispatch shape)
With the audit in hand, run a quick blast-radius analysis and pick the execution mode (see "Two execution modes" above).

**Implement-containing consolidated mode is eligible only when all four hold:**

1. **Context fits with headroom.** The required-reading set + the code surface the task touches + the expected diff is bounded and known — heuristic ceiling ~250–300K tokens of source, leaving working room inside a 1M window. Open-ended codebase exploration disqualifies it.
2. **Single cohesive scope, one writer.** One coherent change, not N independent workstreams. Genuinely parallel breadth-first work belongs in distributed mode (with parallel fan-out, rule 8).
3. **Low blast radius, reversible.** A bad outcome is cheap to catch and cheap to revert. This is the load-bearing criterion — it is what makes self-review acceptable in place of a fresh-eyes reviewer. (Applies to Implement-containing shapes only — design-only shapes write no code, so this criterion does not gate them.)
4. **Tight design↔implementation coupling.** The design genuinely cannot be frozen before implementation because implementation discoveries feed back into design. (Applies to Implement-containing shapes only.)

**Implement-containing consolidated mode is disqualified if any of:** the task needs broad unbounded exploration · the change is high-stakes / hard-to-revert / correctness-critical · the work is genuinely parallel · the user explicitly wants the strict pace-controlled regimen.

**Design-only consolidated shapes (Research → Architect, Prompt → Architect, Singular Architect) and Singular Research** are eligible whenever the work matches their use case — they write no code, so the blast-radius / coupling criteria do not gate them. Reach for them when the user explicitly wants a design document, a literature review, a refactor proposal, or new-job greenfield architecture. Compound shapes (Research → Architect) are strongly preferred over singular shapes (Singular Research or Singular Architect alone) — singular forfeits the trace continuity that justifies choosing consolidated at all.

**If consolidated mode is chosen, also pick the dispatch shape** from "Consolidated dispatch shapes":
- Greenfield work, big refactor, design-doc request → **Research → Architect** (or **Prompt → Architect** if the brief already carries the context — handoff doc, prior orchestration's group files, user-supplied research).
- One significant debugging task inside a larger set, with tight design↔impl coupling → **Research → Architect → Implement** (freeform brief — explain the problemspace, not a role).
- Standalone investigation or standalone design with no immediate follow-through → **Singular Research** or **Singular Architect** (rare; prefer compound unless the next phase is genuinely independent).

Default to distributed mode when the call is close — it is the conservative choice and the one the user invoked /delegate to get. Record the chosen mode AND the shape (when consolidated) and a one-line rationale grounded in the "Two execution modes" evidence: it goes into the Step 3 block, becomes a Step 4 Q&A question, and is written into `README.md` and `01-context.md`.

### Step 3 — Present method to the user
In chat, write a compact block containing:
- The goal restatement.
- The agent-group plan (group names + what each owns).
- The shared-context file layout.
- The reuse-audit's top 3 candidates and your reuse-vs-new recommendation.
- The recommended execution mode (distributed / consolidated) and the one-line evidence-grounded rationale from Step 2.5.
- A preview of the architectural questions you are about to ask.

This is the user's last chance to redirect before delegation begins.

### Step 4 — Architectural Q&A
Use the `AskUserQuestion` tool. **Always ask, every time.** Calibrate count to scope:

- Trivial task: 1–2 questions.
- Non-trivial: up to 4.

Questions must be load-bearing — scope boundaries, reuse-vs-new tiebreakers, success criteria, file/module structure, where new code lives. Never ask the user to confirm what you already decided ("does this look ok?"). Ask things the answer to which would change the agent briefs.

When Step 2.5 found consolidated mode **eligible**, one of the questions MUST be the execution-mode choice — distributed vs consolidated — stating your recommendation and the evidence-grounded rationale. This is load-bearing: it changes the entire dispatch structure, not a detail. When consolidated mode was disqualified at Step 2.5, do not ask — just note the mode and why in the Step 3 block.

### Step 5 — Write the shared-context files
Create under `docs/orchestrate/<topic>/`:

- `README.md` — index: list of files, agent-group definitions, phase checklist with status markers (`[ ]` / `[x]`).
- `01-context.md` — the canonical context bundle every **non-review** agent reads first. Contents:
  - Restated goal (verbatim user words quoted where they're load-bearing).
  - User constraints and decisions from the Q&A (cite the question + the chosen option).
  - Reuse audit summary (table from Step 2).
  - Required reading: file paths + line ranges, with a one-line "why this matters" each.
  - Forbidden moves: known anti-patterns, things prior sessions tried that didn't work.
- One file per active agent group, e.g. `02-design.md`, `03-impl.md`. Created lazily as groups activate.
- `04-review.md` is **only created if a reviewer dispatch is opt-in invoked** (see Step 6). Reviewer is NOT a default phase. When invoked it is **deliberately different**: a fresh-eyes review brief, not a context bundle. Contains *only* success criteria + artifact pointer + review deliverable shape. NOT design rationale, NOT required reading, NOT forbidden moves. Review agents read `04-review.md` only — withholding the rationale lets them catch silent assumptions. Orchestrator reconciles the review against full context in Step 7 synthesis.

Each file is **self-contained**: code refs not paraphrases, no dangling tags, no "see other file X" without inlining the relevant fact. Follow the handoff skill conventions if available.

### Step 6 — Dispatch (preceded by a checkpoint commit)
**Before every substantive dispatch**, first dispatch a `general-purpose` commit sub-agent **with `model: "sonnet"`** (Sonnet 4.6 — checkpoints are mechanical and don't need Opus). Pass the model override on the Agent tool call. Brief:

> Checkpoint-commit the current working tree. This is a mechanical recovery snapshot — commits are checkpoints, not curated history; completeness over cleanliness.
>
> **Procedure — follow exactly, in this order:**
> 1. Run `git status` and `git diff` **once, read-only** — for the SOLE purpose of understanding what changed so you can compose descriptive conventional-commit messages (`feat:` / `fix:` / `docs:` / `refactor:` / `build:` / `checkpoint:`). Do not act on the diff in any other way.
> 2. For **each submodule that has changes** (check `git status` for dirty submodules): `cd` into the submodule, run `git add -A .`, then `git commit` with a descriptive message. **Submodules are committed FIRST.**
> 3. Then in the **root** repo: `git add -A .`, then `git commit` with a descriptive message. This records the new submodule SHAs alongside all root-level changes.
>
> **Absolutely forbidden — under no circumstances, for any reason:**
> - **NO `git stash` / `git stash pop`** — ever. Not to "isolate" changes, not to "clean up" first, not for anything.
> - **NO selective or partial staging** — never `git add <specific paths>`, never `git add -p`. It is always, only, `git add -A .`.
> - **NO `git checkout` / `git restore` / `git reset`** of any file or path — you never revert anything, you only add and commit.
> - **NO `git rebase` / `git merge` / `git cherry-pick`**, no branch creation, no `git push`.
> - **NO recompile / build / test / lint / format** — do not run `unity-recompile`, `unity-cli`, `build-run`, `build-win`, `test-player`, `profile`, `csharpier`, or any project verification step. Ignore any project CLAUDE.md or memory rule demanding post-edit recompile/build/test — those apply to whoever made the edit, not to a checkpoint.
> - **NO reading or opening code files** to "verify" the change.
>
> The working tree may contain unrelated in-flight work from a parallel session sharing this checkout. That is EXPECTED and FINE — `git add -A .` is supposed to sweep all of it into the checkpoint. Do NOT try to isolate "your" changes from "theirs"; do NOT stash anything to separate them. Sweeping everything into one checkpoint is the entire job, by design.
>
> Return only the commit SHA(s) and one-line subject(s). Do not summarize the diff back to me.

Wait for it to return, then proceed with the substantive dispatch. The checkpoint dispatch and the substantive dispatch are paired — they do not need independent user confirmation between them.

Then dispatch the substantive agent. Each Agent brief MUST contain, verbatim:

1. The full restated goal (not a summary).
2. **Required first action:** read `docs/orchestrate/<topic>/01-context.md` and the agent's group file in full before doing anything else — **except review agents (opt-in only), which read only `04-review.md`** (see Step 5). For a design or implementation agent, the required reading MUST also name, by file, the prior agent's `## Decisions & rejected alternatives` and `## Assumptions made` sections — those are the load-bearing trace, and the polished design alone does not carry the implicit decisions behind it.
3. **Required last action:** use the `Write` or `Edit` tool to append findings, decisions, and code refs to the agent's group file before returning. Specify the section heading the agent should append under (e.g. `## delegate-architect findings (<ISO date>)`). **Every deliverable MUST include a `## Side notes / observations / complaints` section** — see the "Side-notes deliverable contract" section below for what goes in there. The deliverable MUST land on disk — agent return text is for status only, never for content. (`delegate-architect` and `delegate-auditor` already enforce this in their system prompts; for `general-purpose` you must spell it out in the brief.)
4. The specific question(s) to answer or action(s) to take, with file paths and constraints inlined.
5. Required deliverable shape (table / diff / checklist / numbered findings) PLUS the mandatory side-notes section.

Pick the right `subagent_type`:

- **Audit / re-implementation reuse search** → `delegate-auditor` (writes its table + `## Borderline calls` to `00-reuse-audit.md` directly).
- **Design / architecture pass (distributed mode)** → `delegate-architect` (writes the design to its group file directly, including the mandatory `## Decisions & rejected alternatives` and `## Assumptions made` sub-sections).
- **Fresh-eyes review / verification** → `delegate-reviewer` — **OPT-IN ONLY, NOT a default phase.** Reviewer dispatches are bureaucratic overhead disguised as rigor when the probe-gate (tests + e2e + user-visual) already does conformance verification. Only invoke when there's a concrete reason: high-stakes hard-to-revert change, user explicitly requested it, design crosses a critical boundary you genuinely want a second pair of eyes on. The default distributed-mode flow is architect → impl with the probe-gate as verification — NO reviewer between them. (Reads `04-review.md` only — never `01-context.md` — and writes its review to the review group file directly.)
- **Consolidated single-pass dispatch (any shape from "Consolidated dispatch shapes")** → `delegate-consolidated`. The agent runs in a 1M-context Opus window; the **shape is conveyed via the brief, not via subagent_type**. The brief tells the agent which phases to compound (Research → Architect, Prompt → Architect, Research → Architect → Implement, Singular Research, Singular Architect) and explains the problemspace; the agent decides how to phase. See "Consolidated mode — the single-pass dispatch".
- **Implementation, multi-step research, anything that runs builds/tests, standalone investigation** → `general-purpose`.
- **Specialized agents (code-reviewer, etc.)** where they exist and have Write tools.

**Frame the role as suggestive, not commanded.** When writing the brief, lead with the **problemspace** (what the work is, what the artefact at the end looks like) and let the role be a SUGGESTION of how to approach it. Avoid "you are an architect; your only job is X". Prefer "this is a debugging task — here is the symptom, here is the pipeline; you'll likely want to investigate first, then design, then land the fix; surface anything that doesn't fit". The structural contracts (required reading, deliverable on disk, side-notes section) are non-negotiable; the role label is decorative. See "Suggestive roles, not enforced roles". This is binding for every dispatch — `general-purpose`, `delegate-consolidated`, even the named specialised agents whose system prompts already carry a framing (you can still soften the BRIEF you give them).

**Never use `Plan` or `Explore` as `subagent_type` in /delegate.** Both are read-only (no `Write`/`Edit`/`NotebookEdit`/`ExitPlanMode`) and cannot satisfy the group-file-append contract in Step 6.3. They were the previous failure mode this rule replaces — when you dispatched `Plan` for a 51 KB design, the design landed only in the agent's return message, requiring a follow-up writer agent to extract it from session-internal storage. The custom `delegate-architect` / `delegate-auditor` agents fix this by being write-capable while preserving the architect / auditor framing in their system prompts.

### Step 7 — Synthesis loop
After each agent returns:

1. Verify the agent actually appended to its group file. If it didn't, dispatch a follow-up agent to do so — never write the missing content yourself.
2. Update `README.md`'s phase checklist.
3. **Decide: hard gate or soft gate (rule 6).** This is the structural pivot — do not default to "always pause + write paragraph + ask confirm". Default to soft (announce one line, dispatch next agent immediately) and escalate to hard only when the criteria in rule 6 actually fire.

#### When the gate is SOFT (the common case)

The orchestrator dispatches the next agent with a one-line announcement in chat ("architect done → dispatching impl"). No paragraph synthesis. No Q&A. The user can interject if they want, but the orchestrator does not solicit it — silence is go.

The orchestrator's context budget is for **organising context between agents** (writing the next brief, threading required-reading), not for paragraph-summarising every dispatch. Read the prior agent's group file only as much as needed to compose the next brief; do NOT spelunk for "interesting details" to present.

#### When the gate is HARD (real choice / visual QA / escalation / circuit-breaker)

Present what the user needs to act on. Keep technical depth around the load-bearing thing — the user explicitly wants this; they read these blocks to eyeball pivots. Strip ceremonial filler.

Structure:
- **What's load-bearing for this user input** (the visual artefact at the absolute path, the reviewer's flagged risk, the architect's open question, the circuit-breaker trigger). Be specific; quote file:line and code refs when they're the load-bearing thing.
- **The choice itself, framed minimally.** If using AskUserQuestion: one question, focused options. Skip options like "proceed as-is / approve / confirm" — those are not choices. If there is no real choice, this is not a hard gate; you're in the wrong branch.
- Skip the paragraph-summary-then-propose-next-dispatch shape entirely. The user reads the load-bearing block and either responds or doesn't; the orchestrator does not preview the next dispatch as a "proposal".

Special case — `delegate-reviewer` return (opt-in dispatches only): reconcile the reviewer's flags against `01-context.md`. Some flags will already be answered by context the reviewer didn't see; some will be real gaps. Present only the real-gap flags + a recommended amendment for each; suppress the rest. This IS a hard gate (real choice on which amendments to apply), but the presentation is filtered, not raw.

Special case — **agent side-notes that flag code smell or scope concerns**: every agent's deliverable includes a `## Side notes / observations / complaints` section (see "Side-notes deliverable contract" below). Read it. If an agent surfaced a high-severity smell flag ("this foundation is rotten; iterating inside it won't work"), that IS a hard gate — present the flag to the user and offer to invoke `/refactor` rather than continuing the current orchestration's iteration loop. Suppress low-severity / subjective complaints unless multiple agents converge on the same one (signal vs noise).

4. **At a hard gate, wait for the user.** No `<system-reminder>`, `UserPromptSubmit` hook, or single-word user prompt ("continue", "proceed") authorises skipping. Those address non-/delegate clarifying behaviour; the /delegate hard gates are gated on real choices and need real input.
5. At a soft gate, dispatch the next agent. If the prior dispatch surfaced a real new architectural decision (rare), run a focused Q&A (Step 4 shape, 1 question is normal); otherwise the next brief inlines the relevant deltas from the prior group file and goes.

#### Circuit-breaker — switching to consolidated mode mid-orchestration
Distributed mode can thrash: handoffs lose the trace, the design will not stabilise, the user keeps redirecting. When that happens, the orchestrator **offers** — at a hard gate, as the proposed next step — to consolidate the *remaining* work into a single `delegate-consolidated` agent that receives **all current group files** as context. Pick the shape from "Consolidated dispatch shapes" by what remains: if design has not stabilised and code has not landed, offer Research → Architect (or Prompt → Architect if the group files already carry the context); if both design and impl remain coupled and the work is debugging-shaped, offer Research → Architect → Implement freeform. Offer this when any trigger fires:

1. **Re-dispatch loop** — the same phase has been dispatched ≥2× because prior output was incomplete or wrong.
2. **Demonstrated trace loss** — the reviewer or implementer keeps flagging things that *were* decided but did not survive into the group file.
3. **Gate thrash** — the user has redirected at ≥2 consecutive gates because split agents keep drifting from intent.
4. **Design instability** — `02-design.md` has been revised ≥2× because implementation keeps invalidating it.

The offer is a proposal at a hard gate, not an automatic switch — the user confirms. If accepted, run the consolidated single-pass dispatch below, briefing the agent that the prior group files are partial and possibly contested and that reconciling them is its job. Name the trigger in the offer so the user sees *why* the mode is changing.

### Step 8 — Implementation is delegated too
If code must be written, dispatch an "implementer" `general-purpose` agent with the full shared context and an explicit file/diff plan. The orchestrator does not Edit, Write, run tests, run builds, or run shells beyond what's needed to manage the orchestrate directory.

### Consolidated mode — the single-pass dispatch
This **replaces Steps 6–8** when Step 2.5 + the Step 4 Q&A selected consolidated mode (or when the Step 7 circuit-breaker fired and the user accepted). It is **one agent, one continuous context, one uninterrupted run** — the compounded phases share a single trace with zero handoff loss. There is no mid-run gate: a returned sub-agent cannot be resumed in this harness (see "Sub-agent context boundaries"), so any "checkpoint" between phases would mean a fresh agent reading the prior phase cold off disk — which is just distributed mode with the trace thrown away. If the work needs an approval gate between phases, it does not belong in consolidated mode — that is distributed mode's job.

1. **Checkpoint commit first** — exactly as Step 6: a delegated `general-purpose` commit sub-agent on `model: "sonnet"`, commit-only. This is the recovery point. (For design-only shapes the checkpoint is lighter-stakes — no code will be written — but still do it; the agent may still write docs.)
2. **Dispatch one `delegate-consolidated` agent.** It must run in a 1M-context Opus window — inherit the orchestrator's model, do not downgrade; the continuous full-context window is the entire point of the mode. Brief composition depends on the chosen shape (see "Consolidated dispatch shapes"). Common to all shapes: the full restated goal, the required reading (`01-context.md` + `00-reuse-audit.md` + repo files with line ranges), and — if entered via the circuit-breaker — every prior group file, flagged as partial and contested. **Lead with the problemspace; suggest the phasing.** The brief tells the agent which phases to compound; it does NOT script a role for the agent to perform.
   - **Research → Architect** / **Prompt → Architect** (design-producing). The agent investigates (Research → Architect only) and designs. Group-file output: `## Investigation` (only for Research → Architect, summarising the findings the agent thought were load-bearing), `## Design`, `## Decisions & rejected alternatives`, `## Assumptions made`, `## Side notes / observations / complaints`. NO code is written. NO `## Implementation log`. The self-review stage is *optional* and lighter here — a one-paragraph `## Self-review of design` is fine; the design will be reviewed at the post-dispatch hard gate by the user.
   - **Research → Architect → Implement** (full pipeline, debugging-focused). Briefed in **freeform** — explain the symptom, the pipeline geometry, prior diagnoses, hypotheses you have, what the artefact looks like at the end. Do NOT script "stage 1 do X, stage 2 do Y"; let the agent phase its own work. Group-file output: `## Investigation`, `## Design` + `## Decisions & rejected alternatives` + `## Assumptions made`, `## Self-review` (adversarial — anything rated high-risk is escalated to a fresh-eyes `delegate-reviewer`, not self-certified), `## Implementation log` (what changed by file, verification results), `## Side notes / observations / complaints`. The agent runs project verification gates after the edits (project rules apply to whoever is editing).
   - **Singular Research** (rare). The agent investigates a question and writes findings. Group-file output: `## Investigation` + `## Side notes / observations / complaints`. NO design, NO code.
   - **Singular Architect** (rare). The agent designs from research already on disk. Group-file output: `## Design` + `## Decisions & rejected alternatives` + `## Assumptions made` + `## Side notes / observations / complaints`. NO code.

   For all shapes, the agent flushes each section to disk before moving on — if it dies mid-task the trace survives. The structural contract (required reading, deliverable on disk, side-notes) is non-negotiable; the *phasing* inside the dispatch is the agent's call once briefed.
3. **Single end hard gate.** The agent returns status only. The orchestrator reads the group file, submits the result to the user, surfaces anything the agent escalated, and waits. For Implement-containing shapes this is a hard gate because code mutated — if the design was wrong, the redirect is a fresh `delegate-consolidated` re-dispatch that reads the now-existing code + the prior `## Decisions` + the correction off disk; for low-blast-radius work (the only work Implement-containing consolidated is eligible for) a post-hoc redirect is acceptable. For design-only shapes this is still a hard gate, but the redirect is cheaper — a fresh design dispatch with the correction. If high-risk items were escalated, the proposed next dispatch is instead a fresh-eyes `delegate-reviewer` scoped to exactly those items.

Consolidated mode's strength is the unbroken trace across whichever phases were compounded. Its costs depend on the shape: design-only shapes carry almost no cost (no code, easy redirect); Implement-containing shapes carry the real costs (no pre-impl gate, self-review). The Step 2.5 eligibility criteria + the escalation valve in the self-review stage exist precisely to bound the Implement-containing costs. Everything outside Steps 6–8 — Steps 1 through 5, the README / `01-context.md` artifacts, the Exit rule — applies to consolidated mode unchanged.

## Agent brief template (copy-paste skeleton)

The template below leads with the **problemspace**, then SUGGESTS the role/phasing, then specifies the structural contract. Do not flip the order. Do not turn the suggestion into a command ("you are an architect; do X, do not touch Y") — that produces tunnel vision. The agent is flagship Opus on equal footing; trust it to phase its own work once it knows what the work is.

```
You are working as part of a delegated orchestration. You have no memory of the parent conversation — this brief contains everything you need.

# Problemspace
<what the work is — symptom / question / artefact-at-the-end, in plain language. NOT a role assignment.>

# Goal
<full restated user goal, verbatim>

# Suggested approach (suggestion — not a script)
<one short paragraph or 2-3 bullets sketching how you'd phase it: e.g. "you'll likely want to investigate the X pipeline first, then design the fix, then land it. Phase however makes the most sense once you see the code." For consolidated dispatches, name the compound shape (Research → Architect / Research → Architect → Implement / etc.) as a guideline, not a script.>

# Required reading (in order)
1. docs/orchestrate/<topic>/01-context.md   (REVIEW AGENTS: read docs/orchestrate/<topic>/04-review.md instead — and ONLY that)
2. docs/orchestrate/<topic>/<this-agent's-group-file>.md
3. <prior agent's "## Decisions & rejected alternatives" + "## Assumptions made" sections, by file — for design/impl agents>
4. <any other repo files with line ranges>

# Constraints
- <inlined user constraints from the Q&A>
- <inlined forbidden moves from prior agents>

# Deliverable
- <exact shape: table / diff / numbered findings / file list / design doc / implementation log — match to the work>
- Append your output under the section heading "## <descriptive-section> (<ISO date>)" in docs/orchestrate/<topic>/<group-file>.md before returning.
- **Required: end your deliverable with `## Side notes / observations / complaints`.** Bullet anything you noticed outside the brief's scope that the orchestrator should know — suspicious code, IoC violations, abstractions that fight the standard pipeline for the domain, the brief feeling over-constrained, decisions in the codebase that don't make sense, subjective reactions, suspicions about whether the FOUNDATION is right vs whether the specific task is right. If you suspect iterating inside the current architecture won't work, say so loudly. Equal footing — your observations are signal.

# Hard rules (structural — non-negotiable)
- Do not skip the required reading.
- Do not invent files or line numbers — verify with Read or Grep.
- Reuse existing types and utilities from the reuse audit unless the brief explicitly directs otherwise.
- If the design feels wrong while you implement / the constraints force a workaround that's worse than restructuring / the foundation you're iterating inside of stinks — **bail out and write the smell-flag in your side-notes** rather than grinding through. Smell-driven escape is a first-class output; the orchestrator decides whether to act, your job is to surface.
- The role label in this brief is suggestive. The work itself is what matters; phase it however makes the most sense. Side-notes is your channel to flag anything the brief didn't anticipate.
```

## Anti-patterns

- **"It's a small task, I'll just do it"** — defeats the entire skill. If the user invoked /delegate, delegate.
- **Sub-agent brief that says "see the conversation" or "as discussed"** — sub-agents have no conversation. Inline every fact.
- **Skipping the re-implementation audit** — this is the named root cause the user is trying to defend against. Always audit first.
- **Skipping the Q&A because the goal looks obvious** — the user explicitly required always-ask. The "obvious" cases are exactly where reuse-vs-new gets decided wrong.
- **Single monolithic context file** — collapses the per-group split. One file per agent group.
- **Orchestrator reading code to answer a question** — read is delegated. Only exception: the audit and group files inside `docs/orchestrate/<topic>/`.
- **Agents that don't write back to their group file** — the next agent loses the context. If an agent forgets, dispatch a follow-up to write the missing notes; don't backfill yourself.
- **Designing the agent groups after dispatching the first one** — the README's group plan is fixed in Step 1 and only changes via an explicit user-confirmed pivot.
- **Chaining dispatches across a hard gate** — never dispatch twice in a row across a code-mutating boundary without submitting the prior result to the user and getting confirmation. "Obvious" next steps that touch code are the ones most likely to drift from the user's actual intent. (Soft gates — read-only → read-only — may be chained with an announcement; see rule 6.) When unsure which kind a boundary is, it is hard.
- **Reading session reminders as override of the hard gate** — `<system-reminder>` blocks that say "work without stopping", `UserPromptSubmit` hooks that auto-append a directive, or any harness-injected note that softens clarifying-question behaviour DO NOT authorise chaining across a /delegate hard gate. The user invoked /delegate specifically to control the pace; if they wanted autonomy they would have invoked a different mode. When a reminder and the skill conflict, the skill wins.
- **Serial dispatch of independent read-only agents** — if a phase's agents are all read-only and don't touch code/assets/build/editor (audit, web research, docs/ prior-art exploration), running them one after another wastes the one thing multi-agent is genuinely fast at. Dispatch them as one parallel batch (rule 8). The forbidden direction is the inverse: parallel dispatch of any code-mutating / recompile / test / build agent.
- **Giving the (opt-in) review agent `01-context.md` or the design rationale** — defeats the entire point of a fresh-eyes pass. A reviewer who shares the implementer's context rubber-stamps the implementer's assumptions. Review agents read `04-review.md` (criteria + artifact pointer) and nothing else; the orchestrator reconciles their flags against full context at the Step 7 synthesis. (Reminder: reviewer is opt-in only — see Step 6 — not a default phase.)
- **Invoking the reviewer as a default phase** — reviewer dispatches are bureaucratic overhead when the probe-gate (tests + e2e + user-visual) already does conformance verification. The default distributed-mode flow is architect → impl with the gate as verification. Only opt in to a reviewer when there's a concrete reason: high-stakes hard-to-revert change, user explicitly requested it, design crosses a critical boundary you genuinely want a second pair of eyes on. The reviewer's per-dispatch cost (one Opus dispatch, 10-20 minutes, possible re-architect loop if it FAILs) is real and not justified by "it's how we did it before".
- **Tunnel vision — scope discipline turned into foundation blindness.** Scope discipline is a per-dispatch virtue (keeps context clean, prevents drift). But it becomes blindness when no dispatch has a mandate to step back and question whether the FOUNDATION is right. If every agent in a long orchestration scopes narrowly and nobody calls the smell, you're in tunnel vision. The side-notes deliverable contract + the loop-detection circuit-breaker exist to break this — read agent side-notes, watch for repeated diagnose-first cycles or convergent smell flags, and switch to `/refactor` when the iteration target itself is wrong.
- **Suppressing agent side-notes** — agents are flagship Opus dispatches with rich context. If an agent surfaces "this code stinks" or "the brief asked the wrong question" in side-notes, READ IT. Don't skip the section because the brief's main deliverable was clean. The expensive thing is running Opus and ignoring 99% of what it observed because the brief didn't ask.
- **Design agent that persists only the polished design** — the `## Decisions & rejected alternatives` and `## Assumptions made` sub-sections are the load-bearing trace. An implementer who only sees the design re-derives every implicit decision, often differently. If a design agent's group-file output is missing those sub-sections, dispatch a follow-up to add them — do not let the next agent run without them.
- **Reading user shorthand as a blanket plan-approval** — "continuation", "go", "keep going", "proceed", "do the rest" each authorise ONE next dispatch, not the remainder of the plan. After that one dispatch returns, pause again and ask. Do not infer "continue all phases" from "continuation".
- **Running the commit yourself** — committing pulls the diff into the orchestrator's context and burns tokens on text the orchestrator doesn't need to read. Always delegate the checkpoint commit, even when it feels faster to just `git commit` directly.
- **Skipping the checkpoint because "the agent didn't change anything"** — group-file appends are changes worth checkpointing. If the diff is genuinely empty the commit sub-agent will report that; let it decide.
- **Commit sub-agent recompiling / building / testing** — checkpoint commits only run `git`. If the commit brief lets the sub-agent read project CLAUDE.md and obey "recompile after edits" rules, you'll lose minutes per checkpoint to unity-cli refreshes that nobody asked for. Forbid recompile/build/test explicitly in the brief.
- **Commit sub-agent stashing / selective-staging / reverting** — the checkpoint agent's only git verbs are `git add -A .` and `git commit` (submodules first, then root). Any `git stash`/`stash pop`, any `git add <path>` or `git add -p`, any `git checkout`/`restore`/`reset` of a file is forbidden. A checkout shares its working tree with parallel sessions; a stash or selective-stage that tries to "isolate this session's work" WILL clobber or orphan the other session's in-flight changes. Sweeping the whole tree into one checkpoint is correct behaviour, not a bug to work around.
- **Conversation-relative references in shared files** — "image 32", "the screenshot above", "as discussed", "the file we Read earlier", "see the diff from prior turn". Sub-agents cannot resolve any of these. Replace with prose descriptions or absolute paths.
- **Using `Plan` or `Explore` as `subagent_type`** — both are read-only (no `Write`/`Edit`/`NotebookEdit`/`ExitPlanMode`). Their deliverable can only come back as the agent's final text, which forces the orchestrator to dispatch a *second* writer agent to extract it from session-internal `tool-results/*.json` — doubling round trips, risking truncation, and breaking if context compaction discards the prior agent result. Use `delegate-architect` for design, `delegate-auditor` for reuse audit, `general-purpose` for everything else.
- **Letting an agent return its deliverable only as text** — the orchestrator never extracts content from agent return messages; only files on disk are load-bearing. Every agent's brief must contain a "Required last action: Write/Edit to <group file>" instruction, and the orchestrator must verify the file actually changed before proceeding.
- **Assuming a sub-agent can see an attached image** — they cannot. Conversation-attached images have no on-disk path. Either describe the image's load-bearing content in prose, or get the user to save it to a path you can reference absolutely.
- **Skipping Step 2.5 mode selection** — defaulting to distributed mode without running the blast-radius analysis. The mode choice is mandatory and evidence-grounded; "I always use distributed" is the same shortcut as "I'll just do it myself."
- **Running distributed mode for a cohesive, dependency-dense, bounded-context change** — this is precisely the case both Anthropic and Cognition found multi-agent *hurts*. If all four Step 2.5 criteria hold, distributed mode is the wrong tool; recommend consolidated mode.
- **Consolidated agent self-certifying high-risk work** — consolidated mode's review is self-review. For anything high-risk it must escalate to a fresh-eyes `delegate-reviewer`, never sign off on its own design. A consolidated `## Implementation log` with high-risk items and no escalation is incomplete.
- **Writing `SendMessage`, "resume the agent", or any mid-run checkpoint into a brief or flow** — a returned sub-agent is gone; this harness has no resume (the Agent tool's description mentions `SendMessage`, but the tool is not present). A gate between two stages always means a fresh agent reading the prior stage cold off disk. So consolidated mode runs in one uninterrupted pass, and any flow that genuinely needs a design-approval gate before implementation belongs in distributed mode, not consolidated mode.
- **Ignoring the circuit-breaker while distributed mode thrashes** — re-dispatching the same phase a third time, watching the design fail to stabilise, letting the user redirect at gate after gate. When a trigger fires, offer the consolidated handoff; do not grind the distributed loop into the ground.
- **Paragraph-summarising every dispatch and asking "confirm to proceed?"** — the orchestrator's job is to thread context between agents, not to narrate every dispatch back to the user. Routine architect → implementer flow goes silent (one-line announcement, no synthesis, no Q&A). Synthesis fires when something is load-bearing for the user (visual QA, flagged risk, real choice). When the soft-gate branch applies, paragraph syntheses are friction without benefit. The user reads syntheses to catch pivots — give them syntheses where pivots actually exist, not after every clean dispatch.
- **Q&A with "approve / confirm to proceed" as a primary option** — if the only options are "go" and "stop", there is no real choice; the orchestrator should just dispatch. AskUserQuestion is for load-bearing forks where the user's preference picks the answer. A 4-option Q&A whose recommended option is "yes, proceed" is the symptom — collapse it.
- **Reading agent group files to spelunk for "interesting" content** — the orchestrator's reads of agent group files are budgeted for (a) composing the next agent's brief, (b) extracting visual QA / flagged risk / real choice to surface to the user. Reading the full design to write a synthesis the user didn't ask for burns the orchestrator's context for no gain. If the next dispatch's brief doesn't need a fact, don't read it into your context.
- **Forced-role briefs ("you are an architect; do only X; do not touch Y")** — kills the agent's sense of responsibility outside the labelled scope and guarantees tunnel vision. The brief explains the WORK (problemspace, artefact, constraints); the role is a SUGGESTION the agent can re-phase. The diagnostic agent that won't flag an upstream smell because "that's not what I was asked to look at" is this anti-pattern's signature. Frame roles as suggestive — see "Suggestive roles, not enforced roles".
- **Defaulting to Singular Research or Singular Architect when Research → Architect would work** — the compound shape preserves the trace continuity from investigation into design (or design into code), which is the entire reason to choose consolidated mode in the first place. Singular shapes throw that away. Reach for singular only when the next phase is genuinely independent (a literature review the user wants to react to before deciding direction; a design pass that will be implemented weeks later by a different orchestration). Otherwise compound.
- **Scripting the phases of a consolidated dispatch in the brief ("stage 1 do X, stage 2 do Y, stage 3 do Z")** — defeats the point of the freeform Research → Architect → Implement shape. The agent receives the problemspace and decides phasing once it sees the code; orchestrator-imposed scripting fights the agent's own analytical surface and produces the same tunnel vision as forced roles. Brief composition: lead with problemspace, suggest phasing as a guideline, specify the structural contract — let the agent re-phase if its read of the code says the suggested phasing is wrong.
- **Using Research → Architect → Implement for non-debugging work** — the freeform full-pipeline shape is for one significant task inside a larger debugging set, where impl discoveries feed back into design. Greenfield work, big refactors, and design-doc requests do NOT benefit from compounding implementation in — they belong in Research → Architect (or Prompt → Architect) with the implementation as a separate downstream dispatch (or session). Compounding impl into a design-doc-producing shape produces a fait-accompli the user has no chance to redirect before code lands.
- **Orchestrator speculating code-grounded hypotheses** (binding — see Hard Rule 9). The orchestrator does not read code, so any "candidate mechanism" / "this is probably caused by X" / "likely the issue is Y" it produces is pattern-match off training-data priors, not synthesis off this codebase's evidence. Speculation in synthesis blocks pre-frames the dispatched agent's investigation; speculation in briefs channels Opus-1M into the orchestrator's hunches instead of fresh investigation; speculation in orchestrate documents pollutes the durable record with wrong-mechanism noise that future agents waste cycles ruling out. The user caught this on workstream A4 (2026-05-20): "did you just pose a hypothesis? why did you do that? did you read any code during this session?" The signature: a bulleted "candidate mechanisms" list in a hard-gate block; a brief that says "the issue is probably X, investigate that first"; an orchestrate doc that lists three hypotheses none of which were cited to any file. Surface user-verbatim observations, sharp thresholds, and grounded prior findings. Then dispatch. Do not "help" the dispatched agent by pre-framing the diagnosis.
- **Mixing one grounded candidate with speculative ones in a single list** — the speculation contaminates the grounded item by association. If only one bullet in a "candidate mechanisms" list is cited to a doc and the rest are speculation, the list reads as a triage by the orchestrator across multiple hunches, lending false authority to the speculative items. Cite each item to its source or remove it. Bulleted-list-with-only-some-citations is the smell shape — every item gets a citation or the list collapses to the one item that has one.
- **Scoping the brief by inferred symptom-location instead of user-observed symptom-manifest** (binding — see Hard Rule 9). The orchestrator observes the user's report ("rings on main camera, smooth on probe") and translates it into a code-path claim ("the AP-LUT is the divergence surface"). The claim is unverified speculation, but phrased as topology it reads like a fact and becomes the brief's scope. Every subsequent architect dispatches *inside that scope* and never questions it — because the partition was presented as the frame, not as a hypothesis to test. Signature: a brief sentence that names a specific code path / pipeline stage as the location of the bug, without citing a probe output, captured value, or user-confirmed bisection that empirically implicates it. Cure: frame the problemspace by what the symptom MANIFESTS AS in user-visible terms (an open question — "find what code path could produce this manifest"). Let the architect derive the partition by reading code. The user's 2026-05-21 cloud-radial-banding session is the canonical instance: three architect dispatches (A7 / A8 / A9) tunneled inside an orchestrator-inferred "AP-LUT path" partition that turned out to be only half-correct, until a diagnose-first probe sequence finally tested the partition empirically.
- **Ignoring the diagnose-first trigger to issue a second speculative fix** (binding — see "Diagnose-first circuit-breaker"). When the user reports a fix didn't visibly reduce the symptom — even ONCE, even slightly — the next dispatch is a read-only diagnostic. Not "let me try fix B" / "let me revert and try fix C" / "the architect's diagnosis was internally consistent but maybe the wrong term". The temptation to issue a second speculative fix is exactly what the rule forbids. The 2026-05-21 cloud-radial-banding session: A7 fix landed → user reported rings → orchestrator dispatched A8 (revert) → user reported rings persist → orchestrator dispatched A9 (revert different term) → user reported rings persist → orchestrator FINALLY invoked diagnose-first. Two unnecessary code-mutating dispatches before the trigger was honoured. The trigger fires the FIRST time the user reports the symptom unmoved; subsequent fix-shaped dispatches are forbidden until a diagnostic has narrowed the partition by empirical probe.

## E2e gate authoring discipline (binding)

When an orchestration's scope includes adding or modifying an e2e gate that is intended to capture a **user-visible artefact** (a visual glitch, a runtime behaviour, anything whose ground-truth is "what the user sees"), the gate is NOT considered analytically valid until the user has visually confirmed that its captures show the artefact. A passing/failing variance ratio + a numerical threshold are **not sufficient** — they only prove the metric responds to the captured pixels, not that the captured pixels are the artefact.

This rule exists because the dominant failure mode of this orchestration mode is: an agent builds an e2e gate that compiles and passes a pre-fix/post-fix smell test, but the captured framebuffers are smeary, mis-timed, off-camera, or otherwise not actually showing the symptom the user described. The fix lands, the gate is green, and the artefact is still there because the gate was measuring something else.

### How this changes the dispatch shape

E2e gate authoring is split into a **separate phase** from the fix-implementation phase. The two are NEVER bundled into a single dispatch — not "two stages of a consolidated dispatch", not "two steps of one impl agent's brief". **Separate dispatches with a hard user-verification gate between them.**

1. **Gate-authoring phase.** Dispatch an implementer to:
   - Add the e2e gate (binary entry, capture system, mode flag, driver wiring).
   - **Mandatory: capture screenshots.** One per captured frame — not just a summary frame. Save them to a predictable absolute path the user can browse, e.g. `target/e2e-screenshots/<gate-name>-frame-<N>.png`. Every new visual-capturing gate MUST land with on-disk screenshots; a gate that only emits a numerical metric is not finishable.
   - Run the gate ONCE on the **current** (pre-fix) worktree.
   - Report: path to each captured frame, the pre-fix metric value(s).
   - Do **NOT** apply any fix yet. Do **NOT** calibrate the threshold yet. Do **NOT** propose post-fix expectations yet.

2. **Visual verification hard gate (user-facing, mandatory).** Present the captured screenshots to the user as absolute paths in chat — one line per frame, so they can open each frame and judge. Ask explicitly: *"Do these captures show the artefact you described? Is the timing right (capturing the shift frame, not a frame before/after)? Is the camera path right? Are the captures sharp, not smeary?"*
   - **If the user says "yes, the captures clearly show the artefact"** → proceed to step 3.
   - **If the user says "no" / "kind of" / "the timing is off" / "this isn't what I see" / "they're smeary"** → **redirect**. Dispatch a fix to the gate's capture mechanism (camera path, capture trigger, frame indexing, screenshot timing, exposure, scene state). Do NOT proceed to the fix until the captures are clean. **Re-loop the user verification after each capture-mechanism fix.** A smeary, wrong-timing, or wrong-content capture is a *broken gate*, not a finishable one — perfecting it before moving on is the entire point of this phase.

3. **Threshold calibration phase.** Only after the captures are user-confirmed: dispatch the metric + threshold authoring. The threshold is calibrated against the user-confirmed-artefact pre-fix run.

4. **Fix-implementation phase.** Now (and only now) dispatch the actual fix. Re-run the gate post-fix; the gate must PASS. Optionally re-present the post-fix screenshots to the user for a second visual confirmation — recommended for symptoms where the post-fix expectation isn't a sharp binary (e.g. "this should be eliminated" vs "this should be reduced").

### Why this is mandatory, not optional

If the captures are smeary or mis-timed, no threshold calibration can save the gate. A 1.40× ratio reduction between "wrong frames pre-fix" and "wrong frames post-fix" tells you the fix changed something — but says nothing about whether it changed the thing you cared about. The visual verification gate is what bounds the gate to the user-reported artefact rather than a coincidentally-correlated GPU signal.

The shape that fails: bundling gate-authoring + threshold-calibration + fix-implementation into one dispatch, then declaring victory because pre-fix FAILED and post-fix PASSED. The threshold calibration *can* still be tuned to make almost any pair of captures produce a FAIL→PASS transition — that doesn't make the gate analytically valid.

The shape that succeeds: split the dispatches, hand the screenshots to the user before the metric is even calibrated, and accept that gate-authoring may need its own redirect loop before the fix can land.

### When this rule does NOT apply

- Pure logic / unit tests with no visual component — Rust unit tests, property tests, parser tests, etc.
- Existing gates being re-run as part of verification — only NEW or MODIFIED visual-capturing gates trigger the visual-verification dispatch shape.
- Gates whose ground-truth is byte-exact equality against a fixed reference (e.g. oracle tests where the reference framebuffer is itself the spec). The reference image IS the verification surface.

The rule applies whenever the e2e gate's job is to capture a user-described visual symptom and reduce it to a metric — that's where the smear/timing failure mode lives.

## E2e-specific anti-patterns

- **Bundling e2e-gate authoring with fix implementation in one dispatch.** Defeats the visual verification step. Gate captures are validated only by the variance ratio, not by the user's eye. If the captures are smeary, the fix gets credited (or blamed) for moving a metric on the wrong frames. See §"E2e gate authoring discipline".
- **Validating a gate by pre-fix FAIL / post-fix PASS alone.** That ratio proves the metric moved; it does NOT prove the metric moved because of the artefact. Visual confirmation of the captured frames is mandatory. The threshold can be calibrated to make almost any pair of pre/post captures produce the FAIL→PASS transition — the load-bearing question is "are these captures actually the artefact?", and only the user can answer that.
- **Treating "the gate compiled and the variance ratio looks reasonable" as completion.** It is not completion. Completion is "the user has looked at the captured screenshots and confirmed they show the artefact, AND the metric responds to that artefact correctly."

## Diagnose-first circuit-breaker (binding)

A separate trigger from the consolidated-mode circuit-breaker in Step 7. Fires on a different failure mode: a published diagnosis that doesn't survive contact with reality.

**Trigger:** the user reports that a fix did NOT visibly reduce the user-visible symptom (a live visual check, a runtime check, anything where the ground-truth is what the user sees). Even ONCE. Even slightly. "Pretty much the same" / "still blinking" / "no change" — all trigger.

**Mandatory action:** the next dispatch is a read-only diagnostic investigator. No exceptions. No "let me tighten the hash" / "let me widen the parity bit" / "let me try option B from the prior analysis". A speculative second-pass fix is never an option.

**Do NOT present a Q&A at all.** Not "diagnose vs try-fix-B vs revert" — none of that is a menu. Diagnose is the only path. A speculative fix is not an alternative the orchestrator can offer. Revert is sometimes the right call but it is a *self-realisation* ("we screwed up scope, the cleanest move is to back out and restart") — never a user-facing menu item alongside diagnose. Presenting alternatives is itself evasion: the user picks whatever sounds fastest, which is precisely the bias this rule exists to override.

**What the orchestrator does instead:** state in chat that the visual check failed and diagnose-first is firing. Summarise in one or two sentences what the diagnostic agent will look at. Dispatch it (it is read-only, so the soft-gate rule applies — announce and proceed, no user-confirmation pause). The user can interject if they want a different path, but the orchestrator does not solicit that — the default is dispatch-now, silence-is-go.

A speculative fix is never an option. Revert is the orchestrator's silent escape hatch when scope is wrong, not a menu choice.

The diagnostic investigator's brief:
- Reads the existing diagnosis with fresh eyes (the brief tells it explicitly to drop the prior diagnosis as a bias source).
- Maps the full pipeline that touches the symptom — not just the layer the prior diagnosis attacked.
- Enumerates alternative hypotheses with code-grounded evidence for/against each.
- Writes findings to disk; does not edit code.

**This rule overrides "the diagnosis was line-grounded and confident".** The handoff that produced the original diagnosis was, by `/handoff` skill's framing, written by a session that itself could not finish the task — its diagnosis is unverified by construction. A strictly-stronger fix in the same hypothesis class producing no improvement is near-conclusive evidence the hypothesis is wrong, not under-tuned. The orchestrator MUST treat "user-visible symptom did not move" as a kill signal for the current hypothesis class, not as "fix needs more tuning".

**Anti-pattern this defends against:** the orchestrator reads the prior fix's failure as "the implementer self-flagged Finding X as a known-residual tradeoff; let's address Finding X next", and dispatches a refinement targeting that Finding. That is the trap. A self-flagged "known residual" turning out to be load-bearing for the symptom is much less likely than "the diagnosis is wrong and Finding X is irrelevant". When in doubt, observe before iterating.

**Sanity check before any post-fix dispatch (predict-the-outcome rule).** Before dispatching iteration N+1 of a fix, write down — in chat, in one line — *what the user-visible symptom would look like if iteration N had been the right fix.* This is the falsification line. When iteration N's actual user check produces an outcome inconsistent with that prediction (e.g. you predicted "blink eliminated" and the user reports "unchanged"), the hypothesis is falsified, not under-tuned. Diagnose-first fires. The predict-the-outcome line goes into the orchestrator's chat output BEFORE the user runs the check, so the comparison is honest after the fact.

## Side-notes deliverable contract (binding — every agent, every dispatch)

Every agent's group-file deliverable MUST end with a `## Side notes / observations / complaints` section (or equivalent heading — "agent notes", "out-of-scope flags", "things I'd improve", "rants"). The orchestrator reads it. It is OPTIONAL content with EXPLICIT permission to surface anything the agent noticed that doesn't fit the deliverable contract.

The framing for the agent (include in every brief):

> Anything you noticed while doing this task that doesn't fit the deliverable but you think the orchestrator should know — write it here. Examples:
> - Code that looks suspicious or stinky (conflated concerns, IoC violations, accidentally-global state, "dead memory nobody reads", abstractions that fight the standard pipeline for the domain).
> - The brief felt over-constrained or asked the wrong question — say what you'd have done differently.
> - Decisions in the codebase that don't make sense to you.
> - Tools that were missing; context that was missing; signals you wish you'd had.
> - Even subjective reactions — "this was confusing", "I felt like I was making the same observation as the prior agent", "the brief asked X but Y seemed more relevant", "I think this orchestration is heading in the wrong direction".
> - If you suspect the FOUNDATION is wrong (not the specific task you were given, but the architecture you'd be iterating inside of), say so loudly. The orchestrator decides whether to act; your job is to surface.
>
> Stay terse — bullet points are fine. The orchestrator reads side-notes as signal, not noise; one sharp observation beats five paragraphs of hedging.

**Why this is binding (not optional):** the orchestrator's tunnel-vision failure mode is scoping every dispatch narrowly and ignoring everything that doesn't fit the scope. The side-notes channel is the structural cure. Agents are flagship Opus dispatches with rich context windows full of observations; suppressing those observations because the brief didn't ask for them is the most expensive waste in this skill. Equal footing — every agent (architect, impl, auditor, diagnostic, even reviewer when invoked) writes side-notes; orchestrator reads them.

## Loop-detection circuit-breaker → `/refactor`

A separate trigger from diagnose-first and the consolidated-mode handoff. Fires when the orchestration is stuck iterating inside a broken foundation rather than solving the user's symptom.

**Trigger** — any one of:

1. **3+ consecutive failed fix attempts** on the same user-visible symptom (the user reports "no change" / "still broken" / "same issue" multiple times across distinct fix dispatches).
2. **Diagnose-first has fired 3+ times** in one orchestration — each diagnosis was code-grounded but the fix didn't move the symptom. Signal: the diagnoses are pointing at real bugs that aren't the load-bearing one; the load-bearing one is foundation-level.
3. **2+ agents in one orchestration surface "this code is smelly / the foundation is wrong" in their side-notes**, even on distinct dispatches. Multiple independent agents converging on a smell flag is strong signal.
4. **The orchestrator notices** while organising context that the codebase has obvious architectural rot the prior dispatches walked past (two addressing schemes for one buffer, "dead memory nobody reads", state that doesn't reset, etc.). Trust your own smell-check.

**Mandatory action:** present the trigger to the user at a hard gate and offer to switch from `/delegate` iteration into a `/refactor` session. The framing: "we've iterated N times against this symptom; the foundation looks rotten; the right next step is to refactor toward [the missing pattern] BEFORE more fix attempts, otherwise the next dispatch likely lands on top of the same rot." User confirms; if yes, the current orchestration pauses (docs stay intact) and `/refactor` takes over.

**This is NOT a speculative second fix** — it's a structural acknowledgement that the iteration target is wrong. Diagnose-first prevents speculative same-class fixes; loop-detection prevents speculative-iteration-inside-rot. They're complementary circuit-breakers, not alternatives.

**Do NOT push past this circuit-breaker silently.** When a trigger fires, the orchestrator stops and offers. Continuing without the offer is the tunnel-vision failure mode this rule exists to prevent — same shape as ignoring diagnose-first when a fix didn't help.

## Brute-force protocol (opt-in alternative to diagnose-first)

An opt-in mode that trades orchestrator-context-hygiene for sub-agent autonomy. Where diagnose-first keeps the orchestrator in the loop and dispatches one read-only diagnostic at a time, brute-force dispatches ONE sub-agent that owns the entire hypothesise-test-iterate loop end-to-end, against a deterministic probe-gate, with a private progress file the orchestrator NEVER reads. The orchestrator sees only a final-deliverable summary on success or an architectural-escape-hatch report.

This mode is **legitimate alongside diagnose-first**, not a replacement. They suit different conditions.

### When to use brute-force

All four should hold:

1. **A clean deterministic probe-gate exists.** A passing/failing programmatic signal (SSIM threshold, unit test, CI check, byte-exact oracle) that takes minutes — not hours — to run. The gate must be analytically valid (the e2e-gate authoring discipline still applies — captures must show the artefact; threshold must be calibrated against user-confirmed pre-fix runs).
2. **Iteration cost is low.** Building + running the gate fits comfortably in one sub-agent's context window (~5–15 mins per round; agent can run 10–30 rounds before context exhaustion).
3. **Scope is bounded.** The expected change surface is one module or a small set of files. Open-ended "could touch half the codebase" scope disqualifies — the agent would rabbit-hole.
4. **The orchestrator has either repeatedly failed diagnose-first cycles** (3+ fix attempts didn't help; the search space is broader than the orchestrator's hypotheses keep finding) **OR the user explicitly engages it** ("lets do brute-force protocol"). Don't open with brute-force on a fresh task — diagnose-first's lighter ceremony is the right default.

### When NOT to use brute-force

- No clean probe-gate. The only verification is "user looks at the binary". Use diagnose-first + visual verification gates instead — the user IS the analytical surface and can't be replaced by a gate.
- Probe-gate takes >15 mins per run. Iteration cost too high; the agent burns its context on waiting.
- The user wants a design-approval gate before code is written. Brute-force commits code on every hypothesis attempt; the user reviews only the final 3×PASS submission.
- The orchestrator already knows the right architectural shape and just needs an architect → impl walk (with optional opt-in reviewer if the change is high-stakes). Use distributed mode.

### Protocol shape

1. **Single dispatch, full autonomy.** The orchestrator briefs ONE sub-agent with:
   - Required reading: the full orchestration context (all the prior diagnoses + impl logs + the probe-gate's recent failure modes + the SSIM scores / unit-test logs / whatever).
   - The probe-gate command + the success criterion (e.g. "all SSIM checks ≥ 0.9; three consecutive PASS runs to rule out indeterminism").
   - A pointer to the agent's PRIVATE progress file (e.g. `docs/orchestrate/<topic>/NN-brute-force-log.md`).
   - The architectural-escape-hatch clause (see #7 below).
   - Explicit context-hygiene rule: "The orchestrator never reads `<progress-file>`. Do not echo your attempts back via your return text. Only the final summary in `<summary-file>` reaches the orchestrator."

2. **Independent pre-round of investigation.** Before touching code, the agent reads:
   - All orchestration docs (context, diagnoses, prior fix attempts).
   - The probe-gate's recent failure modes (verbatim output if available).
   - Their own progress file from any prior brute-force rounds (if any).
   - The relevant source files end-to-end (not just the lines the prior diagnoses named).

3. **Agent poses an independent hypothesis set, ordered by probability.** At least three hypotheses, ranked by their own (fresh-eyes) read of the code. The agent does NOT follow the orchestrator's "recommended fix shape" — that recommendation is part of the prior context, not a directive. Independent ranking is the point; if the agent just executes the orchestrator's recommendation, the brute-force protocol has no value over distributed mode.

4. **Agent writes a predict-the-outcome line per hypothesis BEFORE testing.** What the probe-gate would do (PASS/FAIL on which checks) if the hypothesis is the right fix. This is the falsification line (mirror of diagnose-first's predict-the-outcome rule). Without it, brute-force devolves into "tune until something passes".

5. **Test each hypothesis against the probe-gate.** For each:
   - Implement the change.
   - Run the probe-gate.
   - Record outcome (PASS / FAIL + which checks moved + how that compares to the prediction) in the private progress file.
   - If FAIL: revert the change or keep it as a partial improvement (agent's call, based on whether the change made the gate *worse* or *better-but-not-passing*).
   - If PASS: proceed to the indeterminism check.

6. **Indeterminism check on first PASS.** Run the probe-gate TWO MORE TIMES on the same code. **All three runs must PASS.** If any of the additional runs FAILs, the first PASS was a fluke (or there's flakiness in the gate) — record + continue iterating against the next hypothesis. Three-consecutive-PASS is the only acceptable submission criterion.

7. **Architectural-escape-hatch (binding).** If at any point the agent's analysis reveals that the right fix requires a LARGE architectural change — e.g., touches multiple modules, introduces a new system, crosses world boundaries, requires API redesign, or otherwise blasts past "bounded scope" — the agent MUST EXIT the brute-force protocol and report this to the orchestrator. The escape signal is a one-paragraph design sketch in the summary doc: "I've identified the load-bearing fix but it requires <architectural change description>; the orchestrator should switch to distributed mode (architect → reviewer → impl) for this." The brute-force protocol is for bounded iteration, not for delegating architectural decisions to a sub-agent.

8. **Submit on three consecutive PASSes.** Write a clean summary in the deliverable doc (e.g. `NN-brute-force-summary.md`) that the orchestrator reads. The private progress log stays separate — the orchestrator should not need to read it to understand the submission.

### What the summary doc contains

- One line: the final-hypothesis that produced the PASS.
- File:line touch list of the landed change.
- Verbatim three-run probe-gate output (proving indeterminism is ruled out).
- One paragraph: what the agent tried that DIDN'T work (compressed, NOT a full progress log).
- If the architectural-escape-hatch fired: the design sketch instead of a PASS report.

### Context hygiene (binding)

- The agent's progress file is **NEVER** read by the orchestrator. Not for status checks, not for "interesting details", not to populate the next agent's brief. The whole point is that the orchestrator's context stays clean across long iteration loops.
- The brief must explicitly state: "track your attempts in `<progress-file>`. The orchestrator never reads that file. Do NOT echo attempt details back via your return text — that pollutes the orchestrator's context the same way."
- The summary file IS read by the orchestrator. Keep it terse; everything verbose goes in the progress log.

### Comparison with diagnose-first

| | Diagnose-first | Brute-force |
|---|---|---|
| Trigger | A fix didn't visibly help (mandatory) | Repeated diagnose-first failure + clean gate exists (opt-in) |
| Per-cycle dispatches | Read-only diagnostic → fix → user check → repeat | One agent owns whole loop |
| Orchestrator context per cycle | Sees diagnosis findings, presents to user | Sees only final summary or escape report |
| Verification surface | User's eye + e2e gate after fix | Probe-gate within the agent's loop |
| Cost | Lower per-dispatch; more dispatches | One dispatch; heavier sub-agent context |
| Architectural decisions | Orchestrator decides per cycle | Agent escapes back to orchestrator if needed |
| Bias-resistance | Fresh-eyes per cycle (each diagnostic agent independent) | Agent's pre-round investigation is the fresh-eyes pass |

Either mode satisfies the principle "no speculative fixes" — diagnose-first by forcing a read-only diagnostic between attempts; brute-force by requiring an independent pre-round of investigation + predict-the-outcome per hypothesis + 3×PASS submission criterion.

### Anti-patterns specific to brute-force

- **Orchestrator reading the progress log.** Defeats the entire mode. The progress log is for the agent's own bookkeeping across its own context; it accumulates verbose detail by design. Reading it pollutes the orchestrator with the very context the protocol exists to isolate.
- **Sub-agent following the orchestrator's "recommended fix shape" verbatim.** The brief usually contains an orchestrator's recommendation from the prior diagnose-first cycles. The brute-force agent treats that recommendation as ONE hypothesis among several, ranked by the agent's own analysis. If the agent just executes the recommendation, brute-force adds no value over a regular impl dispatch.
- **Submitting on a single PASS.** Indeterminism kills the entire signal. Three consecutive PASSes is the floor; anything less is a fluke.
- **Skipping the predict-the-outcome line.** Without it, the agent can rationalise any PASS as "the fix" even when the gate moved for unrelated reasons. The prediction must be written BEFORE the gate run, in the progress log.
- **Pushing through the escape-hatch.** When the agent realises the right fix is architectural, the protocol REQUIRES exit. Pushing through with a hack that "happens to make the gate pass" produces a brittle PASS that regresses on the next change. Escape is not failure — it's the protocol working.
- **Using brute-force as the default opening mode.** Brute-force is heavy (one sub-agent eats many rounds of context). On a fresh task with no failed diagnose-first cycles, the lighter ceremony of regular dispatching is correct. Brute-force earns its weight when diagnose-first has demonstrably stalled.

## Exit
The mode ends when the user signals done or when `README.md`'s phase checklist is fully `[x]`. Leave `docs/orchestrate/<topic>/` intact — it's the durable artifact. Do not delete or condense it on exit unless the user asks.
