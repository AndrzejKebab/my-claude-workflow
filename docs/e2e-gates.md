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
