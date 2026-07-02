---
name: warden
description: Deliberate structural pass verifying a repo's structural laws (AGENTS.md/CODESTYLE.md) over a diff or the whole tree. One fresh agent per law family, evidence gathered by enumeration before judgment, findings reported for separate fix dispatches. Use at /delegate close-out, before merges, or as a periodic horizontal audit ("/warden", "/warden tree", "run a structural pass", "check the laws").
---

# warden

## Premise (why this skill exists)

Implementing agents are token predictors with bounded windows: they cannot hold cross-cutting structure, count pattern instances, or sense sibling code, and they write to the gate they are given. Instruction raises the floor; guarantees come from verification. **Structure gets its own deliberate passes** — each law checked by a fresh context whose entire attention is that one law, fed evidence gathered by enumeration (Grep/Glob/ls) run within the pass.

Warden only reports. Fixes are separate dispatches (or the user's call) — a checker that edits is an implementer with a conflict of interest.

## Inputs

- **Laws file** — the repo's `AGENTS.md` (fallback `CODESTYLE.md`). Refuse to run without one; the pass needs written laws to check against.
- **Scope** — `diff [<range>]` (default: working tree + HEAD vs merge-base with the default branch) or `tree` (whole repo; the periodic horizontal audit).

## Protocol

1. **Partition.** Read the laws file. Group laws into pass families (default partition below; a repo's laws may add or remove families). In `diff` mode, drop families whose subject the diff cannot touch — placement and seam-purity always run (cheap, and violations hide in "unrelated" files).
2. **Dispatch.** One fresh `warden` agent per family, in parallel. Each brief carries: the law(s) verbatim from the laws file, the enumeration procedure (the family's evidence-gathering commands), the scope, and the findings path. One agent per family keeps attention undivided; a single agent checking every law drifts into vibes. The agent definition carries the verdict-discipline conviction (the two judging pulls and their rails) — briefs point at the laws and the evidence, without restating it.
3. **Collect.** Each agent writes its section to `docs/orchestrate/warden-<scope>-<date>/findings.md`. An agent claiming "no violations" must show the enumeration it ran (commands + hit counts); an absence claim arriving without its enumeration gets rejected and re-dispatched.
4. **Synthesize** (orchestrator): one table — `| law | file:line | violation | suggested fix locus |` — ranked by blast radius, plus three follow-up lists:
   - **Borderline calls:** the agents' genuine-uncertainty verdicts, surfaced to the user with what would settle each. These are judgment calls the user admits or dismisses; dismissed ones that keep recurring point at a law whose wording needs sharpening.
   - **Mechanize candidates:** any check that reduced to greps + trivial judgment gets proposed as a lint under the repo's `tools/` (per the ad-hoc-instrumentation rule), making the next run free and deterministic.
   - **Law gaps:** violations that felt wrong but matched no written law → proposed law amendments, surfaced to the user. The laws file changes only by user decision.
5. **Hand off.** Findings feed fix dispatches, parity-table rows, ceilings-register updates, or user decisions. The report is warden's only output.

## Default pass families

| Family | Checks | Enumeration first |
|---|---|---|
| **placement** | files/types in the wrong layer; forbidden tokens in sealed headers | grep API/type prefixes per layer rule; ls new files vs the placement map |
| **seam-purity** | test/bench/app concepts below a frozen seam; gate evidence computed in the wrong layer | grep test-harness identifiers (checksum, capture, png, bench) under platform/library dirs |
| **lockstep** | contract changed for fewer than all N implementations; silent default bodies; name-string dispatch | enumerate implementations of every touched contract member; grep override sets per sibling; grep `name()`/string compares in shared layers |
| **parity** | hardcoded behavioral constants without a parity row; sibling implementations diverging on a recorded row | grep literals in sibling implementations; diff against the repo's parity table |
| **instance-count** | shapes copied/extended past the rule of three without waiver | enumerate instances of the extended pattern (the diff shows what was copied; grep shows how many exist) |
| **invariants** | logged external reliances lacking their assert or doc line; index-equivalence smells (same index, two meanings) | grep impl logs for reliance entries; grep the named symbols for asserts |
| **ceilings** | register entries without checkable lift-conditions; entries whose condition has come true; lifted ceilings still listed | read the ceilings register; evaluate each condition against HEAD by enumeration |
| **consumers** | shared code reshaped without retrofitting all consumers | enumerate includers/callers of every reshaped shared symbol |

## Models and token economy

Passes are wide and frequent; tier and reading discipline are chosen for cost.

- **Enumeration-heavy, judgment-light families** (placement, parity, consumers) run on a cheaper tier / low effort via the Agent tool's per-dispatch `model`/`effort` overrides — the greps do the work, the agent classifies hits.
- **Judgment families** (seam-purity, instance-count, invariants, ceilings) inherit the session model; verdict quality there is the product.
- The orchestrator stays thin: it reads the findings file's tables and enumeration logs, and re-runs no enumeration itself. Agent reading is scoped by the family's procedure — hit sites plus enough surrounding code to judge, never the whole tree.
- In `diff` mode, run only the families the diff can touch (placement and seam-purity always run). A family with an empty scope returns in one turn; that is cheap insurance, and dropping it silently is how violations hide in "unrelated" files.

## Modes in practice

- **`/warden diff`** — pre-merge / delegate close-out. Minutes, few families, gate-adjacent.
- **`/warden tree`** — the scheduled horizontal audit (see the repo's `HUMANS.md` cadence). Expect real findings; budget a synthesis conversation with the user.
