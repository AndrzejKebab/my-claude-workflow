---
name: delegate
description: Multi-agent orchestration. The orchestrator scopes, briefs, and synthesizes — every other action is dispatched to sub-agents. Two hard laws: (1) the orchestrator NEVER injects hypotheses, code-path references, or fix directions into briefs — subagent context purity is the entire value proposition; (2) the orchestrator never edits repo code and never runs the gate — it dispatches, agents do, no matter how small the change.
---

# delegate

## Standing: an approach, not law

This skill is an idea of how supervisor-agent orchestration can be approached — not a statute. The emphatic sections ("LAW", "binding") mark the defaults with the strongest observed-failure evidence behind them; read them as hard-won defaults, deviate deliberately with the reason recorded in the group file, never by drift. The orchestrator's real job is deliberation: every dispatch shape, gate shape, and brief is a judgment call made fresh against the situation, with this document as the failure-mode catalogue, not the script.

One step is genuinely mandatory: spec agreement with the user (next section). Everything downstream of a malformed spec is the game of broken phone — the orchestrator's misreading multiplies through every brief in the chain.

## Spec agreement with the user — mandatory, continuous (user law, 2026-07-14)

The worst orchestration outcome is not a slow wave plan — it is broken phone: a malformed spec born from user↔orchestrator miscommunication, transferred with full confidence onto every agent in the chain. Agents amplify specs; they do not repair them.

- Before orchestrating: agree the technical specification with the user in the most minimal but completely unambiguous form. Short spec files the user can cross-read (one per problem, target behavior only) beat a restatement buried in chat. This step is mandatory even when the user seems to be rushing — rushing is where broken phone starts.
- Continuous, not front-loaded: the spec is agreed at the start and re-agreed every time understanding moves — a user correction, an agent side note contradicting an assumption, a design decision that reshapes behavior. Material spec changes go back to the user before they propagate into briefs; spec files are amended in place so there is always one current, reviewable statement of intent.
- Minimal but unambiguous: define target behavior; leave mechanism as design space unless the user pins it. Don't prescribe conventions for their own sake (user, 2026-07-14: "lets make sure not to prescribe conventions just for the sake of it").

## Orchestrator window: caveman-style (binding)

The main window is a control panel, not an essay. Write caveman-style (JuliusBrussee/caveman: compress output ~75%, "why use many token when few do trick"). The orchestrator's job produces a LOT of status/synthesis text; the user reads it constantly, so compress hard.

