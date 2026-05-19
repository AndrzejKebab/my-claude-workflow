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

**Distributed mode (default).** Orchestrator + separate auditor / architect / reviewer / implementer agents, phase gates, shared-context files. Buys context isolation and a genuinely independent fresh-eyes reviewer. Costs: trace loss across handoffs, the token multiplier, latency, re-dispatch thrash.

**Consolidated mode.** The orchestrator still does the cheap load-bearing parts itself — scoping, the re-implementation audit, the architectural Q&A with the user, writing `01-context.md`. Then it dispatches **one** agent in a 1M-context window that designs → independently self-reviews → implements → logs, in a single uninterrupted run, flushing each stage to its group file as it goes. One continuous context throughout — the full reasoning trace carries from design into implementation with zero handoff loss, which is the entire point of the mode. The price is named and real: there is no design-approval gate *before* code is written (a returned sub-agent cannot be resumed in this harness — see "Sub-agent context boundaries"), and the review is *self*-review, not fresh-eyes. Both are bounded by the Step 2.5 eligibility criteria — consolidated mode is only for low-blast-radius, reversible work — and it carries an escalation valve (it must escalate high-risk findings to a real `delegate-reviewer`). If the work needs a design-approval gate before implementation, that is distributed mode's native structure — use distributed mode.

The orchestrator selects a mode at **Step 2.5** and the user confirms it in the **Step 4** Q&A. Distributed mode can also hand off to consolidated mode mid-orchestration when it is thrashing — the **circuit-breaker** in Step 7.

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

### Step 2.5 — Select execution mode
With the audit in hand, run a quick blast-radius analysis and pick the execution mode (see "Two execution modes" above). **Consolidated mode is eligible only when all four hold:**

1. **Context fits with headroom.** The required-reading set + the code surface the task touches + the expected diff is bounded and known — heuristic ceiling ~250–300K tokens of source, leaving working room inside a 1M window. Open-ended codebase exploration disqualifies it.
2. **Single cohesive scope, one writer.** One coherent change, not N independent workstreams. Genuinely parallel breadth-first work belongs in distributed mode (with parallel fan-out, rule 8).
3. **Low blast radius, reversible.** A bad outcome is cheap to catch and cheap to revert. This is the load-bearing criterion — it is what makes self-review acceptable in place of a fresh-eyes reviewer.
4. **Tight design↔implementation coupling.** The design genuinely cannot be frozen before implementation because implementation discoveries feed back into design.

**Consolidated mode is disqualified if any of:** the task needs broad unbounded exploration · the change is high-stakes / hard-to-revert / correctness-critical · the work is genuinely parallel · the user explicitly wants the strict pace-controlled regimen.

Default to distributed mode when the call is close — it is the conservative choice and the one the user invoked /delegate to get. Record the chosen mode and a one-line rationale grounded in the "Two execution modes" evidence: it goes into the Step 3 block, becomes a Step 4 Q&A question, and is written into `README.md` and `01-context.md`.

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
- One file per active agent group, e.g. `02-design.md`, `03-impl.md`, `04-review.md`. Created lazily as groups activate.
- `04-review.md` is **deliberately different**: it is a fresh-eyes review brief, not a context bundle. It contains *only* the success criteria (extracted from the Q&A), a pointer to the artifact under review (diff, files, or group file), and the review deliverable shape. It does **not** contain the design rationale, the required-reading list, or the forbidden-moves list. Review agents read `04-review.md` and **not** `01-context.md` — withholding the rationale is what lets the reviewer catch assumptions the implementer silently baked in (generator–verifier loops work better with fresh context). The orchestrator reconciles the fresh-eyes review against full context in the Step 7 synthesis.

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
2. **Required first action:** read `docs/orchestrate/<topic>/01-context.md` and the agent's group file in full before doing anything else — **except review agents, which read only `04-review.md`** (see Step 5). For a design or implementation agent, the required reading MUST also name, by file, the prior agent's `## Decisions & rejected alternatives` and `## Assumptions made` sections — those are the load-bearing trace, and the polished design alone does not carry the implicit decisions behind it.
3. **Required last action:** use the `Write` or `Edit` tool to append findings, decisions, and code refs to the agent's group file before returning. Specify the section heading the agent should append under (e.g. `## delegate-architect findings (<ISO date>)`). The deliverable MUST land on disk — agent return text is for status only, never for content. (`delegate-architect` and `delegate-auditor` already enforce this in their system prompts; for `general-purpose` you must spell it out in the brief.)
4. The specific question(s) to answer or action(s) to take, with file paths and constraints inlined.
5. Required deliverable shape (table / diff / checklist / numbered findings).

Pick the right `subagent_type`:

