# E2e gates under agentic development

Gates are as important as the spec. The spec states what correct is; the gate makes incorrect
unacceptable by construction. Under semi-supervised agentic flow nobody — user or orchestrator —
has complete sensory-spatial assessment of every result, and agents optimize toward whatever
acceptance signal exists. The gate is the only channel that cannot be talked past: a well-formed
gate logically excludes accepting an invalid or partially falsified result. Gate quality bounds
result quality; a weak gate converts confident agent reports into silent regressions.

Sidecar: `skills/delegate/e2e-gates.md` — the authoring workflow for gates that capture a
user-described visual symptom (user verifies captures before threshold calibration). This page is
the general criteria; that page is the visual-capture dispatch shape.

## Criteria

1. **Black box.** Control signals in → real app tick → metrics out. The gate drives the shipped
   pipeline; it never reimplements the loop. Feature isolation is app config, not a test fork.
2. **Independent oracle.** Expected values come from closed-form math (analytical primitive), a
   constructed golden case, or a brute-force reference implementation of the same physics. The
   system never blesses its own output; a captured golden is valid only if its provenance is an
   independent oracle or a user-confirmed capture.
3. **Exact by default.** Bit-exact / SSIM = 1.00 wherever determinism permits; epsilon only where
   physics genuinely denies equality, with the justification written in the gate. Corollary:
   design the system for determinism so exactness is reachable — an epsilon is never a licence to
   paper over a nondeterminism bug.
4. **Capture the real artifacts.** Internal buffers and state alongside the final frame. The
   defect's mechanism must be what diffs; a gate that only sees the composited output can be green
   while the mechanism churns underneath.
5. **Cross-referenced conditions.** Measure the same subject under conditions that must — or must
   not — change it, and assert the diff between conditions. Invariance assertions (condition must
   change nothing) are as load-bearing as difference assertions.
6. **Mechanism over proxy.** Assert the mechanism itself — a render pass absent from the frame, an
   allocation counter at zero — never a correlate (GPU-time ≈ 0, "looks smooth", headless proxy
   renderer while the user runs a real GPU).
7. **At least one absence criterion.** Something that must NOT happen, asserted: no event below
   threshold, no output outside the domain, no work while idle. Difference-only gates miss
   over-eager behavior entirely.
8. **Bite proof.** Red on the pre-change artifact, green after, non-vacuously. A gate that never
   failed proves nothing about what it guards.
