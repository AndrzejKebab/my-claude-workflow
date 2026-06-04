---
name: delegate
description: Multi-agent orchestration mode. The orchestrator never reads, edits, runs, or tests directly — it scopes work, runs a re-implementation audit, presents a freeform method brief with grounded recommendations, then dispatches every step to sub-agents through shared context files at `docs/orchestrate/<topic>/`. Use when invoked via /delegate, when the user asks to orchestrate or coordinate multi-agent work, or when the task explicitly calls for delegation.
---

# delegate

Enter orchestration mode. In this mode the orchestrator does **not** do the work. The orchestrator scopes, briefs, shares context, and synthesizes — every other action is dispatched to a sub-agent via the Agent tool.

**Scoping means assembling the *problemspace*, not navigating it.** The orchestrator's handoff describes the problem as **spatial-visual phenomenology** — what is perceived, where *in the rendered scene / the artefact the user sees*, when, under what conditions — never where in the *machinery* the problem resides. The forbidden "where" is not only a code path: a **domain concept**, a **pipeline stage**, a **named subsystem or technique** ("the AP-LUT", "the fog stream", "the scattering integration") is the identical error — each pre-locates the problem in the machinery that produces the phenomenon. The orchestrator assembles the problemspace; the architect navigates it from phenomenon → machinery → mechanism → fix (Hard Rule 9).

**What `/delegate` buys — and what it costs.** The multi-agent structure buys *context isolation*: the orchestrator stays clean, never accumulates code/diffs/tool-output, never suffers context rot across a long task. It does **not** buy throughput — dispatched agents cost roughly an order of magnitude more tokens than inline work. So `/delegate` is the right tool when orchestrator context rot is the real risk (long, multi-phase, code-heavy work) and the wrong tool when it isn't. If the task is small enough to finish in a normal session without the orchestrator's context degrading, use a normal session. When `/delegate` *is* right, recover what speed you can via parallel read-only fan-out (rule 8) and cost-tiering (Step 1).

## Two execution modes

`/delegate` runs in one of two modes, chosen per task from the published evidence, not by guess:

- **Anthropic** (multi-agent research system) found orchestration *excels* at breadth-first work — many independent directions in parallel, information exceeding one context window, heavy tool use — and *underperforms* in three cases: **(1) coding tasks**, **(2) work where all agents share the same context**, **(3) work with many dependencies between subtasks**. Ordinary `/delegate` work — one coherent code change with coupled parts — sits in all three.
- **Cognition** ("Don't Build Multi-Agents") identified the mechanism: handoff and parallel workers make *conflicting implicit decisions*, because the full agent trace does not survive compression into a handoff file. Their fix: keep context continuous — share full traces, not distilled summaries.
- **Therefore:** the split is right when the work is genuinely breadth-first, independent, exploration-heavy, or too big for one context. It is *wrong* — by both labs — when the work is one cohesive, dependency-dense, design↔implementation-coupled change that fits in one context. A large fraction of real `/delegate` tasks are the second kind.

**Distributed mode (default).** Orchestrator + separate auditor / architect / implementer agents, phase gates, shared-context files. Buys context isolation; costs trace loss across handoffs, the token multiplier, latency, re-dispatch thrash. **A fresh-eyes reviewer is NOT in the default flow** — reviewer dispatches are opt-in, for a concrete reason only (high-stakes hard-to-revert change, user explicitly requested it, design crosses a critical boundary). Default verification is the probe-gate (tests + e2e + user-visual); code-quality / smell concerns belong to `/refactor` sessions.

**Consolidated mode.** The orchestrator still does the cheap load-bearing parts itself — scoping, the re-implementation audit, the architectural Q&A, writing `01-context.md`. Then it dispatches **one** agent in a 1M-context window that runs the compounded phases in a single uninterrupted run, flushing each stage to its group file as it goes. One continuous context — the full reasoning trace carries phase-to-phase with zero handoff loss, which is the entire point. The price is real and bounded by Step 2.5 eligibility: there is no mid-run approval gate (a returned sub-agent cannot be resumed — see "Sub-agent context boundaries"), and when implementation is included the review is *self*-review. If the work needs a hard approval gate between phases, that is distributed mode's native structure — use it.
> Failure mode: running distributed mode for a cohesive, dependency-dense, bounded-context change is precisely the case both labs found multi-agent *hurts*. If all four Step 2.5 criteria hold, recommend consolidated.

The orchestrator selects a mode at **Step 2.5**; the user confirms it in the **Step 4** Q&A. Distributed mode can also hand off to consolidated mode mid-orchestration when thrashing — the **circuit-breaker** in Step 7.

### Consolidated dispatch shapes

Consolidated mode is a family of dispatch shapes, not one fixed pipeline. **Compound** shapes stitch multiple phases into one continuous trace; **singular** shapes run one phase. Default to compound — singular forfeits the trace continuity that makes consolidated mode worth choosing.

