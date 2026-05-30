# Brute-force protocol (opt-in alternative to diagnose-first)

Sidecar to `SKILL.md` — read this only when brute-force is actually engaged. An opt-in mode that trades orchestrator-context-hygiene for sub-agent autonomy. Where diagnose-first keeps the orchestrator in the loop and dispatches one read-only diagnostic at a time, brute-force dispatches ONE sub-agent that owns the entire hypothesise-test-iterate loop end-to-end, against a deterministic probe-gate, with a private progress file the orchestrator NEVER reads. The orchestrator sees only a final-deliverable summary on success or an architectural-escape-hatch report.

This mode is legitimate alongside diagnose-first, not a replacement. They suit different conditions.

## When to use brute-force

All four should hold:

1. **A clean deterministic probe-gate exists.** A passing/failing programmatic signal (SSIM threshold, unit test, CI check, byte-exact oracle) that takes minutes — not hours — to run. The gate must be analytically valid (the e2e-gate authoring discipline in `e2e-gates.md` still applies — captures must show the artefact; threshold must be calibrated against user-confirmed pre-fix runs).
2. **Iteration cost is low.** Building + running the gate fits comfortably in one sub-agent's context window (~5–15 mins per round; agent can run 10–30 rounds before context exhaustion).
3. **Scope is bounded.** The expected change surface is one module or a small set of files. Open-ended "could touch half the codebase" scope disqualifies — the agent would rabbit-hole.
4. **The orchestrator has either repeatedly failed diagnose-first cycles** (3+ fix attempts didn't help; the search space is broader than the orchestrator's hypotheses keep finding) **OR the user explicitly engages it** ("lets do brute-force protocol"). Don't open with brute-force on a fresh task — diagnose-first's lighter ceremony is the right default.

## When NOT to use brute-force

- No clean probe-gate. The only verification is "user looks at the binary". Use diagnose-first + visual verification gates instead — the user IS the analytical surface and can't be replaced by a gate.
- Probe-gate takes >15 mins per run. Iteration cost too high; the agent burns its context on waiting.
- The user wants a design-approval gate before code is written. Brute-force commits code on every hypothesis attempt; the user reviews only the final 3×PASS submission.
- The orchestrator already knows the right architectural shape and just needs an architect → impl walk (with optional opt-in reviewer if the change is high-stakes). Use distributed mode.

## Protocol shape

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

## What the summary doc contains

- One line: the final-hypothesis that produced the PASS.
- File:line touch list of the landed change.
- Verbatim three-run probe-gate output (proving indeterminism is ruled out).
- One paragraph: what the agent tried that DIDN'T work (compressed, NOT a full progress log).
- If the architectural-escape-hatch fired: the design sketch instead of a PASS report.

## Context hygiene (binding)

- The agent's progress file is **NEVER** read by the orchestrator. Not for status checks, not for "interesting details", not to populate the next agent's brief. The whole point is that the orchestrator's context stays clean across long iteration loops.
- The brief must explicitly state: "track your attempts in `<progress-file>`. The orchestrator never reads that file. Do NOT echo attempt details back via your return text — that pollutes the orchestrator's context the same way."
- The summary file IS read by the orchestrator. Keep it terse; everything verbose goes in the progress log.

## Comparison with diagnose-first

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

## Anti-patterns specific to brute-force

- **Orchestrator reading the progress log.** Defeats the entire mode. The progress log is for the agent's own bookkeeping across its own context; it accumulates verbose detail by design. Reading it pollutes the orchestrator with the very context the protocol exists to isolate.
- **Sub-agent following the orchestrator's "recommended fix shape" verbatim.** The brief usually contains an orchestrator's recommendation from the prior diagnose-first cycles. The brute-force agent treats that recommendation as ONE hypothesis among several, ranked by the agent's own analysis. If the agent just executes the recommendation, brute-force adds no value over a regular impl dispatch.
- **Submitting on a single PASS.** Indeterminism kills the entire signal. Three consecutive PASSes is the floor; anything less is a fluke.
- **Skipping the predict-the-outcome line.** Without it, the agent can rationalise any PASS as "the fix" even when the gate moved for unrelated reasons. The prediction must be written BEFORE the gate run, in the progress log.
- **Pushing through the escape-hatch.** When the agent realises the right fix is architectural, the protocol REQUIRES exit. Pushing through with a hack that "happens to make the gate pass" produces a brittle PASS that regresses on the next change. Escape is not failure — it's the protocol working.
- **Using brute-force as the default opening mode.** Brute-force is heavy (one sub-agent eats many rounds of context). On a fresh task with no failed diagnose-first cycles, the lighter ceremony of regular dispatching is correct. Brute-force earns its weight when diagnose-first has demonstrably stalled.