- **Audit / re-implementation reuse search** → `delegate-auditor` (writes its table + `## Borderline calls` to `00-reuse-audit.md` directly).
- **Design / architecture plan** → `delegate-architect` (writes the design to its group file directly, including the mandatory `## Decisions & rejected alternatives` and `## Assumptions made` sub-sections).
- **Fresh-eyes review / verification** → `delegate-reviewer` (reads `04-review.md` only — never `01-context.md` — and writes its review to the review group file directly).
- **Consolidated single-pass design→review→implement** → `delegate-consolidated` (consolidated mode only — designs, self-reviews, implements, and logs in one uninterrupted 1M-context run; see "Consolidated mode — the single-pass dispatch").
- **Implementation, multi-step research, anything that runs builds/tests** → `general-purpose`.
- **Specialized agents (code-reviewer, etc.)** where they exist and have Write tools.

**Never use `Plan` or `Explore` as `subagent_type` in /delegate.** Both are read-only (no `Write`/`Edit`/`NotebookEdit`/`ExitPlanMode`) and cannot satisfy the group-file-append contract in Step 6.3. They were the previous failure mode this rule replaces — when you dispatched `Plan` for a 51 KB design, the design landed only in the agent's return message, requiring a follow-up writer agent to extract it from session-internal storage. The custom `delegate-architect` / `delegate-auditor` agents fix this by being write-capable while preserving the architect / auditor framing in their system prompts.

### Step 7 — Synthesis loop
After each agent returns:

1. Verify the agent actually appended to its group file. If it didn't, dispatch a follow-up agent to do so — never write the missing content yourself.
2. Update `README.md`'s phase checklist.
3. **Decide: hard gate or soft gate (rule 6).** This is the structural pivot — do not default to "always pause + write paragraph + ask confirm". Default to soft (announce one line, dispatch next agent immediately) and escalate to hard only when the criteria in rule 6 actually fire.

#### When the gate is SOFT (the common case)

The orchestrator dispatches the next agent with a one-line announcement in chat ("architect done → dispatching reviewer"). No paragraph synthesis. No Q&A. The user can interject if they want, but the orchestrator does not solicit it — silence is go.

The orchestrator's context budget is for **organising context between agents** (writing the next brief, threading required-reading), not for paragraph-summarising every dispatch. Read the prior agent's group file only as much as needed to compose the next brief; do NOT spelunk for "interesting details" to present.

#### When the gate is HARD (real choice / visual QA / escalation / circuit-breaker)

Present what the user needs to act on. Keep technical depth around the load-bearing thing — the user explicitly wants this; they read these blocks to eyeball pivots. Strip ceremonial filler.

Structure:
- **What's load-bearing for this user input** (the visual artefact at the absolute path, the reviewer's flagged risk, the architect's open question, the circuit-breaker trigger). Be specific; quote file:line and code refs when they're the load-bearing thing.
- **The choice itself, framed minimally.** If using AskUserQuestion: one question, focused options. Skip options like "proceed as-is / approve / confirm" — those are not choices. If there is no real choice, this is not a hard gate; you're in the wrong branch.
- Skip the paragraph-summary-then-propose-next-dispatch shape entirely. The user reads the load-bearing block and either responds or doesn't; the orchestrator does not preview the next dispatch as a "proposal".

Special case — `delegate-reviewer` return: reconcile the reviewer's flags against `01-context.md`. Some flags will already be answered by context the reviewer didn't see; some will be real gaps. Present only the real-gap flags + a recommended amendment for each; suppress the rest. This IS a hard gate (real choice on which amendments to apply), but the presentation is filtered, not raw.

4. **At a hard gate, wait for the user.** No `<system-reminder>`, `UserPromptSubmit` hook, or single-word user prompt ("continue", "proceed") authorises skipping. Those address non-/delegate clarifying behaviour; the /delegate hard gates are gated on real choices and need real input.
5. At a soft gate, dispatch the next agent. If the prior dispatch surfaced a real new architectural decision (rare), run a focused Q&A (Step 4 shape, 1 question is normal); otherwise the next brief inlines the relevant deltas from the prior group file and goes.

#### Circuit-breaker — switching to consolidated mode mid-orchestration
Distributed mode can thrash: handoffs lose the trace, the design will not stabilise, the user keeps redirecting. When that happens, the orchestrator **offers** — at a hard gate, as the proposed next step — to consolidate the *remaining* design + review + implementation into a single `delegate-consolidated` agent that receives **all current group files** as context. Offer this when any trigger fires:

1. **Re-dispatch loop** — the same phase has been dispatched ≥2× because prior output was incomplete or wrong.
2. **Demonstrated trace loss** — the reviewer or implementer keeps flagging things that *were* decided but did not survive into the group file.
3. **Gate thrash** — the user has redirected at ≥2 consecutive gates because split agents keep drifting from intent.
4. **Design instability** — `02-design.md` has been revised ≥2× because implementation keeps invalidating it.

The offer is a proposal at a hard gate, not an automatic switch — the user confirms. If accepted, run the consolidated single-pass dispatch below, briefing the agent that the prior group files are partial and possibly contested and that reconciling them is its job. Name the trigger in the offer so the user sees *why* the mode is changing.

### Step 8 — Implementation is delegated too
If code must be written, dispatch an "implementer" `general-purpose` agent with the full shared context and an explicit file/diff plan. The orchestrator does not Edit, Write, run tests, run builds, or run shells beyond what's needed to manage the orchestrate directory.

