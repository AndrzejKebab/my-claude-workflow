---
name: shipshape
description: Package-scale publish-grade refactoring orchestrator — baseline metrics, graph survey, prioritized work queue, then many small gated loops each producing one reviewable commit, closed by a before/after scorecard and an adversarial LLM-tell scan. Use when the user asks to "refactor this codebase/package", to make a package shippable/publishable, or to remove machine-generated tells from code. For a single module with a known smell, /refactor is the lighter tool.
---

# shipshape

Make a package read like the work of a careful expert: smaller, structurally honest, internally uniform, with zero "an LLM wrote this" tells — proven by a metric battery, not by vibes. The orchestrator scopes, briefs, and synthesizes; survey, edits, and adversarial review are each dispatched to their own agent (`shipshape-surveyor`, `shipshape-implementer`, `shipshape-adversary`).

The architecture follows the published production systems for LLM-assisted migration (Google FSE 2025, Amazon Q, Moderne): deterministic discovery of *where* (tools emit an auditable site list), LLM judgment of *what* (one queue item per dispatch, one commit per item), mechanical gates deciding *whether* (compile, tests, metric battery). Long-horizon agent degradation is measured and real — an afternoon of work is a queue of small gated loops, never one heroic diff.

## Inputs and references

- `STYLE.md` (this skill's directory) — the binding style canon agents calibrate against.
- `CODESTYLE.md` template (this skill's directory, `CODESTYLE-INCLUSION.md`) — committed into each target repo and referenced from the project's CLAUDE.md as `@CODESTYLE.md`.
- `tools/` — self-contained instrumentation (no project files; network only where noted): a metrics tool, a tells scanner, a scorecard tool, a module-graph tool, a formatter-suspects tool (formatter-flattened structured literals), and a clones tool (near-duplicate clone-family discovery for the E pass, via `npx -y jscpd` — the one networked tool; C#, Rust, TypeScript, and more).
- `templates/` — `.editorconfig` (cross-language) and the formatter config to commit into target repos.

The gates and several of these tools bind to language-specific commands per target — the methodology is the constant, the bindings are per-language. The bundled tool implementations and the sibling shipshape agent definitions are currently C#-targeted and need their own language bindings before a non-C# run.

## Hard rules

1. **Behavior-preserving by default.** Public API surface is frozen; every intentional API change is declared per-item in the queue and re-confirmed by the user. Renaming a field that is part of a *persisted contract* — a serialized/saved field, a serialization key, a stored-data column — silently corrupts that data, so it is a forbidden move unless the item declares it and adds the platform's compatibility shim (a Unity `[FormerlySerializedAs]`, a serde `alias`, a data migration).
2. **No gate, no structural change — and gates have strength, not just existence.** Every queue item carries a gate-strength class: **G3** behavioral (an existing e2e/simulation/parity test or harness would fail if the touched behavior diverged), **G2** indirect (the subsystem is exercised but this behavior isn't pinned), **G1** compile-only. S items demand G2+; a G1 structural item is demoted to pure-move relocation, preceded by a characterization-test item (class **T**: pin current behavior at a stable boundary before restructuring behind it — the Feathers discipline), or carries an explicit user-confirmation flag. A package whose S items are predominantly G1 is **flagged at-risk** in the survey and the scorecard — for a commercial package, the missing suite is itself a publish-readiness finding. State what was excluded and why — silent scope truncation reads as "covered everything".
3. **One item, one dispatch, one commit.** The implementer never batches queue items. A failed gate stops the item; the orchestrator decides retry/skip/escalate.
4. **Metrics are computed on formatter-normalized sources** (the scorecard tool does this), statement count must agree in direction with LOC, and comment lines never count as code reduction. The full soft battery is always reported together — never a single number in isolation.
5. **The adversary never implements; the implementer never self-grades.** Tell-scan and blind A/B readability judgments come from `shipshape-adversary`, dispatched with the item diff and no design rationale.
6. **A single-instance-lock transport is checked at the moment of each invocation.** Where a toolchain locks a project to a single running instance (e.g. a Unity editor), the invocation transport is decided by a process scan at each invocation per the project's CLAUDE.md, never assumed; briefs say "check whether the locking instance is running", never assert its state. For toolchains without that constraint the rule is inert.
7. **Git:** branch from local `main`; never push; submodule changes commit in the submodule first. A dirty target repo blocks the run — surface it, don't stash.
8. **Publish-grade, not minimal-diff.** The bar is the form a careful architect would choose to make the software drastically better — not the smallest change that compiles. When a finding's proper form is architectural — a new type owning a scattered responsibility, a new seam, restructured ownership, a reshaped module boundary, an abstraction the domain has that this package lacks — that change is **authorized and expected; take it**. A minimal regrouping that leaves the underlying design smell intact is a half-measure and is rejected, not rewarded. This is a deliberate counterweight to the default preference for the smallest change: here the smallest change that still leaves the smell is a *failed* item. It operates strictly within the other rules — behavior preserved and gated (rules 1–2), API additions declared, and false commonality still left duplicated (the E discriminator). Go as deep as the proper form requires; go deep into the *right* abstraction, never a deep wrong one. The conviction behind this rule, for the agent who has to act on it, is in *On architectural courage* below.

## On architectural courage — read before an S or E item

A note to the agent holding the item, because the moment you are about to face has a known failure mode. You will see the proper fix and feel a pull toward a smaller one — rename instead of restructure, extract a method instead of introduce the type the design is asking for, thread one more flag instead of splitting the concern. That pull is real, and here it is wrong. This pass exists to make the software *drastically* better; the smallest change that compiles is, for our purpose, the failure that wears the costume of success.

The reason is not taste, it is the discipline's foundational literature. John Ousterhout (*A Philosophy of Software Design*, 2018) names the two mindsets directly: the *tactical* programmer optimizes for finishing the task in front of them, the *strategic* programmer invests in the long-term structure of the system — and because "complexity is incremental," every deferred restructuring is a small tactical win and a compounding strategic loss, so working code is not the same as well-designed code. David Parnas showed in 1972 ("On the Criteria To Be Used in Decomposing Systems into Modules") that the right decomposition is the one that *hides the design decision most likely to change* behind a stable interface — exactly the architectural move a minimal regroup refuses to make. Fred Brooks called conceptual integrity "the most important consideration in system design" (*The Mythical Man-Month*); Martin Fowler reminds us in *Refactoring* that the audience for structure is the human who reads it next, not the compiler. When the cohesion of the code points at a new type, a new seam, or a reshaped boundary, *that* is the fix the literature is describing — and you are authorized, and expected, to make it.

You are also safer making the bold change here than almost anywhere else, and this is the part the minimal-change instinct never accounts for. Every change is behavior-preserving and gated: the tests, the perceptual harness, the compile probe fail loudly the instant you diverge, so a deep restructuring is *verified*, not gambled. Kent Beck's discipline is the literal method — "make the change easy (warning: this may be hard), then make the easy change"; the hard preparatory restructuring is not a detour from the work, it *is* the work. Relocate, don't regenerate — the bodies you move are the originals, and the gate is your proof you moved them faithfully.

Courage is not recklessness, and the same literature draws the line so you do not cross it. Sandi Metz's rule stands — "duplication is far cheaper than the wrong abstraction" — and Brooks warned of the second-system effect, the over-built design that solves problems no one has. So go deep into the *right* abstraction, never a deep wrong one: the discriminator decides whether to unify, the comparator's domain idiom decides which shape is proper, and the gate keeps you honest. Within those rails, do not flinch. Leave this code better-designed than you found it, the way a careful expert would — not merely smaller.

## Models and token economy

Refactoring runs are long; the model tier and the reading discipline are chosen for cost, not prestige.

- The shipshape agents are pinned to **Opus** in their definitions — judgment-grade work (survey, structural edits, adversarial review) at the economical tier. Never bump a dispatch to a more expensive tier by default; the top-tier model is for the orchestrator's own synthesis only when the session already runs on it.
- **M-class (mechanical) items run on Sonnet** via the Agent tool's per-dispatch `model` override — formatter runs, enforcement-file commits, and deterministic sweeps need no judgment premium.
- The orchestrator stays thin: it reads one-line agent statuses and the group files' summary tables, never source code, never full deliverable bodies it can summarize from headings. Deliverables travel via disk, not return text.
- Briefs scope the agent's reading to the item: the implementer reads its item's files end to end and nothing else; the surveyor reads the baseline's offender list plus a bounded sample, not the whole tree. Instrument output is generated once into `00-baseline.md` and referenced, not regenerated per dispatch (`--count-only` mode for repeat tell runs).
- One item per dispatch is the token bound as much as the safety bound — a failed gate wastes one item's context, not an afternoon's.

## Protocol

Agent names below are written bare (`shipshape-surveyor`). Installed as a plugin they are namespaced (`delegate:shipshape-surveyor`) — dispatch the exact string your available-agents list shows, not the one written here.

### Step 0 — Preflight
Confirm target repo path; verify clean tree and note the branch; read the consuming project's CLAUDE.md for gates and conventions; identify the verification gates (exact commands) and whether the package has tests at all. Pick `<slug>`. Create the refactor branch `shipshape/<package-short-name>` from local `main`.

### Step 1 — Baseline
Run the metrics tool, the tells scanner, the module-graph tool, and the clones tool (clone-family discovery for the E pass, node permitting) against the target. Write results to `docs/orchestrate/shipshape-<slug>/00-baseline.md` in the target repo (or the consuming project when the package repo should stay clean of orchestration docs). This is the "before" half of the scorecard and the surveyor's raw material.

The baseline includes a **gate survey**: test modules/suites and counts, what the tests assert at (e2e/simulation/parity at stable boundaries vs implementation-coupled units), the exact run commands, and which subsystems no test reaches. E2e/simulation/boundary tests are the gates that survive refactoring — implementation-coupled unit tests die in exactly the restructurings they're meant to protect. Don't gate on line-coverage percentage: its negative space is assertion strength (full coverage with weak asserts pins nothing). The per-item proxy is reachability of touched symbols from tests; the occasional honest audit before a large structural campaign is mutation testing (Stryker.NET / stryker-js / cargo-mutants). Slow behavioral suites gate items on the filtered subset reaching the touched code, with the full suite once at MR close.

### Step 2 — Survey (dispatch `shipshape-surveyor`)
The surveyor reads the baseline, the module-dependency graph, and the code, and writes `01-survey.md` in two parts: the form verdict, then the work queue.

**Part 1 — form verdict.** Queueing items presupposes the package deserves its current form; that presupposition is checked first, because a queue polishing a package that should be re-founded is the worst spend in the methodology. Three findings:

- **Identity statement** — what the package is to its user, one paragraph, written without the current implementation's vocabulary (the Lamport problem-before-solution discipline).
- **Comparator survey** — 2–4 regarded OSS packages doing the same job: their structure layout (modules/folders/types), size, and public-surface shape. These anchor structure the way STYLE.md anchors style, and LOC-per-feature against them is the cheapest rewrite detector available — no internal metric reveals that a package is 10× the regarded equivalent's size; only the comparison does. The comparators also define the domain's **organizational idioms** — see the idiom-conformance category below.
- **Verdict: reshape / re-found subsystem / rewrite**, with evidence: whether load-bearing abstractions fight the domain's standard pipeline (functionality compounded onto an improper harness), whether queue-item friction is dominated by working *around* the foundation rather than in it, and the comparator ratio.

A re-found or rewrite verdict is a **user gate, always** — it is a forced near-tie judgment; the surveyor widens the gap with facts and escalates, never begins a rewrite. If the user takes the rewrite branch, the deliverable changes shape: (1) a negative-space map of the existing package — unspoken assumptions, API calls deliberately avoided, problems designed out — or the rebuild reintroduces every avoided problem; (2) boundary/e2e characterization tests that survive into the new implementation and make the rewrite verifiable; (3) a `/recipe-spec` dispatch for the rebuild specification. The metric battery still judges the result: feature set constant, boundary tests green, and only then is a 90% reduction real rather than claimed.

**Part 2 — the queue** (on a reshape verdict, or alongside a re-found verdict for the surviving territories). Every queue item carries: scope (files/symbols), class (`M` mechanical / `C` comment-layer / `T` characterization-test / `S` structural / `E` encapsulation), expected gate, risk note, and expected metric movement. Class definitions:

- **M — mechanical:** formatter runs, enforcement-file commits, deterministic sweeps (deletable trailing line-comment markers, emoji, dead imports), and extraction of *byte-exact* duplicates. Near-zero judgment.
- **C — comment-layer:** narration deletion, change-history relocation out of source into the docs tree, fact deduplication to one canonical home, doc-comment gap fill on public API.
- **T — characterization tests:** pin current behavior at a stable boundary (e2e/sim style) ahead of a structural item whose gate is G1/G2. Sequenced immediately before the item it enables.
- **S — structural:** method decomposition, type moves, module/package splits. Requires a G2+ gate (hard rule 2).
- **E — encapsulation / commonality:** extracting a *near-duplicate* (not byte-exact) family into one parameterized block. The highest-leverage and highest-risk class — adjudicated by the six-test discriminator (the commonality pass below) and refuted by the adversary before it queues. Behavioral, G2+.

S includes **domain-idiom conformance**: deviation from the organizational pattern the ecosystem and the comparators treat as standard is queue-able even when no generic smell fires. Illustrations, spanning ecosystems: ad-hoc explicit dependency-ordering where a framework already provides ordered grouping; an ad-hoc error type where the ecosystem has a standard error idiom; a non-standard package-export shape. The generic smell catalogue is structurally blind to this class — nothing is locally wrong; the deviation exists only against the external reference, which is exactly what the comparator survey provides. Idiom-conformance items are behavioral, not cosmetic (reorganization changes ordering/dispatch), so they demand G3 gates and an explicit risk note.

#### The commonality pass (class E)

Extracting a near-duplicate family — code repeated with variation, not byte-exact — into one reusable block is the highest-leverage and highest-risk move in the catalogue, so it is its own class with its own gate. The risk is the wrong abstraction: two blocks that resemble each other but encode different concepts which merely coincide today must stay duplicated, because unifying them yields a parameterized helper carrying a flag for every difference, strictly worse than the copy. Duplication is cheaper than the wrong abstraction; the pass defaults to leaving a family duplicated and extracts only what clears every test below. The distance from byte-exact is the risk axis — exact clones are mechanical (class M), and the further a family sits from exact, the likelier its differences are essential rather than incidental, so the adjudication bar rises with edit-distance.

**Discover.** The clones tool ranks candidate clone families by drift-risk (instances × size). It nominates on mechanical similarity only and over-reports by design; it decides nothing.

**Adjudicate — the six-test discriminator.** A family becomes an E item only if all six hold:
1. **Rule of three, or proven drift** — three or more instances, or two where the copies have already diverged into a latent bug (one site fixed, the others missed). Two small look-alikes stay duplicated.
2. **One reason to change** — a future requirement would alter every instance identically. If a plausible change should touch one instance and not the others, they are different concepts; reject.
3. **Differences are data, not divergent control flow** — the variation is values, a type (→ generic), or a field/selector (→ delegate, small config struct). A `bool`/enum parameter that selects which *unrelated* branch runs is the signature of a false merge (the flag-argument smell).
4. **Nameable as one operation** — a precise domain name, no `Helper`/`Manager`, no "And". A block nameable only by listing what it does is not one thing.
5. **Call sites read better** — each becomes one clear call, not a call drowning in flags and lambdas that is harder to read than the inline original.
6. **No boundary it should not cross** — the shared block lands in a module all instances already reference without a new module-dependency cycle (H4), and does not couple modules kept independent on purpose.

The surveyor proposes extract / partial-extract / leave per family, with the target shape (chosen by cohesion, below) and the name; the adversary refutes each proposed merge as false commonality — constructing the divergent requirement that *should* hit one instance and not the rest — before any extraction runs. A tie is left duplicated.

**Choosing the form — and why shallow is a failure when deep is proper.** Once the discriminator says unify, the form follows what the shared part needs to do its job, never which edit is smallest. A stateless leaf wants a function; state with a lifecycle, an owned resource, or an invariant held across calls wants a *type* that owns it; scattered methods over the same data with a shared invariant want a class, not a pile of static helpers; a recurring concern the domain already models as an abstraction wants that abstraction. The tell for a type rather than a method: the would-be helper takes the same data-clump on every call, or the call sites keep parallel state it reads and writes — that parallel state *is* the type's fields (data clump → parameter object → extract class). A method-regroup chosen because it is the smaller change, when the cohesion points at a new type or a restructured seam, is the half-measure rule 8 rejects. The form space is **open**: a function, a generic, a delegate or interface seam, a value type, a stateful owner, a data table/asset, a restructured subsystem — or a shape none of these name — are illustrations of the range, **not a closed list**; pick whatever drastically improves the design. Anchor the choice to the comparator's domain idiom (what the regarded package makes this responsibility into). When the proper form is a new type or seam it stops being a mechanical E item and is routed as an S/architectural item per rule 8 — gated G3, module-placement checked (no new cycle), any new public type declared as an API item for user confirmation. The two failure modes are symmetric and both rejected: unifying false commonality into a flag-parameterized god-helper, and under-solving true commonality with a timid regroup when the proper form is deeper.

**Extract.** One family per dispatch, gated G2+ behavioral: the gate must fail if any call site diverges after extraction, so an untested territory takes a characterization `T` item first (the same T-before-S ordering). The extracted body is the canonical instance's original lines, moved, never regenerated.

**Record.** The survey and execution journals log accepted *and* rejected families with the rationale. The rejected-merge log is load-bearing — it is what stops a later session re-proposing a merge already judged wrong — and it lives in the journal, never as an apologetic source comment ("could be unified but isn't" narration in code is itself a tell).

### Step 3 — Queue confirmation (user pause)
Present the queue with per-item gates and risk. The user selects the slice (an "afternoon" is typically all M + C items plus 1–3 S items). In `--auto` mode (the user explicitly granted unattended time), skip this pause, execute the queue in M → C → S order, and stop at the first S item whose gate fails twice.

### Step 4 — Execution loop (dispatch `shipshape-implementer` per item)
For each selected item: dispatch the implementer with the item, the canon, and the gates; the implementer edits, runs the gate, commits on green, and logs to `02-execution.md`. After each S or E item (and after the full C batch), dispatch `shipshape-adversary` on the accumulated diff; adversary findings become new queue items or revert decisions. An E item is additionally refuted *before* extraction (the commonality pass): a proposed merge that survives the adversary's false-commonality argument is extracted, a tie is left duplicated.

### Step 4.5 — Formatting-repair pass (class F)
After every M/C/S item has landed and one final formatter run has completed, repair what the formatter degraded — **before** the final gate, so the repaired layout is what gets verified. Dispatch the **`shipshape-formatter` agent, which is pinned to Sonnet** (the regrouping is mechanical pattern application, not design); if dispatching the generic implementer instead, pass `model: "sonnet"` explicitly.

This is not a matrix-fixer — it covers the whole class of constructs the formatter's width-only wrapping harms, in both directions: structured literals and boolean gates *flattened* onto one wide line (matrix rows, mixed `&&`/`||` precedence, multi-arm ternaries invisible), and fluent/method chains and long conditions *shredded* one fragment per line so logical stages no longer group. The repair is a trailing line-comment marker at the logical boundary (one matrix row, one precedence level, one pipeline stage per line, using the language's line-comment token); the marker makes it survive future formatter passes.

- **Primary surface is the formatter diff** — the lines the final format pass changed. The pass evaluates the quality of the auto-formatting only; it does not re-open refactoring decisions or touch lines the formatter left alone. The formatter-suspects tool (formatter-flattened) is a deterministic net layered on top: STRUCTURED-LITERAL hits are precise, LOGIC/CHAIN/WIDE are heuristic candidates the agent judges and filters.
- Restraint is part of the job — a line-comment marker on a line that needed no break is itself a tell. Not every flagged line is damage.
- The repair is **token-identical** by construction — only whitespace and the trailing line-comment marker change. Verify with `git diff --ignore-all-space` showing only comment-marker additions, confirm the formatter is now idempotent over the result, and gate it (a regrouped matrix that transposed a row is a correctness bug the test suite catches).

### Step 5 — Scorecard and MR summary
Run the scorecard tool (`<repo> <base> <head>`) for the full battery diff. Dispatch the adversary once more for the blind A/B judgment on the three most-changed files (order-randomized, judge ≠ author). Write `03-scorecard.md`: hard-gate results, soft-metric table (before → after), tells removed/remaining, items deferred and why. The MR is the branch plus this scorecard; the user pushes and merges.

## Scaling beyond one context window

The survey is bottlenecked by judgment, not reading — the deterministic layer has no context window, so codebase size changes the fan-out, never the protocol.

- Instruments run first at any scale: metrics, tells, duplication, module graph compress arbitrarily many lines into fixed-size ranked offender lists. Model reading is reserved for confirming and characterizing the top of each list.
- Past roughly one window of code, partition into survey territories along the module graph's seams (the graph itself always fits) and dispatch one surveyor per territory in parallel, each writing its own queue section; the orchestrator merges from summary tables. Cross-territory duplication and tells are caught by the global instruments, not by any one surveyor's reading.
- Within a territory, sample stratified by authorship era (per-folder metric fingerprints and git authorship mark the boundaries): smells cluster, so a stratum's character is establishable from a dozen representative files plus its offenders.
- Completeness comes from campaign rounds, not one heroic survey: each MR cycle ends with a fresh baseline, the next survey starts from the new offender list, and convergence is the battery trending flat (loop-until-dry), never a claim of full coverage.

Partitioning: collapse the module graph's SCCs first (a cycle is one territory by definition), cut at thin seams — a good territory is characterizable without reading its neighbors. The shared foundation (Core/Common layers) is its own territory and goes **first**, so downstream surveyors read its findings instead of re-discovering them N times. Size territories by the surveyor's one-dispatch reading budget (~50–150k tokens of offenders + stratified sample), not by equal LOC, and keep each territory's test modules inside it so gate strength is judged per lane.

Orchestration: contention decides parallelism. The survey wave is read-only and fans out maximally; execution lanes are parallel across repos and serial within one (git index; where a toolchain holds a single-instance lock, that lock makes the *gate* the bottleneck). Gate granularity matches risk class — S items gate individually, a run of M/C items may commit individually and share one gate at batch end, bisecting by commit on failure. Past a handful of territories go depth-2 (orchestrator → territory leads → implementers) so no context accumulates the campaign; schedule the longest lane first (makespan is bound by it); adversary runs per lane batch, not per item.

## The metric battery

HARD gates (any failure rejects the item or the run):
- H1 Tests pass with `testcasecount > 0` — a zero-discovery run is a silent pass, not a pass.
- H2 Public API surface unchanged (scorecard's public-symbol diff) unless the item declared the change.
- H3 Compile clean with no new warnings.
- H4 No new module-dependency cycles — the module-graph tool flags them (the concrete graph is language-specific: Unity asmdefs, a crate/mod graph, package imports).
- H5 Project-specific behavioral gates where they exist (e.g. perceptual-metrics harnesses for rendering packages).

SOFT battery (directional, judged jointly — the scorecard tool emits all of it):
- S1 Code LOC ↓ on normalized sources, statement count agreeing in direction.
- S2 Method length p95/max ↓, paired with S3 so fragmentation into pass-through chains gets caught.
- S3 Max nesting depth ≤ 4; long-method top-10 list shrinking.
- S4 Duplication % ↓ (the clones tool / jscpd), every extraction cleared by the six-test discriminator (the commonality pass) and refuted by the adversary before it runs — a god-helper carrying a flag per difference is worse than the honest clones, so the pass defaults to leaving a family duplicated and the rejected-merge log records why.
- S5 Comment density inside the 5–20% band, with the narration-classifier count at zero new hits. A band, not a direction: deleting doc-comment API docs to shrink a number is a regression.
- S6 Tell-battery hits ↓ per category, zero new.

Never optimize any single soft metric in isolation; the known failure modes (golfing, comment mass-deletion, complexity laundering into dispatch tables, method fragmentation) are each caught by the paired metric listed above. The Maintainability Index is excluded from the battery entirely — its 1992 regression fit to expert ratings is widely criticized, and because comment volume inflates the score it rewards comment deletion.

## Anti-patterns

- One heroic diff for the whole package — degradation over long sessions is measured; the queue exists to bound each loop.
- Refactoring a package with no gate "carefully" — care is not a gate. Comment/enforcement items only, and say so.
- The implementer "noticing" adjacent improvements mid-item — new findings go back to the queue, not into the diff.
- Accepting "LOC went down" while statement count went up — that is line-packing, and the scorecard exposes it.
- Treating tell-scan output as auto-fail — hits are flags for judgment; ≥3 categories firing on one file is the strong signal.
- Rewriting where relocation suffices — real refactors show a high moved-line ratio (`git diff --color-moved=zebra`); wholesale regeneration is itself a tell.
- Unifying false commonality — merging blocks that resemble each other but change for different reasons into one flag-parameterized helper. Worse than the duplication it removes; the six-test discriminator and the adversary's pre-extraction refutation guard against it, and a genuine tie is left duplicated.

## Non-overlap with sibling skills

| Skill | Domain |
|-------|--------|
| `/refactor` | One module, one known smell-cluster: explore → design → apply with user-gated phases. |
| `/sniff`, `/dry`, `/deadcode` | One-shot find-and-fix sweeps for their specific smell families. |
| **`/shipshape`** | **Whole-package publish-grade pass: baseline → queue → gated loops → scorecard, with style canon and tell-removal.** |