caveman rules, applied to the window:
- Fragments over sentences. Drop filler, politeness, transitions, hedges, preamble, self-narration ("here's where this stands"), agent-praise, and recaps of what an agent already said.
- Keep substance exact: numbers, file:line, paths, commit hashes, commands, verbatim user citations — never compressed.
- Status = one line: "Dispatched X. Waiting." / "Y done: 25.2%→1pp. Next: Z."
- Finding = result + number, not the mechanism. Mechanism/detail lives in group files; link, don't inline.
- Decision to user = the choice + one line per option.
- If a reply runs past ~3 lines, cut it. (Mirror the user's own level if they go terse.)

ponytail (DietrichGebert/ponytail) is a DIFFERENT thing — code-minimalism (YAGNI ladder: does it need to exist? stdlib? platform? one line?), not a prose style. It governs the CODE agents write, not window text. If wanted, fold it into substantive agents' briefs (write the minimum that works), not here.

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

## THE LAW (2): the orchestrator never edits code and never runs the gate

The orchestrator dispatches; agents do. Every mutation of repo state is dispatched: source edits, shader/config/asset changes, builds, tests, captures, format runs, compile-fixes, dependency installs, and the verification gate itself. The orchestrator reads only canon, spec, and the group files, and writes only the group files plus checkpoint commits of agents' already-written work. Running a build "to check," running a capture "to verify," hand-fixing one line "because it's small," or hand-running the gate are the same violation: the orchestrator became a single-context implementer, and every such edit is unreviewed work the dispatch discipline exists to prevent.

The temptation scales inversely with size — the one-liner feels too small to dispatch, and the one-liner is exactly where the rule is load-bearing, because a pile of "too small to dispatch" one-liners is how the orchestrator silently becomes the implementer. The test is *touches repo code / build / gate?*, not *how small?* — when in doubt, dispatch. Want a change? Write a brief and dispatch. Want green/red? Dispatch the validating agent and read back the result. The only repo write the orchestrator owns is the checkpoint commit (contract 2), and that commits agents' work — never an edit the orchestrator authored. If you are about to call `Edit`, `Write` on a source file, `cargo`/`vite`/`npm`/a test runner, or a capture script, stop: that is a dispatch, not an orchestrator action.

---

## Structural-decay guards (binding)

Vertical-slice orchestration with behavior-only gates decays architecture in the seams *between* briefs: every agent optimizes its brief, nobody owns the whole. Each guard below traces to a real decay mode (evidence: hypertino `docs/methodology-postmortem.md`).

**Enforcement-locus principle (governs every guard):** agents are bounded-window token predictors — they cannot count their own repetitions, sense sibling code, or "keep in mind" anything across contexts. A rule binds only whoever has the evidence in the window. Three valid loci, in order of preference: **mechanical** (grep/assert/lint in the repo's `tools/`, runs in the gate), **pass** (a fresh agent whose entire attention is one check — `/warden`), **brief** (a fact the orchestrator computes/enumerates and injects). A rule left as an ambient memory obligation ("always remember to…") fails silently — restate it at a valid locus or drop it. Counts and absence claims come from enumeration (Grep/Glob) run in-session.

- **Laws belong in every brief.** A repo's structural laws (`AGENTS.md`/`CODESTYLE.md`) are facts of the artifact, the same class of brief payload as code at file:line. Briefs list the laws file in required reading and quote the laws in scope. THE LAW governs hypotheses about *problems*; invariants of the *artifact* ride in every brief.
- **Rule of three.** The auditor reports the pattern instance count when a dispatch extends an existing pattern or names a structural template. N=2: architect records extend-vs-generalize in Decisions. N≥3: generalize is the default; extending needs a recorded waiver. A template's accidents replicate with full fidelity — establish whether the template's shape is a decision or a placeholder before copying it.
- **Lockstep for multi-implementation contracts.** A change to a contract with N implementations (backends, adapters, platforms) dispatches one agent owning all N, or parallel agents + an explicit convergence step. "Default body now, port the others later" is a violation.
- **Invariants relied on get written down in the same dispatch.** The implementer logs every invariant it relied on but did not create; each becomes an assert in code (preferred) or a line in the repo's laws/subsystem doc. An unstated coupling is a bug with a delay timer.
- **Every gate includes one adversarial criterion.** Acceptance criteria exercise at least one boundary/failure mode of the shipped mechanism (exhaustion, churn, capability absence) in addition to the happy metric. Agents write to the gate, so the gate must contain the failure mode.
- **Gate tiering — acceptance retires, the battery is invariant-only (user law, 2026-07-06).** Two artifact classes, never conflated. An *acceptance gate* proves a milestone's claim at landing: scripted walkthrough, bite proofs, exact scenario — it runs green once, its evidence lands in the log, and it retires (runnable on demand, never wired into the permanent check). A *battery gate* lives in the repo's permanent check and must be invariant-shaped: properties that survive intended change — wire/store/hash identity, determinism, lint fences, golden parity, real-entry-point boot smoke — cheap, headless where possible, generic. A scripted walkthrough wired into the permanent battery is a unit test in an e2e costume: it validates the authored implementation against its own specifics, taxes every future milestone with recalibration (observed: coordinate retuning, reference rebakes after an intended convention change), and rots silently (observed: a reference gate red for days while sessions reported green). UI-visible behavior is accepted by user live QA — the user's eye is the instrument; a script re-walking what QA already saw adds upkeep without protection. The durable regression vehicle is the project's replay/divergence/metrics instrument once it exists (record/replay class); scenario scripts retire into replays, they never accumulate. Gate authorship must not dominate a dispatch's tokens — a gate costing more than its mechanism is the wrong tier.
- **Verification-evidence placement is a design decision.** When a gate needs observable evidence (checksums, captures, metrics), the design names the layer that computes it. Evidence never sinks below a frozen seam to make a gate greener.
- **Ceilings carry lift-conditions; synthesis sweeps them.** Recorded simplifications need a checkable "lifts when X". At close-out, sweep: did this session make any recorded ceiling's condition true, or diverge from the spec's stated layout? Matches surface to the user as named candidate sessions — the sweep is what turns the debt register into a scheduler input.
- **Review = function + structure.** The fresh-eyes reviewer verifies success criteria; structure is verified by `/warden diff` (one fresh agent per law family, enumeration before judgment — see the warden skill). Success criteria cannot catch what they never state, and an implementer cannot audit the structure it just optimized a gate inside of.
- **Gates run the shipped artifact in the user's config.** A gate exercising a proxy — a headless/software renderer, a stubbed transport, one browser/GPU — while the user hits another config is worse than no gate: it reports green while the real artifact is broken (evidence: a web UI passed on headless-SwiftShader while the real browser aborted at context creation; a spatial-variance check passed while the UI drew *behind* the scene). The gate loads the real built/served artifact in the environment the user runs (real browser/GPU, and the capability matrix that matters — e.g. an optional extension present *and* absent), and proves it bites: fails on the pre-fix artifact, passes post-fix, non-vacuously. Green on a proxy is not proof, and "eyeball it yourself" handed to the user is not a gate.

---

## When a fix fails: diagnose-first

The user reports the symptom didn't move → next dispatch is a **read-only diagnostic**. No "let me try option B." No Q&A. Diagnose is the only path.

**Before dispatching fix N+1:** write in chat what success would look like. When the user's report contradicts it, the hypothesis is falsified.

**3+ failed fixes on the same symptom → stop.** Offer `/diagnose-first` (scientific method), `/refactor`(reduce surface for clarity) or `/handoff`.

---

## Structural contracts

1. **Never work alone — this is LAW (2), not a guideline.** Every source read, edit, build, test, capture, format, compile-fix is dispatched. Orchestrator reads only canon/spec and the group files, and writes only the group files plus checkpoint commits of agents' already-written work. "Too small to dispatch" is the trap — a one-liner, config tweak, shader tweak, package install, "just run the build," "just grab a capture to check" all still dispatch. The test is *touches repo code/build/gate?*, not *how small?*. See THE LAW (2) above.
2. **Checkpoint before every code-mutating dispatch — and commit WIP often during the work; never hold a large uncommitted tree.** A committed WIP with a known-red gate is recoverable; an uncommitted pile is not, and under concurrent editors it invites clobbers and racing-writer loss (an agent's `git checkout`/`restore` on a shared file destroys a sibling's uncommitted edits with no copy to restore). Not commit purists: never gate a commit on all-green — commit at each meaningful step (a piece that passes, before a risky diagnostic, before a handoff), labelling WIP as WIP with the known-red gate named. **Each completed step checkpoints as its own commit before the next step dispatches** — when an agent returns its gate green, commit that deliverable immediately, never batch several green steps into one deferred commit, and never defer checkpointing to the user's own final commit ("the user commits at the end" is not a licence to hold a multi-step green tree; the user's commit is the end state, the orchestrator's per-step checkpoints are the recovery trail to it). Recovery, not tidiness, is the reason: git edits get botched, and a committed step is the only state a bungled `Edit`/`restore`/`checkout` can roll back to — an uncommitted multi-step tree has no floor. Edits revert via selective `Edit` from the diff, never `git checkout`/`restore` on a shared file. The orchestrator runs its own checkpoint commits inline (`git add <paths> && git commit -m "..." -- <paths>`) — committing already-written work is bookkeeping, not implementation, and spinning up a commit agent for a one-liner costs more than it protects (user-confirmed economics); substantive agents commit their own progress.
3. **Shared-context files on disk** (`docs/orchestrate/<topic>/`). One file per group. Agents read on entry, append on exit.
4. **Every deliverable ends with `## Side notes`.** Agent's channel to flag anything the brief missed.
5. **Verification is a dispatch — the validating agent.** Compilation proves nothing; verify end-to-end (visual = user's eye = hard gate). After the (often parallel) implementation dispatches, one validating agent owns the gate: runs build + tests, fixes what they surface (impl vs test bug, decided from spec/design), iterates to green, writes a log. Orchestrator relays build/test output as symptom, reads back green/red — never runs the gate or hand-fixes errors itself. The validator drives the existing invariant battery + real entry points; it does not author new walkthrough scripts (gate-tiering guard) — milestone acceptance of UI-visible behavior is the user's live QA session.
6. **Scope teammates to reusable topics, not one-shot tasks.** Agents here are persistent, addressable, resumable teammates — `SendMessage` by name continues one with its context intact; a fresh `Agent` call starts clean. The lever is the `name` parameter on the `Agent` call: pass a `name` to spawn a durable addressable teammate (resumable by `SendMessage` to that name); omit `name` for a one-shot subagent that runs, returns, and is gone. The roster is flat — a teammate cannot spawn named teammates, so any dispatched agent that itself fans out must omit `name` on its children (a named child spawn fails with "Teammates cannot spawn other teammates"). Scope one teammate to a live topic (an area that will take several related tasks) and route the topic's follow-ups back to it, so it keeps the code context instead of re-reading the area every dispatch. The purity LAW still governs: keep a FRESH agent for any job that needs unbiased eyes — verification/review (an implementer cannot review its own work), observe-first diagnosis, anything a prior task's conclusions would bias. Topic-reuse buys context economy; it never smuggles a prior brief's hypotheses into a job that needs fresh eyes. Retire a teammate when its topic closes (idle teammates otherwise linger on the roster), and re-scope fresh when its context bloats — a long-lived teammate's early hallucination hardens into its own later canon, and it runs slow and expensive. **Reassign by kill, not by stand-down message — a task is never live in two agents at once.** Before dispatching a replacement for a stuck, silent, or not-yet-started teammate, `TaskStop` the original and confirm it is dead; do NOT send a stand-down `SendMessage` and dispatch the replacement in parallel — the message races the teammate's own resume on its still-queued brief and loses (the original wakes, both agents run the same brief, both edit the same files, they clobber). A `SendMessage` can *retask* a responsive teammate in place; only a confirmed `TaskStop` retires an unresponsive one before its replacement touches shared files. Corollary: never leave the same brief live in two inboxes — if the first hasn't started, either re-nudge that same teammate or kill-then-replace, never both-hold. Disk group files stay the durable record, the cross-topic handoff, and the recovery channel when the transcript drops.
7. **Build publish-grade from the first line — fold in `/shipshape`.** Early (with the context files), commit the `CODESTYLE.md` inclusion into the target repo and add a shipshape-calibrated shape-discipline section to `01-context.md`, binding every substantive agent: the negative-space test (no deletable comment, no defensive check the types rule out, no doc restating a name); architectural courage (the right abstraction the cohesion points at — a type or seam, never a flag-threaded helper, and never a deep *wrong* one; duplication beats the wrong abstraction); the platform's domain idioms; the tell blacklist; reachable-citation discipline (cite what the shipped artifact's reader can reach, never the spec path or this journal); behavioral (not compile-only) gates. Briefs point agents at both. Canon: `~/.claude/skills/shipshape/STYLE.md` + `CODESTYLE-INCLUSION.md`. For structural/S-shaped work, the brief additionally points the implementer at `~/.claude/skills/shipshape/SKILL.md` §On architectural courage to read before implementing — the conviction text is what changes behavior at the moment of the pull; its one-line summary here does not.
8. **Sibling orchestrations are journals, not canon — don't cross-reference, inherit, or re-record them.** Another session's `docs/orchestrate/<other-topic>/` is its working memory and the lowest source-of-truth tier, below code at HEAD and research papers: a load-bearing claim grounds in code (`file:line`) or a paper, never a sibling journal. The orchestrator never lists sibling-session docs in required reading, and no brief points a sub-agent at one as canon. A sub-agent that reaches for a sibling journal on its own and inherits its conclusion — reading "session N rejected X" as "X is impossible" — has violated this; such a claim enters chat only after it is verified against the code, and an unverified sibling-journal conclusion never reaches the user as a wall (that is how a false dichotomy is manufactured). Do not re-record another session's claim into the current log as a corroborating fact — a tier-4 claim copied forward is noise that later reads as canon. When the user explicitly names a sibling session, the brief frames it as "what an agent thought once — verify every load-bearing claim against the code before acting; do not inherit its conclusions." Never amend another orchestration's docs from inside the current one (the "poisoning the well" cascade).
9. **A parked agent is a dying agent — nudge on sight.** Sub-agents recurrently end their turn while a background gate runs ("I'll wait for the completion event") despite brief instructions to block in-session; the wake event is unreliable and a parked agent can silently die for hours (observed repeatedly). A completion notification whose text says "waiting for / holding for / will resume when" IS a parked agent: immediately SendMessage a block-in-session directive (TaskOutput block=true loop until exit, act on the result in the same run). Brief text alone does not prevent this; the orchestrator's nudge-on-notification is the enforcement locus.
10. **A completion is a claim, not proof — verify the agent actually worked.** A "completed" notification can be a no-op misfire: zero tool-uses, garbled output, nothing committed, tree unchanged. Before relaying any result as progress, confirm work happened — tool-uses > 0 **and** HEAD/tree moved (or the gate output is genuinely present). A no-op is not a result: resume that agent with an execute directive, or `TaskStop` and re-dispatch — never report it as done or mine it for a finding. The same `git status`/`git log` check catches the inverse — an agent that claims green while nothing landed.

---

## Protocol

1. **Scope & spec-agree** — restate goal as behavioural problemspace (the three DO axes); agree the technical spec with the user, minimal and unambiguous (see Spec agreement — mandatory, and continuous through the whole session). Pick topic slug, name groups and files.
2. **Audit** — dispatch `delegate-auditor`. Read `00-reuse-audit.md` yourself — including `## Pattern instance count` (N≥3 → the architect must generalize or record a waiver).
3. **Explore & scope broad edits** (encouraged for milestone-scale / multi-subsystem goals; skip for narrow ones) — dispatch exploration against the spec: the scoping agent reads the code the spec touches, partitions the work into broad edit groups, and emits a **parallel workload map** — groups with file-ownership partition, dependency DAG between groups, wave plan, per-group gates. This is where the parallelism decision gets MADE instead of defaulted; a linear slice list silently forfeits it. Overlappable: scope milestone N+1 while N's implementation runs (exploration is read-only).
4. **Mode** — distributed (default) or consolidated (bounded scope, low blast radius, tight design↔impl coupling).
5. **Brief** — present method to user. State recommendations and commit. Acceptance criteria include one adversarial condition (boundary/failure mode), and — when a gate needs computed evidence — the layer that owns computing it.
6. **Context files** — `README.md` + `01-context.md` (problemspace, constraints, audit summary, required reading incl. the repo's laws file, open questions, forbidden moves with hard provenance).
7. **Dispatch** — checkpoint commit → substantive agent(s). Brief leads with problemspace, suggests approach. Agent is Opus on equal footing. Multi-implementation contract changes dispatch in lockstep (one agent owns all N, or parallel + convergence step). When a workload map exists, dispatch by it (see Dispatch shape below) — a mapped parallel wave runs parallel only under the worktree + trivial-merge precondition; don't collapse it serial out of habit, don't fan it out without the isolation.
8. **Verify & synthesize** — dispatch the validating agent (contract 5) to drive the build/test gate to green; run `/warden diff` for the structural check (the reviewer's law check covers repos without warden); confirm the group files were written. Close-out sweep: invariants relied on → assert/laws-file; ceilings whose lift-condition is now true → surface as named candidate sessions; session scripts committed under `docs/orchestrate/<topic>/scratch/` → promote (parameterize into the project's tools — a dispatch) or delete. Hard gate on visual QA / real choice / circuit-breaker; soft gate otherwise.

---

## Dispatch shape: parallel vs combined (deliberate per dispatch)

The orchestrator's central decision, made fresh for every wave: fan out in parallel, or combine tasks into one agent. Neither is the groove; undecided is the only wrong answer. We don't fight for wall-clock speed — we fight for exceptionally good results as a software development team (user law, 2026-07-14). Wall-clock is the weakest reason to parallelize.

- **Parallel — only when worktree-isolated and trivially merged (user law, 2026-07-14).** Parallel agents are dispatched only when their workloads can be orchestrated in individual git worktrees and the merge back is trivial — disjoint files, or mechanically resolvable seams named before dispatch. If two workloads cannot be worktree-isolated and trivially merged, they are not parallel candidates: combine them into one agent or run them as sequential waves. The merge is an explicit step with an owner, planned before dispatch, not discovered after.
- **Gate stays singular.** ONE validating agent owns the global gate at wave end regardless of how many implementers ran — a gate raced by N agents produces unattributable reds. Implementers verify per-group criteria in their own worktrees.
- **Checkpoint per wave** (contract 2): commit/merge each agent's deliverable as it returns green; wave N+1 dispatches only on wave N committed.
- **Combine — for knowledge locality.** Group tasks into a single agent when they share the knowledge a context must hold anyway: the same subsystem's mental model, the same required reading, the same contract. One agent doing three related tasks reads the canon once; three agents read it three times and each holds a third of the picture — the seams between them are where architecture decays. Coupled tasks (a contract with N implementations, a change plus its integration) default to one context; a chain of gate-green slices in one agent also beats parallel when attribution matters more than latency. Token economics point the same way (N agents re-read required reading N times).
- **Deliberate, and record.** These are possibilities, not a formula — weigh isolation cost, merge triviality, knowledge locality, coupling, tokens, and attribution per dispatch; write the one-line reason in the group file. A scope doc claiming "groups X and Y are independent" earns parallel only if the worktree + trivial-merge precondition actually holds.
- **Residual shared-tree rule.** If agents ever do share one tree (exception, recorded), pathspec commits only (`git commit -m "..." -- <own paths>`, never bare `git commit`) — a shared index sweeps a sibling's staged files into a mislabeled commit (observed live); retry on index.lock; never rewrite a live sibling's commit to relabel commingling.

---

## Brief template

No role-play preamble — an agent already knows it is fresh with no parent memory; stating it ("you are a fresh agent in a delegated orchestration, no memory of the parent") is noise that reads as a confusing role-assignment. Open with facts: where the work lives + one line of orientation.

```
# Context
<worktree + branch; one line — what this area is and where this task sits in the larger effort. Facts, not role-play.>

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
Structural laws in scope: <repo laws file (AGENTS.md / CODESTYLE.md) + the specific laws this change touches>
Sibling-orchestration docs (any other docs/orchestrate/<topic>/) are not canon — do not inherit their conclusions; verify any claim against the code (file:line) before acting on or recording it.

# Open questions (yours to resolve from code + canon)
<NOT pre-decided>

# Deliverable
<shape + path on disk>
Log every invariant you relied on but did not create (assert it in code, or name it for the laws file).
End with ## Side notes / observations / complaints.
```

---

## Reference sections (load on demand)

- `execution-modes.md` — distributed vs consolidated, dispatch shapes, eligibility criteria
- `circuit-breakers.md` — diagnose-first, loop-detection, consolidated-mode handoff, brute-force protocol
- `context-boundaries.md` — what subagents can/cannot see, image protocol
- `askuserquestion.md` — when to ask vs brief, sticky amplification
- `e2e-gates.md` — gate authoring discipline for visual-capture gates