9. **Durable.** Gates land as permanent suite members maintained with the codebase (user law,
   2026-07-14: "all gates should land as durable e2e tests that we intend to maintain as part of
   this package") — not one-shot acceptance scripts.
10. **Human eye is the final tier, not a substitute.** Mechanical gate first (SSIM/exact against
    representatives), then human-eye PNG review tops off visual claims
    (verification-representatives protocol).

## Shapes that work

Ordered by how much they survive *not knowing what correct looks like* — the situation you are
usually in when chasing a reported defect.

1. **Invariance.** The output must not depend on X: ordering, timing, batching, position,
   partitioning, an unrelated setting, what else is in the same request. Asserts nothing about
   correctness, so it cannot be argued with on content grounds, and one such gate covers a whole
   class of defects at once. Reach for this first.
2. **Differential A/B.** One subject, exactly one variable changed, the two outputs compared.
   Content-agnostic: it never claims which output is right, only that this variable must not have
   moved it.
3. **Round trip / identity.** What went in comes out; `decode ∘ encode = id`. Exact by default.
4. **Analytical oracle.** Closed form where the domain has one.
5. **Real content.** When the defect may be content-dependent, a synthetic stand-in is a
   *hypothesis*, not a control. Drive the real asset, the real scene, the real payload.
6. **Absence.** Something that must not happen (criterion 7 above).

## Why a gate comes back falsely green

**A green gate is a claim about the fixture as much as about the code.** Nearly every false green
is a fixture that *could not have failed*. Red-first is therefore not paperwork — it is the only
evidence the fixture can express the defect at all. When a gate is green while the reported symptom
persists, suspect this list before concluding the report was wrong.

1. **Regime removed by scaling down.** The defect exists only past a threshold — size, count,
   distance, duration, concurrency, memory pressure, cache capacity. A fixture shrunk to run fast
   is a *different system*, and the shrunk dimension is often exactly the one the defect needs.
   Reproduce the regime, not the shape; if real scale is expensive, pay it once behind a category
   rather than shrinking it into vacuity.
2. **Degenerate content.** The data has no variation along the axis the code branches on: a flat
   field under slope-dependent logic, one material under selection logic, one element under
   ordering logic, one client under contention logic. The branch under test never executes.
   *Tell:* every arm produces identical output.
3. **Settled away.** The defect lives in a transient — in flight, mid-stream, pre-convergence — and
   the fixture flushes, awaits, sleeps or converges before measuring, closing exactly the window
   under test. Never force-flush the subsystem you are gating.
4. **Measured at the wrong layer.** An internal artifact compares equal while the symptom lives
   downstream of a path that does not read that artifact. *Tell:* an internal diff reports 100%
   identical while the end-to-end symptom persists. Measure at the boundary where the symptom is
   observed, then work inward.
5. **Blind oracle.** The metric does not respond to the symptom's channel — brightness where the
   symptom is hue, mean where it is distribution, presence where it is order, total where it is
   the tail. Feed the oracle a known-bad input and confirm it fires; an oracle that has never
   fired is not an oracle.
6. **Two variables.** The arm and its control differ in more than the thing under test, so a
   difference cannot be attributed and an equality is coincidence.
7. **Leaked fixture state.** Shared instances, statics, caches or on-disk residue carry
   configuration between cases. *Tell:* results depend on execution order. Reset in setup, not
   teardown.
8. **Vacuous pass.** The assertion ran over an empty or degenerate sample. Guard the preconditions
   as assertions and log the witness counts, so a green states what it actually examined.

## How you know a fixture could have failed: the negative control

Do not reason about whether the gate *would* catch a regression. **Sabotage the subject and watch
it go red.** If deliberately corrupting the thing under test does not turn the gate red, the gate
is not measuring that thing, whatever its assertions say.

Cheap sabotage, in rough order of how little you need to know about the code: overwrite the output
with a constant; skip the pass or return early; zero a coefficient; drop or duplicate every other
element; shift an index by one; feed the stage an empty input. Any of these is a *known-bad input*,
which is the thing an oracle must be validated against.

Red-first is the special case where the pre-change code is the sabotage. When the symptom cannot
be reproduced yet — the usual situation when chasing a report — sabotage is the only proof of
capability available, and it is available immediately.

**Record the result in the gate.** "Poisoning the X buffer moves this metric 0.03 → 0.71" is the
gate's demonstrated sensitivity, it is what makes the threshold defensible instead of invented, and
it tells the next reader what the gate is for. A gate whose comment cannot state what it caught, or
what it was seen to catch, is decorative.

### The separation criterion — for any threshold

Before choosing a number, measure two spreads:

- **Noise floor N** — the metric between repeated *good* runs (re-run, re-render, reseed).
- **Signal S** — the metric between a good run and a sabotaged one.

Require `S >> N` — an order of magnitude is a sound default — and put the threshold in the gap. If
`S ≈ N` the metric is blind to the defect class: **change the metric, not the threshold.** A
threshold chosen without knowing N is a coin flip that will either flake or never fire.

### Witness — a pass must state what it examined

Print the evidence: sample count, how many samples were non-degenerate, how many crossed the branch
under test, the value of the metric on each arm. A gate that prints only pass/fail cannot be
distinguished from a gate that examined nothing, and a vacuous pass looks exactly like a real one
in a suite summary.

## When you cannot build an oracle: capture what the user sees

The last resort, and frequently the fastest route to a real gate. It applies whenever "correct" is
easier to recognise than to define — rendered output, audio, layout, generated documents, anything
perceptual.

1. **Capture at the boundary the user perceives.** The final frame, the rendered page, the played
   buffer, the response body. Not an internal artifact that seems related — an internal buffer can
   compare identical while the symptom lives downstream of a path that never reads it.
2. **Capture the same artifact under a configuration known to be good** — before the change, a
   working peer, the live path, the other backend. Now you have a pair.
3. **Show the pair to the user and have them say which is wrong, before choosing any metric.**
   Their eye is the oracle you do not have. This is the step that cannot be skipped: it is what
   converts a hypothesis into a labelled example.
4. **Only then pick the metric**, and pick it so it separates *those two captures* with margin
   (the separation criterion above). Re-run to confirm the margin is stable.
5. **Keep both captures as gate artifacts**, so the next reader sees what it guards.

Order matters: **capture → confirm → threshold**. Inventing a threshold first and then looking at
the output is how you get a metric that agrees with your hypothesis instead of with the artifact.

### Grade in the reporter's vocabulary

When a symptom is described in words, measure the quantity those words name. "Washed out" is
saturation, not brightness. "Wrong colour" is hue, not difference. "Stutter" is the frame-interval
distribution, not the mean. "Out of order" is order, not content. "Truncated" is length. A metric
borrowed from a different channel than the complaint will sit at its noise floor while the defect
is fully present — and it will report green with a plausible-looking number attached.

## What a good gate looks like

Concretely, and in one sentence: **it captures the user-visible artifact under two configurations
that must agree, with a metric demonstrated to separate a sabotaged capture from a good one, and it
prints what it examined.** Around that core:

- **Provably red on demand** — sabotage turns it red, and the gate says so in its comment.
- **Invariance-shaped where possible** — asserts that X must not change the result, so it needs no
  definition of correct and cannot be argued with on content grounds.
- **Wide margin** — the failing and passing states are separated far beyond run-to-run noise.
- **Names its catch** — the comment states the defect it exists for, in mechanism terms.
- **Answers "what would this catch?"** — name three plausible regressions in the guarded area; if
  none of them would trip it, it is decoration regardless of how it is written.

## Confirming a cause, and confirming a fix

- **Predict, then move it.** A hypothesis that merely explains the observation is a story. State
  how the symptom must *move* if the hypothesis holds, then move the suspected cause and check.
  A cause that survives a prediction is confirmed; one that cannot be predicted from is not.
- **Measure the fix.** A change that does not move the metric is not the fix. Revert it rather
  than shipping a no-op with a confident comment attached.
- **Never loosen an assertion to reach green.** If the assertion is wrong, the claim was wrong —
  restate the claim and say so; do not widen the epsilon.

## Worked examples (miniheightfields testbed, shadow rework 2026-07)

- **Two-camera isolation** (criteria 3, 4, 5): cameras A and B at different poses; three runs —
  A solo, B solo, A+B every frame — each capturing rendered frame AND internal shadow buffers
  (box, history, confidence) per camera per frame; SSIM = 1.00 cross-referenced A-solo↔A-while-B
  and B-solo↔B-while-A. The defect (cross-view history churn) is precisely what diffs. Exactness
  forced a design improvement: all sampling counters became per-view state, because a global
  counter legitimately fails 1.00.
- **Analytic overhang** (criterion 2): cliff of height H at a terrain edge, sun elevation α — the
  cast shadow must extend `H/tan(α)` past the edge within one texel, for ≥3 α. The oracle is
  trigonometry; no blessed capture to rot.
- **Analytic wedge** (criteria 2, 8): one planar ramp gives a closed-form shadow volume; probes at
  (XZ, h) strictly inside/outside must read shadowed/unshadowed across sun elevations and heights.
  Fails on the pre-fix XZ-only sampling; passes only when the term respects receiver height.
- **Dense-cone world-space golden** (criteria 1, 2): a brute-force dense-sample reference of the
  same shadow physics, compared to the production path via SSIM — an independent implementation as
  oracle, driven through the real pipeline fixture.
- **Idle stability** (criteria 6, 7): a converged static scene must record NO shadow fill/temporal
  pass at all — render-pass capture, an absence proof; "GPU time ≈ 0" would be the proxy version
  and would pass with a cheap-but-present pass.
- **No phantom walls / sub-threshold immunity** (criterion 7): flat terrain must cast zero shadow
  outside its footprint (catches edge-clamp extrusion); a sun oscillating within θ must NOT
  re-trigger convergence, while accumulated drift past θ MUST — both halves gated.
- **Converged-equivalence across budgets** (criteria 3, 5): for S ∈ {8,16,32,64}, the converged
  static output must equal the S=64 reference (near-equality SSIM + an artifact detector showing
  no S-dependent structure) — an invariance cross-reference: the setting buys convergence time,
  and the gate forbids it buying anything else.
- **Config-gated observables** (criteria 1, 6): per-pass app-config toggles
  (`HeightfieldBenchmarkGates.Shadow*`) and internal counters
  (`HeightfieldDiagnostics.AccumulateShadowBake`) let gates isolate and count mechanism events
  without forking the loop — feature gates are APP CONFIG, the test stays black-box.
- **One real-pipeline driver** (criterion 1): a single fixture (`TerrainRenderTestFixture`,
  26 suites) stands up the real pipeline, spawns terrain/sun/camera, ticks `Camera.Render()` —
  every gate drives the shipped loop through it; none reimplements a sim step.

## Anti-patterns

- **FAIL→PASS as sole validation.** A threshold can be tuned to make almost any pre/post pair
  transition; prove the gate measures the artifact (independent oracle or user-verified capture),
  not just that the metric moved.
- **Self-referential goldens.** Capturing today's output and comparing tomorrow's against it
  guards the implementation's accidents, not the spec — unit testing in an e2e costume.
- **Proxy environments.** Green on a headless/software renderer while the user runs a real GPU is
  worse than no gate: it reports health the artifact doesn't have.
- **Epsilon as amnesty.** A tolerance wide enough to absorb the defect class it guards. Every
  epsilon carries a one-line justification of the nondeterminism it covers.
