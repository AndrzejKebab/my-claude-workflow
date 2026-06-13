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
- `tools/` — self-contained instrumentation (no project files, no network): `shipshape-metrics.py`, `shipshape-tells.sh`, `shipshape-scorecard.sh`, `shipshape-asmdef-graph.py`. Duplication detection uses `npx -y jscpd` when node is available.
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
The surveyor reads the baseline, the asmdef graph, and the code, and writes a prioritized work queue to `01-survey.md`. Every queue item carries: scope (files/symbols), class (`M` mechanical / `C` comment-layer / `S` structural), expected gate, risk note, and expected metric movement. Class definitions:

- **M — mechanical:** formatter runs, enforcement-file commits, deterministic sweeps (deletable trailing `//` markers, emoji, dead usings). Near-zero judgment.
- **C — comment-layer:** narration deletion, change-history relocation to `Documentation~/`, fact deduplication to one canonical home, XML-doc gap fill on public API.
- **T — characterization tests:** pin current behavior at a stable boundary (e2e/sim style) ahead of a structural item whose gate is G1/G2. Sequenced immediately before the item it enables.
- **S — structural:** method decomposition, duplicate-logic extraction, type moves, asmdef splits. Requires a G2+ gate (hard rule 2).

### Step 3 — Queue confirmation (user pause)
Present the queue with per-item gates and risk. The user selects the slice (an "afternoon" is typically all M + C items plus 1–3 S items). In `--auto` mode (the user explicitly granted unattended time), skip this pause, execute the queue in M → C → S order, and stop at the first S item whose gate fails twice.

### Step 4 — Execution loop (dispatch `shipshape-implementer` per item)
For each selected item: dispatch the implementer with the item, the canon, and the gates; the implementer edits, runs the gate, commits on green, and logs to `02-execution.md`. After each S item (and after the full C batch), dispatch `shipshape-adversary` on the accumulated diff; adversary findings become new queue items or revert decisions.

### Step 5 — Scorecard and MR summary
Run `tools/shipshape-scorecard.sh <repo> <base> <head>` for the full battery diff. Dispatch the adversary once more for the blind A/B judgment on the three most-changed files (order-randomized, judge ≠ author). Write `03-scorecard.md`: hard-gate results, soft-metric table (before → after), tells removed/remaining, items deferred and why. The MR is the branch plus this scorecard; the user pushes and merges.

## Scaling beyond one context window

The survey is bottlenecked by judgment, not reading — the deterministic layer has no context window, so codebase size changes the fan-out, never the protocol.

- Instruments run first at any scale: metrics, tells, duplication, module graph compress arbitrarily many lines into fixed-size ranked offender lists. Model reading is reserved for confirming and characterizing the top of each list.
- Past roughly one window of code, partition into survey territories along the module graph's seams (the graph itself always fits) and dispatch one surveyor per territory in parallel, each writing its own queue section; the orchestrator merges from summary tables. Cross-territory duplication and tells are caught by the global instruments, not by any one surveyor's reading.
- Within a territory, sample stratified by authorship era (per-folder metric fingerprints and git authorship mark the boundaries): smells cluster, so a stratum's character is establishable from a dozen representative files plus its offenders.
- Completeness comes from campaign rounds, not one heroic survey: each MR cycle ends with a fresh baseline, the next survey starts from the new offender list, and convergence is the battery trending flat (loop-until-dry), never a claim of full coverage.

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