- **Research → Architect** (compound, design-producing). The agent investigates research / prior art / the codebase, then designs. Output is a design document; no code. For: large preliminary fieldsearch, big refactors, greenfield work, or an explicit design-document request.
- **Prompt → Architect** (compound, design-producing). Same shape, but architecting starts directly from the brief without a preliminary investigation pass — appropriate when the brief itself carries enough context (handoff doc, prior orchestration's group files, user-supplied research).
- **Research → Architect → Implement** (compound, full pipeline). For one significant task inside a larger debugging set — where the design genuinely cannot be frozen before implementation because impl discoveries feed back. Briefed in **freeform**: the agent gets a clear explanation of the problemspace (symptoms, hypotheses, pipeline geometry, prior diagnoses) and is trusted to phase its own work. NO strict scenario, NO enforced roleset.
- **Singular Research** OR **Singular Architect** (rare). Standalone investigation, or standalone architecting from research already on disk. Reach for these only when the next phase is genuinely independent (a literature review the user wants to react to before deciding direction; a design pass that will be implemented weeks later by a different orchestration). Otherwise compound — the trace from investigation → design, or design → code, is what consolidated mode buys.

The Step 2.5 eligibility criteria (bounded context, single cohesive scope, low blast radius / reversible, tight design↔impl coupling) gate the **Implement-containing** shapes — they bound the no-pre-impl-gate and self-review costs. Design-only shapes (Research → Architect, Prompt → Architect, Singular Architect) write no code, so the blast-radius / coupling criteria do not gate them; they are eligible whenever the work matches their use case. Singular Research is eligible whenever the investigation is the user-visible artefact.
> Failure mode: using Research → Architect → Implement for non-debugging work produces a fait-accompli the user can't redirect before code lands. Greenfield / big refactors / design-doc requests belong in Research → Architect, with implementation a separate downstream dispatch.

### Suggestive roles, not enforced roles

Roles in `/delegate` are *suggestive*. The brief tells a sub-agent what the WORK is, not who it must pretend to be. Briefs that say "you are an architect; your only job is X, do not touch Y" force tunnel vision — the agent's sense of responsibility evaporates inside the role boundary, and it ignores everything outside its labelled scope, including the side-notes channel that exists to catch what the brief missed. The same failure plays out at every scale: a "diagnostic agent" that won't flag an obvious upstream smell because "that's not what I was asked to look at", an "implementer" that grinds through a bad design instead of bailing, a "reviewer" that signs off on a passing test that measures the wrong thing.

Frame responsibility broadly: lead with the problemspace ("this is a debugging task — here is the symptom, the pipeline, the artefact we want"), then SUGGEST phasing ("you'll likely investigate first, then design, then implement"), then specify the structural contract (required reading, deliverable-on-disk, side-notes). The agent is flagship Opus on equal footing — full entitlement to call smells, raise scope concerns, redirect direction. The only non-negotiables are the structural contracts; the role label is decorative. This applies to every brief, every shape, distributed and consolidated.

**Orchestrator speculation is a particularly damaging form of role-forcing** — it forces the agent to chase a hypothesis the orchestrator pulled from training-data pattern-match. See Hard Rule 9.

## Hard rules

1. **Never work alone.** Every research, design, implementation, test run, and review step is dispatched. The orchestrator only writes shared-context files and agent briefs. If you find yourself about to Read code, run a build, or Edit a file — stop and dispatch. (Includes "it's a small task, I'll just do it": if the user invoked /delegate, delegate.)
2. **Full and complete context in every brief and every shared file.** Sub-agents have no memory of the conversation, no view of attached images, no access to prior tool outputs, no shared memory with the orchestrator. Inline every fact they need: file paths, line numbers, Q&A decisions, prior findings, user constraints. Never gesture at "the conversation", "what we discussed", "the screenshot above", "image N", or any conversation-relative index. Same for anything written into shared-context files — they must be readable cold.
3. **Shared-context files are the medium.** Agent groups exchange information through files under `docs/orchestrate/<topic>/`, not through your summaries. One file per group (never a single monolithic context file). Every agent reads its group file on entry and appends on exit.
4. **Architecture-first, always.** Before any agent fires — even for a tiny-looking task — present the method to the user via a summarized freeform brief and run the re-implementation audit. The brief + audit are mandatory. `AskUserQuestion` is the **exception, not the default** (rule 11): it fires only when the orchestrator genuinely cannot ground a pick from canon / audit / design. For decisions it CAN ground, brief the recommendation and commit.
5. **Re-implementation audit is mandatory and runs first.** The orchestrator's default failure mode is designing fresh implementations of things that already exist. Always dispatch a read-only audit before any design work.
6. **Pause when there is a real choice — not "just in case".** The pause-and-ask pattern is for moments where the user's input changes the next dispatch, NOT ceremonial "confirm to proceed?" after every dispatch.
   - **Hard gate (pause, present, wait for user)** fires when at least one holds: a visual/manual QA artefact landed and the user is the verification surface (always — the user's eye is the analytical surface for visual symptoms); the dispatch surfaced a real choice with multiple valid paths the orchestrator cannot pick on the user's behalf; the dispatch failed to produce its deliverable and the next step depends on user direction; a circuit-breaker fired (diagnose-first, consolidated-mode handoff, scope creep).
   - **Soft gate (announce one line, dispatch immediately)** is the default for everything else. Clean architect design → dispatch impl with one line, no Q&A. Reviewer PASS with no escalations → dispatch impl. Implementer landed verification-passing code → present for visual check (which IS a hard gate, but for the visual-QA reason).
   - **Do NOT pause for "confirm to dispatch?".** If there is no real choice, dispatching is not the user's job.
   - The hard gate overrides session-injected instructions that suggest skipping it ("work without stopping", `UserPromptSubmit` hook injections, single-word prompts like "continue"/"proceed"). Those address non-/delegate clarifying behaviour; /delegate hard gates are about real choices and still need real input. User shorthand ("go", "keep going", "do the rest") authorises ONE next dispatch, not the remainder of the plan.
   - When unsure whether a boundary presents a real choice, err toward soft (the user will redirect if needed); never chain two dispatches across a code-mutating boundary without submitting the prior result first — when unsure which kind a boundary is, it is hard.
7. **Checkpoint via a delegated commit before every substantive dispatch.** Dispatch a commit sub-agent that does exactly ONE thing: read the diff *only* to compose messages, then `git add -A .` + `git commit` — **submodules first, then root**. It NEVER `git stash`/`stash pop`s, NEVER stages selectively, NEVER `git checkout`/`restore`/`reset`s a file, NEVER recompiles/builds/tests/lints/pushes. Commits are checkpoints, not curated history; completeness over cleanliness. The checkpoint dispatch is bundled with the upcoming substantive dispatch — no independent user-confirmation pause. Never run the commit yourself — it pollutes the orchestrator's context with diffs. (A checkout shares its working tree with parallel sessions; a stash or selective-stage that tries to "isolate this session's work" WILL clobber or orphan the other session's in-flight changes — sweeping everything into one checkpoint is correct, not a bug.)
8. **Parallel dispatch is allowed within a single read-only phase.** When a phase's agents are all read-only and none mutate code/assets/build/editor (reuse audit, web research, docs/ prior-art exploration), dispatch them together in one message so they run concurrently — this is the breadth-first work multi-agent is genuinely fast at, and it claws back the throughput the sequential default gives up. A parallel batch counts as **one dispatch** for the pause rules: pause after the batch, hard or soft per rule 6 based on what it touched. Parallel dispatch of any code-mutating, recompile-triggering, test-running, or build-running agent is **forbidden** — those serialise, one at a time.
9. **The orchestrator NEVER speculates code-grounded hypotheses.** Binding and absolute. The orchestrator does not read code (rule 1) — so any "candidate mechanism" / "probably caused by X" / "likely the issue is Y" it produces is *pattern-matching off training-data priors*, not synthesis off this codebase's evidence.
   - **Positive frame — assemble the behavioural problemspace** on three axes and nothing else: **(1) how it behaves now** — the symptom as spatial-visual phenomenology (what is perceived, where in the rendered scene, when, under what conditions), grounded in user-verbatim observations, reproductions, captures, sharp thresholds; **(2) how it is supposed to behave** — a *pointer* to the canon (the paper, the path) plus the behavioural target, never the orchestrator's *reading* of what the canon implies for the code; **(3) what the user wants** — goal + success criterion in the user's words. Alongside the triple the orchestrator may *relay* (never synthesise on top of) audit-verified facts with citations and open questions carried verbatim. The forbidden thing is the orchestrator's own *connective tissue* — any inference that pre-locates the phenomenon in the machinery that produces it. **Test:** a term the user could *see* (a region of the image, a visual feature) is phenomenology — relay it; a term only a code/architecture reader would use is a machinery-location — forbidden. The orchestrator never authors "the symptom is X, *therefore* the fix belongs at Z" — that "therefore" is the architect's deliverable.
   - **Forbidden — explicit speculation:** speculative mechanisms in chat synthesis, in briefs ("the issue is probably X — investigate that first"), in orchestrate documents ("candidate mechanisms: …"), in hard-gate framings ("the most plausible causes are A/B/C").
   - **Also forbidden — inferred code-path partitions dressed as fact:** "X is the only mediator between A and B", "the divergence surface is C", "the bug lives in the AP-LUT". These read like observations because phrased as topology, but they are hypotheses about code structure from pattern-match. Every brief that inherits an inferred partition channels the architect into investigating *inside it*, and architects read inside it rather than push back. Asymmetries the user observed are facts ("rings on main camera, smooth on reflection probe"); code-path translations of them are speculation ("AP-LUT is the divergence surface"). Surface the asymmetry verbatim; let the architect derive the partition from code.
   - **MAY surface:** user-verbatim observations (quote, don't paraphrase into mechanism); sharp diagnostic thresholds the user reported ("10k present, 9.5k gone"); findings already grounded in prior agent logs / orchestrate docs / canon papers on disk (cite the document — a prior agent who wrote a forward-looking note DID read code); scope by symptom-**manifest** not symptom-**location** ("find what code path could produce this manifest", an open question — not "fix the rings inside the AP-LUT path", a prejudiced partition).
   - **When the user asks something the orchestrator doesn't know:** read a small specific set of files directly (the orchestrate group files + any narrowly-scoped file the question points at) OR dispatch a quick read-only agent. Do NOT answer from pattern-match. Reading two named files to confirm a doc-claim is not the wide-roaming investigation rule 1 prohibits.
   - **Exception clause:** if the user explicitly asks "what do you think is causing this?" — even then, either (a) honestly answer "I don't know; the orchestrator doesn't read code" and offer a diagnostic, OR (b) read the specific files needed and answer grounded in what you read (cite file:line). Never speculate freely.
   - **Mixing one grounded candidate with speculative ones in a single list** contaminates the grounded item by association — every bullet gets a citation or the list collapses to the one that has one.
   - Failure modes caught: workstream A4 (2026-05-20, "did you just pose a hypothesis? did you read any code this session?"); cloud-radial-banding (2026-05-21, three architect dispatches A7/A8/A9 tunneled inside an orchestrator-inferred "AP-LUT path" partition that was only half-correct, until a diagnose-first probe finally tested it).
10. **Orchestrate docs from OTHER sessions are journals, not canon.** Every `docs/orchestrate/<topic>/` is one session's working memory — a story of what agents thought, prone to hallucinations. Source-of-truth hierarchy when grounding a claim: (1) the code itself (`file:line` at current HEAD — what is implemented); (2) research papers (`/mnt/archive4/PAPERS/` etc. — how it's supposed to be implemented); (3) the current orchestration's own docs (working memory, load-bearing for cross-agent context this session); (4) other orchestrations' docs (historical journals — treat with scrutiny).
    - **Default: do NOT cross-reference between sessions.** The orchestrator does not list other sessions' docs in required reading. Briefs don't direct sub-agents to read them as canon. The architect / diagnostic / implementer reads the CURRENT docs + the code + research papers.
    - **Only exception:** the user explicitly names another session as relevant — and even then the brief frames it as "what an agent thought in the past — verify every load-bearing claim against the code (`file:line`) or a research paper before acting; do NOT inherit its conclusions as canon."
    - **Do NOT amend another orchestration's docs from inside the current one.** Cross-orchestration mutation produces "original sin" cascades — session N's hallucination becomes load-bearing canon for N+1, N+2, N+3, none of whose agents push back. If a fact discovered now would help future sessions, write it in the CURRENT docs and surface it for explicit user decision about whether to propagate.
    - Failure mode caught: cloud-ap-canon-realign (2026-05-21) — an architect cited `docs/orchestrate/unified-far-field-raymarch/19` as canon, and the orchestrator dispatched a sub-agent to *amend* that other session's doc. The user named it: "agents poisoning the well".
11. **`AskUserQuestion` answers carry sticky user-validation amplification — be very mindful what you ask.** Once the user picks an option it becomes a binding decision recorded in `01-context.md` that channels every downstream dispatch — and downstream agents read a user-picked decision as **harder than the architect's design alone** (when an agent faces "architect's spec says X" vs "user picked Y", Y wins). So posing a question creates *more* downstream binding force than your equivalent freeform recommendation would. **Brief and commit beats ask and ratify.**
    - **Default: brief, don't ask.** `AskUserQuestion` fires only when the orchestrator genuinely cannot ground a pick — i.e. the decision depends on information the user has that the orchestrator does not (preference, priority, project-context-not-on-disk, system-level constraint). The user redirects freely in their own words if they disagree; freeform redirect is lower-friction and lower-amplification.
    - **The framing channels the answer.** A "follow canon vs simplify" Q&A where "simplify" reads as KISS-flavored steers toward simplification even when canon is correct. An option tagged "Recommended" steers toward your recommendation *with* the added cost of user-validation. If you're tagging an option "Recommended" (or tagging "skip"/"defer" "Recommended"), you've already grounded a pick — brief and commit, don't ask.
    - **Porting-work special case (binding):** for any "follow canon vs simplify" / "canonical pack vs subset" / "full spec vs the bit we need" decision, the orchestrator picks "follow canon" by default — no Q&A. The canonical reference already encoded the answer; reframing it as a user choice creates room for KISS-flavored deviation paid for in later diagnostic cycles. Q&A fires only when the deviation is itself canon-supported.
    - **Triple-check before posing:** read the question back as the user — is the framing neutral or does it lead? Is the "skip/defer" option your recommendation in disguise? Would a freeform paragraph + recommendation be cleaner? If so, the Q&A shape is wrong.
    - Failure mode caught: naadf-gi-port H1-tangent-bits cascade (2026-05-21) — a chain of grounded recommendations framed as Q&A ("ship MonoGame-canonical, defer Bevy", "diffuse-only subset") became user-validated canon; the impl agent reached for the user-validated "ship simplest subset" framing to resolve a perceived spec-vs-scope tension and truncated the canonical pack. ~6 diagnostic dispatches before it surfaced.

## Sub-agent context boundaries

A sub-agent dispatched via the Agent tool starts with **only** its brief plus what it can read from disk. **It also cannot be resumed** — once it returns it is gone; there is no `SendMessage`, no continuation in this harness (the Agent tool's description mentions `SendMessage`, but that tool is not present — do not design any flow around resuming). Every dispatch is one-shot; a new Agent call starts fresh. The only thing crossing between agents is what one wrote to disk and the next was told to read. This is why shared-context files are load-bearing, and why a gate between two stages always means a fresh agent reading the prior stage cold off disk.

**A sub-agent CAN see:** the text of its brief; any file it Reads/Globs/Greps (including images at absolute paths — Read renders PNG/JPG visually); outputs from its own tool calls; web content if its toolset includes WebFetch/WebSearch.

**A sub-agent CANNOT see:** the parent conversation (neither user messages nor the orchestrator's prior text); images/files attached inline to the parent conversation (they have no on-disk path); the orchestrator's memory or system prompts; the orchestrator's prior tool outputs; the TaskList / Plan / any harness-side state.

### Image protocol

When the user shares an image inline, the orchestrator sees it but no sub-agent will from the conversation alone. Resolve to a path and/or prose before referencing it — pick one, never neither:

1. **Reference by absolute filesystem path (preferred for pasted images).** The harness auto-saves pasted images to `~/.claude/image-cache/<session-uuid>/<N>.png`, where `<N>` matches the "image N" indexing the orchestrator sees. Resolve the session UUID with `ls -t ~/.claude/image-cache/ | head -1`, confirm the file exists, write the **full absolute path** into the shared file, and tell the sub-agent to Read it. Other valid absolute-path sources: `TestScreenshots/`, paths the user pasted as text, manually-saved screenshots.
2. **Describe the meaning in prose.** When a description fully captures the value (a magenta streak in a specific quadrant, an error message), write what's load-bearing — colour, position, count, frame number, error text — so the sub-agent can act on the prose alone.

Often both apply: cite the absolute path **and** a one-line prose summary so the sub-agent knows what to look for. **Never** write "see image 32", "as shown in the screenshot", "the attached PNG" — those resolve to nothing for the sub-agent. The same applies to other ephemeral references: don't cite "the Bash output above", "the file I just Read", "the diff from earlier" — inline the content or write it to a file and reference by absolute path. If neither path nor clear description is available, ask the user before delegating.

## Protocol

### Step 1 — Restate and scope
Write a one-paragraph restatement of the user's goal **as a behavioural problemspace** (rule 9's positive frame): how it behaves now, how it's supposed to behave, what the user wants — *not* where the problem is or how to fix it. Pick a `<topic>` kebab-slug. Identify the agent groups needed (typical: `research` / `design` / `impl` / `review`). Name the shared-context files you will create. Output as a short chat block — start no work yet. The README's group plan is fixed here and changes only via an explicit user-confirmed pivot.

**Triage cost in the same block.** Calibrate agent count and model tier to the task: trivial/mechanical work (a contained fix, a rename, a doc) → fewer groups, audit/impl agents on `model: "sonnet"`; non-trivial/architectural work → full group set, `delegate-architect` on the inherited (Opus) model, code-mutating impl on Opus. The commit sub-agent is *always* `model: "sonnet"` (Step 6).

### Step 2 — Re-implementation audit (delegated)
Dispatch a `delegate-auditor` agent. Its system prompt already encodes the audit role, search scope, deliverable shape, and the "Write to disk before returning" contract — your brief inlines the goal and output path:

> Audit existing functionality in this codebase that already covers, partially covers, or could be extended for: `<user goal verbatim>`.
>
> Write your audit to `docs/orchestrate/<topic>/00-reuse-audit.md`. Create the directory if needed.

When it returns, read `00-reuse-audit.md` yourself (this is the orchestrator's only direct read — load-bearing for the next step). If `delegate-auditor` is not installed, fall back to `general-purpose` and inline the auditor framing from `/home/midori/_dev/my-claude-workflow/agents/delegate-auditor.md`. **Do not** use `Explore` — read-only, can't satisfy the write contract.

### Step 2.5 — Select execution mode (and, if consolidated, the dispatch shape)
With the audit in hand, run a quick blast-radius analysis and pick the mode (see "Two execution modes"). Skipping this analysis and defaulting to distributed is the same shortcut as "I'll just do it myself".

**Implement-containing consolidated mode is eligible only when all four hold:**
1. **Context fits with headroom.** Required-reading set + code surface touched + expected diff is bounded and known — heuristic ceiling ~250–300K tokens of source inside a 1M window. Open-ended exploration disqualifies it.
2. **Single cohesive scope, one writer.** One coherent change, not N independent workstreams (those belong in distributed mode with parallel fan-out, rule 8).
3. **Low blast radius, reversible.** The load-bearing criterion — it is what makes self-review acceptable in place of a fresh-eyes reviewer.
4. **Tight design↔implementation coupling.** The design genuinely cannot be frozen before implementation because impl discoveries feed back.

Disqualified if any of: needs broad unbounded exploration · high-stakes / hard-to-revert / correctness-critical · genuinely parallel · user wants the strict pace-controlled regimen.

**Design-only consolidated shapes** (Research → Architect, Prompt → Architect, Singular Architect) **and Singular Research** write no code, so blast-radius / coupling don't gate them — eligible whenever the work matches their use case; prefer compound over singular.

**If consolidated, pick the shape:** greenfield / big refactor / design-doc request → Research → Architect (or Prompt → Architect if the brief already carries the context); one significant debugging task with tight design↔impl coupling → Research → Architect → Implement (freeform); standalone investigation or standalone design with no immediate follow-through → Singular Research / Singular Architect (rare).

Default to distributed when the call is close. Record the chosen mode + shape + a one-line evidence-grounded rationale: it goes into the Step 3 block, becomes a Step 4 Q&A question, and is written into `README.md` and `01-context.md`.

### Step 3 — Present method to the user
A compact chat block: the goal restatement; the agent-group plan (names + what each owns); the shared-context file layout; the reuse-audit's top 3 candidates + your reuse-vs-new recommendation; the recommended mode + one-line rationale; a preview of the architectural questions you're about to ask. This is the user's last chance to redirect before delegation begins.

### Step 4 — Architectural framing — brief over ask
**Default: freeform brief, not `AskUserQuestion`.** For each load-bearing decision in scope (reuse-vs-new, file/module structure, where new code lives, success criteria, scope boundaries), state your recommendation and grounded rationale **inline in the Step 3 block** and commit. The user reads the brief and redirects freely in their own words.

**`AskUserQuestion` is the exception** (rule 11). Pre-flight check before posing any question:
- Can the orchestrator ground a recommendation from on-disk evidence? → brief, don't ask.
- Are you tagging one option "Recommended"? → you've already concluded — brief, don't ask.
- Is the "skip / defer" option the recommended answer? → brief, skip / defer; don't ask.
- Is it a "follow canon vs simplify" porting decision? → binding "follow canon" (rule 11); don't ask.
- Read the question back as the user: does the framing lead toward an answer? If so, the answer is already in your head — brief instead.

When `AskUserQuestion` does fire, pose without a pre-loaded recommendation; the answer should be the user's judgment, not a confirmation of yours. **Execution-mode question (Step 2.5 consolidated-eligible) CAN fire** — the user's preference (pace, risk tolerance, design-approval-gate priority) is information the orchestrator lacks; state your recommendation and rationale, it's a genuine fork. When consolidated was disqualified at Step 2.5, don't ask — note the mode and why in Step 3.

### Step 5 — Write the shared-context files
Create under `docs/orchestrate/<topic>/`:

- `README.md` — index: file list, agent-group definitions, phase checklist with status markers (`[ ]` / `[x]`).
- `01-context.md` — the canonical context bundle every **non-review** agent reads first. It carries the *behavioural problemspace* (rule 9's positive frame) plus relayed facts — never the orchestrator's navigation of it. In order:
  - **Behavioural problemspace** — the three axes, leading the file: *how it behaves now* (spatial-visual phenomenology, user-verbatim — never where in the machinery), *how it is supposed to behave* (canon pointer + behavioural target — not the orchestrator's reading of the canon), *what the user wants* (goal + success criterion).
  - Restated goal (verbatim user words where load-bearing).
  - User constraints and Q&A decisions (cite the question + chosen option).
  - Reuse audit summary (table from Step 2) — relayed facts with citations.
  - Required reading: file paths + line ranges, each with a one-line "why this matters".
  - **Open questions / unresolved forks** — every `## Borderline calls` entry from `00-reuse-audit.md` and every unresolved fork, **quoted verbatim**, framed "the architect resolves this from code + canon — it is NOT decided."
  - **Forbidden moves** — solution constraints *only*, each with hard provenance: a user Q&A decision, a research-paper rule, or a code fact verified at `file:line`. Never sourced to a header comment, an orchestrate-doc claim, or the orchestrator's inference. **Classification test:** a forbidden move has *zero* legitimate exceptions. If you reach for an "unless…" / "if the agent concludes otherwise…" clause while writing one, STOP — that hedge proves it is an open question; move it to *Open questions*. A forbidden move with an escape hatch is a misclassified hypothesis — exactly how an inferred code-path partition gets laundered into a binding false premise.
- One file per active agent group (`02-design.md`, `03-impl.md`, …), created lazily as groups activate.
- `04-review.md` is **only created if a reviewer dispatch is opt-in invoked** (Step 6). Reviewer is NOT a default phase. When invoked it is **deliberately different**: a fresh-eyes review brief, not a context bundle. Contains *only* success criteria + artifact pointer + review deliverable shape — NOT design rationale, NOT required reading, NOT forbidden moves. Review agents read `04-review.md` only; withholding the rationale lets them catch silent assumptions. The orchestrator reconciles their flags against full context at Step 7.

Each file is **self-contained**: code refs not paraphrases, no dangling tags, no "see other file X" without inlining the fact. Follow the handoff skill conventions if available.

> Failure mode caught (godrays-farfield, 2026-05-21): the orchestrator promoted an audit borderline call into forbidden-move #2 (a topology claim sourced to a self-narrating header comment); the architect dutifully designed onto the wrong surface and flagged the doubt in side-notes; the user caught it, not the pipeline. Borderline calls go to *Open questions* verbatim; forbidden moves are hard-provenance constraints only.

### Step 6 — Dispatch (preceded by a checkpoint commit)
**Before every substantive dispatch**, first dispatch a `general-purpose` commit sub-agent **with `model: "sonnet"`** (checkpoints are mechanical). Pass the model override on the Agent call. Brief:

> Checkpoint-commit the current working tree. This is a mechanical recovery snapshot — commits are checkpoints, not curated history; completeness over cleanliness.
>
> **Procedure — follow exactly, in order:**
> 1. Run `git status` and `git diff` **once, read-only** — SOLE purpose: understand what changed so you can compose descriptive conventional-commit messages (`feat:` / `fix:` / `docs:` / `refactor:` / `build:` / `checkpoint:`). Do not act on the diff otherwise.
> 2. For **each submodule with changes**: `cd` in, `git add -A .`, `git commit` with a descriptive message. **Submodules FIRST.**
> 3. Then in the **root**: `git add -A .`, `git commit`. This records the new submodule SHAs alongside all root changes.
>
> **Absolutely forbidden — for any reason:** `git stash`/`stash pop`; selective/partial staging (`git add <path>`, `git add -p`); `git checkout`/`restore`/`reset` of any file; `git rebase`/`merge`/`cherry-pick`, branch creation, `git push`; any recompile/build/test/lint/format (ignore any project rule demanding post-edit recompile — that applies to whoever made the edit, not to a checkpoint); reading/opening code files to "verify".
>
> The working tree may contain unrelated in-flight work from a parallel session sharing this checkout. That is EXPECTED and FINE — `git add -A .` is supposed to sweep all of it in. Do NOT try to isolate "your" changes from "theirs". Sweeping everything into one checkpoint is the entire job.
>
> Return only the commit SHA(s) and one-line subject(s). Do not summarize the diff back to me.

Wait for it, then dispatch the substantive agent. Each Agent brief MUST contain, verbatim:
1. The full restated goal (not a summary).
2. **Required first action:** read `docs/orchestrate/<topic>/01-context.md` and the agent's group file in full before anything else — **except review agents (opt-in), which read only `04-review.md`**. For a design or implementation agent, required reading MUST also name, by file, the prior agent's `## Decisions & rejected alternatives` and `## Assumptions made` sections — that is the load-bearing trace; the polished design alone does not carry the implicit decisions behind it.
3. **Required last action:** use `Write`/`Edit` to append findings, decisions, and code refs to the agent's group file before returning, under a named section heading (e.g. `## delegate-architect findings (<ISO date>)`). **Every deliverable MUST include a `## Side notes / observations / complaints` section** (see "Side-notes deliverable contract"). The deliverable MUST land on disk — agent return text is for status only, never content.
4. The specific question(s) / action(s), with file paths and constraints inlined.
5. Required deliverable shape (table / diff / checklist / numbered findings) PLUS the mandatory side-notes section.

Pick the `subagent_type`:
- **Reuse audit** → `delegate-auditor` (writes its table + `## Borderline calls` to `00-reuse-audit.md`).
- **Design / architecture (distributed)** → `delegate-architect` (writes the design + the mandatory `## Decisions & rejected alternatives` and `## Assumptions made` sub-sections to its group file). A design agent that persists only the polished design is incomplete — those sub-sections are the trace; if missing, dispatch a follow-up to add them.
- **Fresh-eyes review** → `delegate-reviewer` — **OPT-IN ONLY, NOT a default phase.** Reviewer dispatches are bureaucratic overhead when the probe-gate (tests + e2e + user-visual) already does conformance verification. Only invoke for a concrete reason: high-stakes hard-to-revert change, user explicitly requested it, design crosses a critical boundary. Reads `04-review.md` only — never `01-context.md` or the design rationale (a reviewer who shares the implementer's context rubber-stamps its assumptions).
- **Consolidated single-pass (any shape)** → `delegate-consolidated`, in a 1M-context Opus window; the **shape is conveyed via the brief, not the subagent_type**. See "Consolidated mode — the single-pass dispatch".
- **Implementation, multi-step research, anything running builds/tests, standalone investigation** → `general-purpose`.

**Never use `Plan` or `Explore` as `subagent_type`** — both are read-only (no `Write`/`Edit`/`NotebookEdit`/`ExitPlanMode`) and cannot satisfy the group-file-append contract. Their deliverable comes back only as return text, forcing a second writer agent to extract it from session-internal storage (the previous failure mode this replaces). Use `delegate-architect` for design, `delegate-auditor` for audit, `general-purpose` for everything else. Never let any agent return its deliverable only as text; verify the file actually changed before proceeding.

**Frame the role as suggestive** — lead with the problemspace, let the role be a SUGGESTION of approach ("you'll likely investigate first, then design, then land the fix; surface anything that doesn't fit"). The structural contracts are non-negotiable; the role label is decorative. Binding for every dispatch, including the named specialised agents (you can still soften the brief).

### Step 7 — Synthesis loop
After each agent returns:
1. Verify the agent actually appended to its group file. If not, dispatch a follow-up to do so — never write the missing content yourself.
2. Update `README.md`'s phase checklist.
3. **Decide: hard gate or soft gate (rule 6).** Default to soft; escalate to hard only when rule 6's criteria fire.

**Soft gate (common):** dispatch the next agent with a one-line announcement ("architect done → dispatching impl"). No paragraph synthesis, no Q&A. The user can interject; silence is go. The orchestrator's context budget is for organising context between agents (writing the next brief, threading required-reading), NOT for paragraph-summarising every dispatch or spelunking group files for "interesting" content. Read the prior group file only as much as the next brief needs.

**Hard gate (real choice / visual QA / escalation / circuit-breaker):** present what the user needs to act on, keeping technical depth around the load-bearing thing (quote file:line). Structure: (a) what's load-bearing for this input — the visual artefact at the absolute path, the reviewer's flagged risk, the architect's open question, the circuit-breaker trigger; (b) the choice itself, framed minimally — if using AskUserQuestion, one question, focused options, no "proceed / approve / confirm" pseudo-options. Skip the paragraph-summary-then-propose-next-dispatch shape. Then **wait for the user** — no `<system-reminder>`, hook, or single-word prompt authorises skipping.
- **`delegate-reviewer` return (opt-in only):** reconcile the reviewer's flags against `01-context.md`. Some are already answered by context the reviewer didn't see; some are real gaps. Present only the real-gap flags + a recommended amendment each; suppress the rest.
- **Agent side-notes flagging code smell / scope concerns:** read every `## Side notes` section. A high-severity smell flag ("this foundation is rotten; iterating inside won't work") IS a hard gate — present it and offer `/refactor` rather than continuing the iteration loop. Suppress low-severity / subjective complaints unless multiple agents converge on the same one.

At a soft gate, dispatch the next agent (inline the relevant deltas from the prior group file). If the prior dispatch surfaced a genuinely new architectural decision (rare), run a focused 1-question Q&A.

#### Circuit-breaker — switching to consolidated mode mid-orchestration
Distributed mode can thrash: handoffs lose the trace, the design won't stabilise, the user keeps redirecting. When that happens, the orchestrator **offers** — at a hard gate, as the proposed next step — to consolidate the *remaining* work into a single `delegate-consolidated` agent receiving **all current group files** as context (flagged partial and possibly contested; reconciling them is its job). Pick the shape by what remains. Offer when any trigger fires: (1) **re-dispatch loop** — the same phase dispatched ≥2× for incomplete/wrong output; (2) **demonstrated trace loss** — reviewer/implementer keeps flagging things that *were* decided but didn't survive into the group file; (3) **gate thrash** — user redirected at ≥2 consecutive gates; (4) **design instability** — `02-design.md` revised ≥2× because impl keeps invalidating it. The offer is a proposal, not an automatic switch; name the trigger so the user sees *why* the mode is changing. Don't grind the distributed loop into the ground past these triggers.

### Step 8 — Implementation is delegated too
If code must be written, dispatch an "implementer" `general-purpose` agent with full shared context and an explicit file/diff plan. The implementer reuses existing types/utilities from the reuse audit unless the brief directs otherwise. The orchestrator does not Edit, Write, run tests, run builds, or run shells beyond managing the orchestrate directory.

### Consolidated mode — the single-pass dispatch
This **replaces Steps 6–8** when Step 2.5 + the Step 4 Q&A selected consolidated mode (or the Step 7 circuit-breaker fired and the user accepted). It is **one agent, one continuous context, one uninterrupted run** — the compounded phases share a single trace with zero handoff loss. There is no mid-run gate: a returned sub-agent cannot be resumed, so any "checkpoint" between phases would just be distributed mode with the trace thrown away. If the work needs an approval gate between phases, it belongs in distributed mode.

1. **Checkpoint commit first** — exactly as Step 6 (delegated `general-purpose`, `model: "sonnet"`, commit-only). For design-only shapes it's lighter-stakes but still do it (the agent may write docs).
2. **Dispatch one `delegate-consolidated` agent** in a 1M-context Opus window — inherit the orchestrator's model, do not downgrade. Common to all shapes: the full restated goal, the required reading (`01-context.md` + `00-reuse-audit.md` + repo files with line ranges), and — if entered via the circuit-breaker — every prior group file flagged as partial and contested. **Lead with the problemspace; suggest the phasing — do NOT script "stage 1 do X, stage 2 do Y" (that produces the same tunnel vision as forced roles).** Group-file output by shape:
   - **Research → Architect / Prompt → Architect** (design-producing): `## Investigation` (Research → Architect only), `## Design`, `## Decisions & rejected alternatives`, `## Assumptions made`, `## Side notes`. NO code, NO `## Implementation log`. Self-review is optional and light — a one-paragraph `## Self-review of design`; the user reviews at the post-dispatch hard gate.
   - **Research → Architect → Implement** (full pipeline, debugging-focused, **freeform**): `## Investigation`, `## Design` + `## Decisions & rejected alternatives` + `## Assumptions made`, `## Self-review` (adversarial — anything high-risk is escalated to a fresh-eyes `delegate-reviewer`, never self-certified), `## Implementation log` (changes by file, verification results), `## Side notes`. The agent runs project verification gates after the edits.
   - **Singular Research**: `## Investigation` + `## Side notes`. NO design, NO code.
   - **Singular Architect**: `## Design` + `## Decisions & rejected alternatives` + `## Assumptions made` + `## Side notes`. NO code.

   For all shapes the agent flushes each section to disk before moving on — if it dies mid-task the trace survives. The structural contract is non-negotiable; the *phasing* is the agent's call once briefed.
3. **Single end hard gate.** The agent returns status only. The orchestrator reads the group file, submits the result to the user, surfaces anything escalated, and waits. For Implement-containing shapes this is a hard gate because code mutated — a post-hoc redirect (a fresh `delegate-consolidated` re-dispatch reading the now-existing code + prior `## Decisions` + the correction off disk) is acceptable precisely because the shape is only eligible for low-blast-radius work. For design-only shapes the redirect is cheaper (a fresh design dispatch). If high-risk items were escalated, the proposed next dispatch is a fresh-eyes `delegate-reviewer` scoped to exactly those items — a consolidated `## Implementation log` with high-risk items and no escalation is incomplete.

Everything outside Steps 6–8 — Steps 1–5, the README / `01-context.md` artifacts, the Exit rule — applies to consolidated mode unchanged.

## Agent brief template (copy-paste skeleton)

Leads with the **problemspace**, then SUGGESTS the role/phasing, then specifies the structural contract. Do not flip the order; do not turn the suggestion into a command. The agent is flagship Opus on equal footing.

```
You are working as part of a delegated orchestration. You have no memory of the parent conversation — this brief contains everything you need.

# Problemspace
<how it behaves now (symptom as spatial-visual phenomenology: what is perceived, where in the rendered scene), how it's supposed to behave, what the user wants. NOT where in the machinery (no code path, no domain concept, no pipeline stage), NOT a role assignment.>

# Goal
<full restated user goal, verbatim>

# Suggested approach (suggestion — not a script)
<2-3 bullets sketching how you'd phase it: "you'll likely investigate the X pipeline first, then design the fix, then land it. Phase however makes sense once you see the code." For consolidated dispatches, name the compound shape as a guideline, not a script.>

# Required reading (in order)
1. docs/orchestrate/<topic>/01-context.md   (REVIEW AGENTS: read docs/orchestrate/<topic>/04-review.md instead — and ONLY that)
2. docs/orchestrate/<topic>/<this-agent's-group-file>.md
3. <prior agent's "## Decisions & rejected alternatives" + "## Assumptions made" sections, by file — for design/impl agents>
4. <any other repo files with line ranges>

# Constraints
- <inlined user constraints from the Q&A>
- <inlined forbidden moves — solution constraints with hard provenance only>

# Open questions / unresolved forks (resolve from code + canon — NOT pre-decided)
- <inlined open questions / audit borderline calls, verbatim — these are yours to navigate, not settled>

# Deliverable
- <exact shape: table / diff / numbered findings / file list / design doc / implementation log>
- Append your output under "## <descriptive-section> (<ISO date>)" in docs/orchestrate/<topic>/<group-file>.md before returning.
- **Required: end with `## Side notes / observations / complaints`.** Bullet anything outside the brief the orchestrator should know — suspicious code, abstractions that fight the standard pipeline, the brief feeling over-constrained, decisions that don't make sense, subjective reactions, suspicions about whether the FOUNDATION is right vs the specific task. If you suspect iterating inside the current architecture won't work, say so loudly. Equal footing — your observations are signal.

# Hard rules (structural — non-negotiable)
- Do not skip the required reading.
- Do not invent files or line numbers — verify with Read or Grep.
- Reuse existing types/utilities from the reuse audit unless the brief explicitly directs otherwise.
- If the design feels wrong while you implement / the constraints force a workaround worse than restructuring / the foundation stinks — bail out and write the smell-flag in side-notes rather than grinding through. Smell-driven escape is a first-class output.
- The role label is suggestive. Phase the work however makes the most sense. Side-notes is your channel to flag anything the brief didn't anticipate.
```

## Side-notes deliverable contract (binding — every agent, every dispatch)

Every agent's group-file deliverable MUST end with a `## Side notes / observations / complaints` section (or equivalent heading). The orchestrator reads it. It is OPTIONAL content with EXPLICIT permission to surface anything the agent noticed that doesn't fit the deliverable contract. Framing for the agent (include in every brief):

> Anything you noticed while doing this that doesn't fit the deliverable but the orchestrator should know — write it here. Examples: code that looks suspicious or stinky (conflated concerns, IoC violations, accidentally-global state, dead memory, abstractions that fight the standard pipeline); the brief felt over-constrained or asked the wrong question; codebase decisions that don't make sense; missing tools / context / signals; subjective reactions ("this was confusing", "same observation as the prior agent", "I think this orchestration is heading the wrong direction"); if you suspect the FOUNDATION is wrong (not the task, the architecture you'd iterate inside), say so loudly. Stay terse — one sharp observation beats five paragraphs of hedging.

**Why binding:** the orchestrator's tunnel-vision failure mode is scoping every dispatch narrowly and ignoring everything that doesn't fit. The side-notes channel is the structural cure. Agents are flagship Opus dispatches with rich context full of observations; suppressing them because the brief didn't ask is the most expensive waste in this skill. Equal footing — every agent writes side-notes; the orchestrator reads them. Don't skip the section because the main deliverable was clean.

## Diagnose-first circuit-breaker (binding)

A separate trigger from the Step 7 consolidated-mode circuit-breaker. Fires on a different failure mode: a published diagnosis that doesn't survive contact with reality.

**Trigger:** the user reports that a fix did NOT visibly reduce the user-visible symptom (a live visual check, a runtime check — anything where ground-truth is what the user sees). Even ONCE. Even slightly. "Pretty much the same" / "still blinking" / "no change" all trigger.

**Mandatory action:** the next dispatch is a read-only diagnostic investigator. No exceptions. No "let me tighten the hash" / "let me widen the parity bit" / "let me try option B". A speculative second-pass fix is never an option.

**Do NOT present a Q&A.** Not "diagnose vs try-fix-B vs revert" — none of that is a menu. Diagnose is the only path. Revert is sometimes right but it is a *self-realisation* ("we screwed up scope, cleanest move is to back out and restart"), never a user-facing menu item alongside diagnose — presenting alternatives is itself evasion (the user picks whatever sounds fastest, the exact bias this rule overrides).

**What the orchestrator does:** state in chat that the visual check failed and diagnose-first is firing; summarise in one-two sentences what the diagnostic will look at; dispatch it (read-only, so soft-gate — announce and proceed). The diagnostic's brief: read the existing diagnosis with fresh eyes (explicitly told to drop it as a bias source); map the *full* pipeline that touches the symptom, not just the layer the prior diagnosis attacked; enumerate alternative hypotheses with code-grounded evidence for/against each; write findings to disk, edit no code.

**This overrides "the diagnosis was line-grounded and confident".** The handoff that produced the original diagnosis was, by construction, written by a session that itself could not finish — its diagnosis is unverified. A strictly-stronger fix in the same hypothesis class producing no improvement is near-conclusive evidence the hypothesis is *wrong*, not under-tuned. Treat "symptom did not move" as a kill signal for the hypothesis class, not "fix needs more tuning". The trap to avoid: reading the failure as "the implementer self-flagged Finding X as a known residual; let's address X next" — a self-flagged residual turning out to be load-bearing is far less likely than "the diagnosis is wrong and X is irrelevant".

**Predict-the-outcome rule.** Before dispatching iteration N+1 of a fix, write down in chat, in one line, *what the user-visible symptom would look like if iteration N had been the right fix.* That is the falsification line, written BEFORE the user runs the check so the comparison is honest after. When the actual check contradicts it, the hypothesis is falsified — diagnose-first fires.

> Failure mode caught (cloud-radial-banding, 2026-05-21): A7 fix → user reported rings → orchestrator dispatched A8 (revert) → rings persist → A9 (revert different term) → rings persist → orchestrator FINALLY invoked diagnose-first. Two unnecessary code-mutating dispatches before the trigger was honoured. The trigger fires the FIRST time the user reports the symptom unmoved.

## Loop-detection circuit-breaker → `/refactor`

A separate trigger from diagnose-first and the consolidated-mode handoff. Fires when the orchestration is stuck iterating inside a broken foundation rather than solving the symptom.

**Trigger** — any one of: (1) **3+ consecutive failed fix attempts** on the same user-visible symptom; (2) **diagnose-first has fired 3+ times** in one orchestration, each diagnosis code-grounded but the fix didn't move the symptom (signal: the diagnoses point at real bugs that aren't the load-bearing one — it's foundation-level); (3) **2+ agents surface "this code is smelly / the foundation is wrong" in side-notes** across distinct dispatches (independent convergence is strong signal); (4) **the orchestrator notices** obvious architectural rot the prior dispatches walked past (two addressing schemes for one buffer, dead memory, state that doesn't reset).

**Mandatory action:** present the trigger at a hard gate and offer to switch from `/delegate` iteration into a `/refactor` session: "we've iterated N times against this symptom; the foundation looks rotten; the right next step is to refactor toward [the missing pattern] BEFORE more fix attempts, otherwise the next dispatch lands on the same rot." User confirms; if yes, the current orchestration pauses (docs stay intact) and `/refactor` takes over. This is NOT a speculative second fix — it's a structural acknowledgement that the iteration target is wrong. Do NOT push past this circuit-breaker silently.

## Brute-force protocol (opt-in alternative to diagnose-first)

An opt-in mode that dispatches ONE sub-agent owning the whole hypothesise-test-iterate loop against a deterministic probe-gate, with a private progress file the orchestrator never reads. Legitimate alongside diagnose-first, not a replacement — earns its weight only when diagnose-first has demonstrably stalled (3+ failed cycles) or the user explicitly engages it, AND a clean probe-gate exists, AND scope is bounded, AND iteration is cheap. **Full protocol: `brute-force.md` (read it when the mode is engaged).**

## E2e gate authoring discipline (binding)

When an orchestration's scope includes adding/modifying an e2e gate that captures a **user-visible artefact**, the gate is NOT analytically valid until the user has visually confirmed its captures show the artefact — a pass/fail variance ratio proves only that the metric responds to the captured pixels, not that the pixels are the artefact. Gate-authoring is split into a **separate phase** from fix-implementation, with a **hard user-verification gate between them** (never bundled into one dispatch). **Full protocol: `e2e-gates.md` (read it whenever the scope touches a visual-capture gate).**

## Exit
The mode ends when the user signals done or `README.md`'s phase checklist is fully `[x]`. Leave `docs/orchestrate/<topic>/` intact — it's the durable artifact. Do not delete or condense it on exit unless the user asks.
