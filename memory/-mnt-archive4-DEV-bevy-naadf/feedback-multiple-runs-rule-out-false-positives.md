---
name: feedback-multiple-runs-rule-out-false-positives
description: "For probes whose result is evidence (especially non-deterministic bugs), run ≥3× on suspect side, ≥2× on reference; aggregate across runs. One run is a data point, not a signal."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b6b284c-a4b9-4e10-80eb-a670749962ae
---

Single-run probes lie both ways:
- A pass hides intermittent failures (false negative).
- A fail might be unrelated flake (false positive).

**For bevy-naadf wasm/WebGPU:** bug class is run-to-run non-deterministic (SSIM 0.69 → 0.94 on identical inputs). Anything claiming to confirm/refute a hypothesis runs ≥3× on suspect (web) AND ≥2× on reference (native). Cross-run variance is itself load-bearing: native should be near-constant; web's spread vs native's constancy is the signal.

**How to apply:**
- Brief: "run N≥3 times, capture each run's output to a separate log file, aggregate in impl log."
- Log naming: `target/diagnostics/logs/<probe>-run-{1,2,3}.log`; outputs `target/diagnostics/<probe>-run-{1,2,3}.json`.
- Impl log includes "Cross-run variance" — what was constant, what varied. Variable field matches hypothesis prediction → supported; varies on unrelated field → weakened.
- Never conclude PASS/FAILED from one run on a known-flaky surface. 1/3 panics = signal, report all exits.

Related: [[feedback-e2e-gates-must-fail-fast]], [[feedback-web-runs-capture-logs]], [[subagent-gpu-app-verification-loop]].
