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
2. **No gate, no structural change.** An item that restructures code requires a runnable verification gate (tests, compile probe, perceptual harness). Scopes with no gate are limited to comment-layer, documentation, and enforcement-file items until a gate exists. State what was excluded and why — silent scope truncation reads as "covered everything".
3. **One item, one dispatch, one commit.** The implementer never batches queue items. A failed gate stops the item; the orchestrator decides retry/skip/escalate.
4. **Metrics are computed on csharpier-normalized sources** (the scorecard tool does this), statement count must agree in direction with LOC, and comment lines never count as code reduction. The full soft battery is always reported together — never a single number in isolation.
5. **The adversary never implements; the implementer never self-grades.** Tell-scan and blind A/B readability judgments come from `shipshape-adversary`, dispatched with the item diff and no design rationale.
6. **Unity transport is checked at the moment of each invocation** (process scan per the project's CLAUDE.md); briefs say "check whether the editor is running", never assert editor state.
7. **Git:** branch from local `main`; never push; submodule changes commit in the submodule first. A dirty target repo blocks the run — surface it, don't stash.

## Protocol

### Step 0 — Preflight
Confirm target repo path; verify clean tree and note the branch; read the consuming project's CLAUDE.md for gates and conventions; identify the verification gates (exact commands) and whether the package has tests at all. Pick `<slug>`. Create the refactor branch `shipshape/<package-short-name>` from local `main`.

### Step 1 — Baseline
Run `tools/shipshape-metrics.py`, `tools/shipshape-tells.sh`, `tools/shipshape-asmdef-graph.py` (and jscpd if available) against the target. Write results to `docs/orchestrate/shipshape-<slug>/00-baseline.md` in the target repo (or the consuming project when the package repo should stay clean of orchestration docs). This is the "before" half of the scorecard and the surveyor's raw material.

### Step 2 — Survey (dispatch `shipshape-surveyor`)
The surveyor reads the baseline, the asmdef graph, and the code, and writes a prioritized work queue to `01-survey.md`. Every queue item carries: scope (files/symbols), class (`M` mechanical / `C` comment-layer / `S` structural), expected gate, risk note, and expected metric movement. Class definitions:

- **M — mechanical:** formatter runs, enforcement-file commits, deterministic sweeps (deletable trailing `//` markers, emoji, dead usings). Near-zero judgment.
- **C — comment-layer:** narration deletion, change-history relocation to `Documentation~/`, fact deduplication to one canonical home, XML-doc gap fill on public API.
- **S — structural:** method decomposition, duplicate-logic extraction, type moves, asmdef splits. Requires a real gate.

### Step 3 — Queue confirmation (user pause)
Present the queue with per-item gates and risk. The user selects the slice (an "afternoon" is typically all M + C items plus 1–3 S items). In `--auto` mode (the user explicitly granted unattended time), skip this pause, execute the queue in M → C → S order, and stop at the first S item whose gate fails twice.

### Step 4 — Execution loop (dispatch `shipshape-implementer` per item)
For each selected item: dispatch the implementer with the item, the canon, and the gates; the implementer edits, runs the gate, commits on green, and logs to `02-execution.md`. After each S item (and after the full C batch), dispatch `shipshape-adversary` on the accumulated diff; adversary findings become new queue items or revert decisions.

### Step 5 — Scorecard and MR summary
Run `tools/shipshape-scorecard.sh <repo> <base> <head>` for the full battery diff. Dispatch the adversary once more for the blind A/B judgment on the three most-changed files (order-randomized, judge ≠ author). Write `03-scorecard.md`: hard-gate results, soft-metric table (before → after), tells removed/remaining, items deferred and why. The MR is the branch plus this scorecard; the user pushes and merges.

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
