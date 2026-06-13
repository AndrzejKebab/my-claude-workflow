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
- `tools/` — self-contained instrumentation (no project files, no network): `shipshape-metrics.py`, `shipshape-tells.sh`, `shipshape-scorecard.sh`, `shipshape-asmdef-graph.py`, `shipshape-fmt-suspects.py` (csharpier-flattened structured literals). Duplication detection uses `npx -y jscpd` when node is available.
- `templates/` — `.editorconfig` and `.csharpierrc.yaml` to commit into target repos.

## Hard rules

1. **Behavior-preserving by default.** Public API surface is frozen; every intentional API change is declared per-item in the queue and re-confirmed by the user. Renaming a `[SerializeField]`/serialized public field without `[FormerlySerializedAs]` silently corrupts scene and prefab data — it is a forbidden move unless the item declares it and adds the attribute.
2. **No gate, no structural change — and gates have strength, not just existence.** Every queue item carries a gate-strength class: **G3** behavioral (an existing e2e/simulation/parity test or harness would fail if the touched behavior diverged), **G2** indirect (the subsystem is exercised but this behavior isn't pinned), **G1** compile-only. S items demand G2+; a G1 structural item is demoted to pure-move relocation, preceded by a characterization-test item (class **T**: pin current behavior at a stable boundary before restructuring behind it — the Feathers discipline), or carries an explicit user-confirmation flag. A package whose S items are predominantly G1 is **flagged at-risk** in the survey and the scorecard — for a commercial package, the missing suite is itself a publish-readiness finding. State what was excluded and why — silent scope truncation reads as "covered everything".
3. **One item, one dispatch, one commit.** The implementer never batches queue items. A failed gate stops the item; the orchestrator decides retry/skip/escalate.
4. **Metrics are computed on csharpier-normalized sources** (the scorecard tool does this), statement count must agree in direction with LOC, and comment lines never count as code reduction. The full soft battery is always reported together — never a single number in isolation.
5. **The adversary never implements; the implementer never self-grades.** Tell-scan and blind A/B readability judgments come from `shipshape-adversary`, dispatched with the item diff and no design rationale.
6. **Unity transport is checked at the moment of each invocation** (process scan per the project's CLAUDE.md); briefs say "check whether the editor is running", never assert editor state.
7. **Git:** branch from local `main`; never push; submodule changes commit in the submodule first. A dirty target repo blocks the run — surface it, don't stash.

## Models and token economy

Refactoring runs are long; the model tier and the reading discipline are chosen for cost, not prestige.

- The shipshape agents are pinned to **Opus** in their definitions — judgment-grade work (survey, structural edits, adversarial review) at the economical tier. Never bump a dispatch to a more expensive tier by default; the top-tier model is for the orchestrator's own synthesis only when the session already runs on it.
- **M-class (mechanical) items run on Sonnet** via the Agent tool's per-dispatch `model` override — formatter runs, enforcement-file commits, and deterministic sweeps need no judgment premium.
- The orchestrator stays thin: it reads one-line agent statuses and the group files' summary tables, never source code, never full deliverable bodies it can summarize from headings. Deliverables travel via disk, not return text.
- Briefs scope the agent's reading to the item: the implementer reads its item's files end to end and nothing else; the surveyor reads the baseline's offender list plus a bounded sample, not the whole tree. Instrument output is generated once into `00-baseline.md` and referenced, not regenerated per dispatch (`--count-only` mode for repeat tell runs).
- One item per dispatch is the token bound as much as the safety bound — a failed gate wastes one item's context, not an afternoon's.

## Protocol

### Step 0 — Preflight
Confirm target repo path; verify clean tree and note the branch; read the consuming project's CLAUDE.md for gates and conventions; identify the verification gates (exact commands) and whether the package has tests at all. Pick `<slug>`. Create the refactor branch `shipshape/<package-short-name>` from local `main`.

### Step 1 — Baseline
Run `tools/shipshape-metrics.py`, `tools/shipshape-tells.sh`, `tools/shipshape-asmdef-graph.py` (and jscpd if available) against the target. Write results to `docs/orchestrate/shipshape-<slug>/00-baseline.md` in the target repo (or the consuming project when the package repo should stay clean of orchestration docs). This is the "before" half of the scorecard and the surveyor's raw material.

The baseline includes a **gate survey**: test assemblies and counts, what the tests assert at (e2e/simulation/parity at stable boundaries vs implementation-coupled units), the exact run commands, and which subsystems no test reaches. E2e/simulation/boundary tests are the gates that survive refactoring — implementation-coupled unit tests die in exactly the restructurings they're meant to protect. Don't gate on line-coverage percentage: its negative space is assertion strength (full coverage with weak asserts pins nothing). The per-item proxy is reachability of touched symbols from tests; the occasional honest audit before a large structural campaign is mutation testing (Stryker.NET / stryker-js / cargo-mutants). Slow behavioral suites gate items on the filtered subset reaching the touched code, with the full suite once at MR close.

### Step 2 — Survey (dispatch `shipshape-surveyor`)
The surveyor reads the baseline, the asmdef graph, and the code, and writes `01-survey.md` in two parts: the form verdict, then the work queue.

**Part 1 — form verdict.** Queueing items presupposes the package deserves its current form; that presupposition is checked first, because a queue polishing a package that should be re-founded is the worst spend in the methodology. Three findings:

- **Identity statement** — what the package is to its user, one paragraph, written without the current implementation's vocabulary (the Lamport problem-before-solution discipline).
- **Comparator survey** — 2–4 regarded OSS packages doing the same job: their structure layout (assemblies/folders/types), size, and public-surface shape. These anchor structure the way STYLE.md anchors style, and LOC-per-feature against them is the cheapest rewrite detector available — no internal metric reveals that a package is 10× the regarded equivalent's size; only the comparison does. The comparators also define the domain's **organizational idioms** — see the idiom-conformance category below.
- **Verdict: reshape / re-found subsystem / rewrite**, with evidence: whether load-bearing abstractions fight the domain's standard pipeline (functionality compounded onto an improper harness), whether queue-item friction is dominated by working *around* the foundation rather than in it, and the comparator ratio.

A re-found or rewrite verdict is a **user gate, always** — it is a forced near-tie judgment; the surveyor widens the gap with facts and escalates, never begins a rewrite. If the user takes the rewrite branch, the deliverable changes shape: (1) a negative-space map of the existing package — unspoken assumptions, API calls deliberately avoided, problems designed out — or the rebuild reintroduces every avoided problem; (2) boundary/e2e characterization tests that survive into the new implementation and make the rewrite verifiable; (3) a `/recipe-spec` dispatch for the rebuild specification. The metric battery still judges the result: feature set constant, boundary tests green, and only then is a 90% reduction real rather than claimed.

**Part 2 — the queue** (on a reshape verdict, or alongside a re-found verdict for the surviving territories). Every queue item carries: scope (files/symbols), class (`M` mechanical / `C` comment-layer / `S` structural), expected gate, risk note, and expected metric movement. Class definitions:

- **M — mechanical:** formatter runs, enforcement-file commits, deterministic sweeps (deletable trailing `//` markers, emoji, dead usings). Near-zero judgment.
- **C — comment-layer:** narration deletion, change-history relocation to `Documentation~/`, fact deduplication to one canonical home, XML-doc gap fill on public API.
- **T — characterization tests:** pin current behavior at a stable boundary (e2e/sim style) ahead of a structural item whose gate is G1/G2. Sequenced immediately before the item it enables.
- **S — structural:** method decomposition, duplicate-logic extraction, type moves, asmdef splits. Requires a G2+ gate (hard rule 2).

S includes **domain-idiom conformance**: deviation from the organizational pattern the platform and the comparators treat as standard is queue-able even when no generic smell fires — ungrouped ECS systems with implicit ordering where the idiom is named SystemGroups with explicit `[UpdateInGroup]`/`[UpdateBefore]` edges; render work bypassing the pipeline's pass abstraction; ad-hoc error enums where the ecosystem expects the standard error-type idiom; non-standard package export shapes. The generic smell catalogue is structurally blind to this class — nothing is locally wrong; the deviation exists only against the external reference, which is exactly what the comparator survey provides. Idiom-conformance items are behavioral, not cosmetic (reorganization changes ordering/dispatch), so they demand G3 gates and an explicit risk note.

### Step 3 — Queue confirmation (user pause)
Present the queue with per-item gates and risk. The user selects the slice (an "afternoon" is typically all M + C items plus 1–3 S items). In `--auto` mode (the user explicitly granted unattended time), skip this pause, execute the queue in M → C → S order, and stop at the first S item whose gate fails twice.

### Step 4 — Execution loop (dispatch `shipshape-implementer` per item)
For each selected item: dispatch the implementer with the item, the canon, and the gates; the implementer edits, runs the gate, commits on green, and logs to `02-execution.md`. After each S item (and after the full C batch), dispatch `shipshape-adversary` on the accumulated diff; adversary findings become new queue items or revert decisions.

### Step 4.5 — Formatting-repair pass (class F)
After every M/C/S item has landed and one final `csharpier format .` has run, repair what the formatter degraded — **before** the final gate, so the repaired layout is what gets verified. Dispatch the **`shipshape-formatter` agent, which is pinned to Sonnet** (the regrouping is mechanical pattern application, not design); if dispatching the generic implementer instead, pass `model: "sonnet"` explicitly.

This is not a matrix-fixer — it covers the whole class of constructs csharpier's width-only wrapping harms, in both directions: structured literals and boolean gates *flattened* onto one wide line (matrix rows, mixed `&&`/`||` precedence, multi-arm ternaries invisible), and fluent/LINQ chains and long conditions *shredded* one fragment per line so logical stages no longer group. The repair is the trailing-`//` idiom at the logical boundary (one matrix row, one precedence level, one pipeline stage per line); the `//` makes it survive future csharpier passes.

- **Primary surface is the csharpier diff** — the lines the final format pass changed. The pass evaluates the quality of the auto-formatting only; it does not re-open refactoring decisions or touch lines csharpier left alone. `tools/shipshape-fmt-suspects.py` is a deterministic net layered on top: STRUCTURED-LITERAL hits are precise, LOGIC/CHAIN/WIDE are heuristic candidates the agent judges and filters.
- Restraint is part of the job — a `//` on a line that needed no break is itself a tell. Not every flagged line is damage.
- The repair is **token-identical** by construction — only whitespace and trailing `//` change. Verify with `git diff --ignore-all-space` showing only `//` additions, confirm `csharpier format .` is now idempotent over the result, and gate it (a regrouped matrix that transposed a row is a correctness bug the test suite catches).

### Step 5 — Scorecard and MR summary
Run `tools/shipshape-scorecard.sh <repo> <base> <head>` for the full battery diff. Dispatch the adversary once more for the blind A/B judgment on the three most-changed files (order-randomized, judge ≠ author). Write `03-scorecard.md`: hard-gate results, soft-metric table (before → after), tells removed/remaining, items deferred and why. The MR is the branch plus this scorecard; the user pushes and merges.

## Scaling beyond one context window

The survey is bottlenecked by judgment, not reading — the deterministic layer has no context window, so codebase size changes the fan-out, never the protocol.

- Instruments run first at any scale: metrics, tells, duplication, module graph compress arbitrarily many lines into fixed-size ranked offender lists. Model reading is reserved for confirming and characterizing the top of each list.
- Past roughly one window of code, partition into survey territories along the module graph's seams (the graph itself always fits) and dispatch one surveyor per territory in parallel, each writing its own queue section; the orchestrator merges from summary tables. Cross-territory duplication and tells are caught by the global instruments, not by any one surveyor's reading.
- Within a territory, sample stratified by authorship era (per-folder metric fingerprints and git authorship mark the boundaries): smells cluster, so a stratum's character is establishable from a dozen representative files plus its offenders.
- Completeness comes from campaign rounds, not one heroic survey: each MR cycle ends with a fresh baseline, the next survey starts from the new offender list, and convergence is the battery trending flat (loop-until-dry), never a claim of full coverage.

Partitioning: collapse the module graph's SCCs first (a cycle is one territory by definition), cut at thin seams — a good territory is characterizable without reading its neighbors. The shared foundation (Core/Common layers) is its own territory and goes **first**, so downstream surveyors read its findings instead of re-discovering them N times. Size territories by the surveyor's one-dispatch reading budget (~50–150k tokens of offenders + stratified sample), not by equal LOC, and keep each territory's test assemblies inside it so gate strength is judged per lane.

Orchestration: contention decides parallelism. The survey wave is read-only and fans out maximally; execution lanes are parallel across repos and serial within one (git index; for Unity, the editor instance lock makes the *gate* the bottleneck). Gate granularity matches risk class — S items gate individually, a run of M/C items may commit individually and share one gate at batch end, bisecting by commit on failure. Past a handful of territories go depth-2 (orchestrator → territory leads → implementers) so no context accumulates the campaign; schedule the longest lane first (makespan is bound by it); adversary runs per lane batch, not per item.

## The metric battery

HARD gates (any failure rejects the item or the run):
- H1 Tests pass with `testcasecount > 0` — a zero-discovery run is a silent pass, not a pass.
- H2 Public API surface unchanged (scorecard's public-symbol diff) unless the item declared the change.
- H3 Compile clean with no new warnings.
- H4 No new asmdef cycles (`shipshape-asmdef-graph.py` flags them).
- H5 Project-specific behavioral gates where they exist (e.g. perceptual-metrics harnesses for rendering packages).

SOFT battery (directional, judged jointly — `shipshape-scorecard.sh` emits all of it):
- S1 Code LOC ↓ on normalized sources, statement count agreeing in direction.
- S2 Method length p95/max ↓, paired with S3 so fragmentation into pass-through chains gets caught.
- S3 Max nesting depth ≤ 4; long-method top-10 list shrinking.
- S4 Duplication % ↓ (jscpd), dedup mechanism reviewed by the adversary — force-parameterized god-helpers are worse than honest clones.
- S5 Comment density inside the 5–20% band, with the narration-classifier count at zero new hits. A band, not a direction: deleting `///` API docs to shrink a number is a regression.
- S6 Tell-battery hits ↓ per category, zero new.

Never optimize any single soft metric in isolation; the known failure modes (golfing, comment mass-deletion, complexity laundering into dispatch tables, method fragmentation) are each caught by the paired metric listed above. The Maintainability Index is excluded from the battery entirely — its 1992 regression fit is discredited and it rewards comment deletion.

## Anti-patterns

- One heroic diff for the whole package — degradation over long sessions is measured; the queue exists to bound each loop.
- Refactoring a package with no gate "carefully" — care is not a gate. Comment/enforcement items only, and say so.
- The implementer "noticing" adjacent improvements mid-item — new findings go back to the queue, not into the diff.
- Accepting "LOC went down" while statement count went up — that is line-packing, and the scorecard exposes it.
- Treating tell-scan output as auto-fail — hits are flags for judgment; ≥3 categories firing on one file is the strong signal.
- Rewriting where relocation suffices — real refactors show a high moved-line ratio (`git diff --color-moved=zebra`); wholesale regeneration is itself a tell.

## Non-overlap with sibling skills

| Skill | Domain |
|-------|--------|
| `/refactor` | One module, one known smell-cluster: explore → design → apply with user-gated phases. |
| `/sniff`, `/dry`, `/deadcode` | One-shot find-and-fix sweeps for their specific smell families. |
| **`/shipshape`** | **Whole-package publish-grade pass: baseline → queue → gated loops → scorecard, with style canon and tell-removal.** |