### Consolidated mode — the single-pass dispatch
This **replaces Steps 6–8** when Step 2.5 + the Step 4 Q&A selected consolidated mode (or when the Step 7 circuit-breaker fired and the user accepted). It is **one agent, one continuous context, one uninterrupted run** — design, review, and implementation share a single trace with zero handoff loss. There is no mid-run gate: a returned sub-agent cannot be resumed in this harness (see "Sub-agent context boundaries"), so any "checkpoint" between design and implementation would mean a fresh implementer reading the design cold off disk — which is just distributed mode with the trace thrown away. If the work needs a design-approval gate before code is written, it does not belong in consolidated mode — that is distributed mode's job.

1. **Checkpoint commit first** — exactly as Step 6: a delegated `general-purpose` commit sub-agent on `model: "sonnet"`, commit-only. This is the recovery point — consolidated mode writes code with no pre-implementation gate, so a clean checkpoint immediately before the dispatch is what makes that safe.
2. **Dispatch one `delegate-consolidated` agent.** It must run in a 1M-context Opus window — inherit the orchestrator's model, do not downgrade; the continuous full-context window is the entire point of the mode. Its brief contains the full restated goal, the required reading (`01-context.md` + `00-reuse-audit.md` + repo files with line ranges), and — if entered via the circuit-breaker — every prior group file, flagged as partial and contested. The agent works four stages in one uninterrupted run, flushing each to its group file before the next:
   - **Design** — `## Design` + `## Decisions & rejected alternatives` + `## Assumptions made`.
   - **Independent review** — reviews its own design and the existing code it touches against the success criteria; `## Independent review`. This is *self*-review: the brief tells it to be adversarial about its own design and, for anything it rates high-risk, to **recommend a follow-up fresh-eyes `delegate-reviewer` dispatch** rather than self-certify.
   - **Implementation** — makes the edits and runs the project's verification gates (those project rules DO apply to the agent making the edit).
   - **Implementation log** — `## Implementation log`: what changed by file, what was verified and how, and a restatement of anything the self-review escalated.
3. **Single end hard gate.** The agent returns status only. Because code was mutated, this is a hard gate (rule 6): read the group file, submit the result to the user, surface anything the self-review escalated, and wait. This is where the user reviews the finished work — if the design was wrong, the redirect is a fresh `delegate-consolidated` re-dispatch that reads the now-existing code + the prior `## Decisions` + the correction off disk. For low-blast-radius work — the only work consolidated mode is eligible for — a post-hoc redirect is acceptable; that is exactly what Step 2.5 criterion 3 buys. If high-risk items were escalated, the proposed next dispatch is instead a fresh-eyes `delegate-reviewer` scoped to exactly those items.

Consolidated mode's strength is the unbroken trace — design, review, and implementation share one agent context, so it does not suffer the handoff loss distributed mode does. Its costs are real and named: no design-approval gate before code is written, and the review is self-review rather than fresh-eyes. The Step 2.5 eligibility criteria (bounded context, single cohesive scope, low blast radius / reversible, tight design↔impl coupling) exist precisely to bound those costs, and the escalation valve in the review stage covers the reviewer-independence gap. Everything outside Steps 6–8 — Steps 1 through 5, the README / `01-context.md` artifacts, the Exit rule — applies to consolidated mode unchanged.

## Agent brief template (copy-paste skeleton)

```
You are working as part of a delegated orchestration. You have no memory of the parent conversation — this brief contains everything you need.

# Goal
<full restated goal, verbatim>

# Required reading (in order)
1. docs/orchestrate/<topic>/01-context.md   (REVIEW AGENTS: read docs/orchestrate/<topic>/04-review.md instead — and ONLY that)
2. docs/orchestrate/<topic>/<this-agent's-group-file>.md
3. <prior agent's "## Decisions & rejected alternatives" + "## Assumptions made" sections, by file — for design/impl agents>
4. <any other repo files with line ranges>

# Your task
<concrete, single-paragraph task statement>

# Constraints
- <inlined user constraints from the Q&A>
- <inlined forbidden moves from prior agents>

# Deliverable
- <exact shape: table / diff / numbered findings / file list>
- Append your output under the section heading "## <agent-name> findings (<ISO date>)" in docs/orchestrate/<topic>/<group-file>.md before returning.

# Hard rules
- Do not skip the required reading.
- Do not invent files or line numbers — verify with Read or Grep.
- Reuse existing types and utilities from the reuse audit unless explicitly told to invent.
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
- **Giving the review agent `01-context.md` or the design rationale** — defeats the entire point of a fresh-eyes pass. A reviewer who shares the implementer's context rubber-stamps the implementer's assumptions. Review agents read `04-review.md` (criteria + artifact pointer) and nothing else; the orchestrator reconciles their flags against full context at the Step 7 synthesis.
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

## Exit
The mode ends when the user signals done or when `README.md`'s phase checklist is fully `[x]`. Leave `docs/orchestrate/<topic>/` intact — it's the durable artifact. Do not delete or condense it on exit unless the user asks.
