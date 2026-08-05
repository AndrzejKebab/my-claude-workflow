---
name: feedback-vigilance-preamble-for-cg-work
description: "Bevy-naadf agent briefs open with vigilance preamble flagging CG-work; circumvents Opus 4.7's adaptive-thinking failure (sloppy source claims on hard CG/GPU tasks)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b6b284c-a4b9-4e10-80eb-a670749962ae
---

Claude Opus 4.7 exhibits "adaptive thinking" failure on hard CG/GPU problems — plausible-looking but incorrect source claims (wrong line numbers, missed cfg branches, missed clamps), then proceeds as if sound.

**Incident:** `delegate-architect` for wasm-chunk-aadf-nondeterminism returned two verified-wrong claims:
- "`config.rs:227` pins `max_group_bound_dispatch: 32768` for all targets" — wrong; wasm clamp at `config.rs:219` IS applied via `From<&AppArgs>` at `config.rs:234-243`.
- "`bounds_calc.rs` is 417 lines with no wasm cfg" — wrong; 593 lines, `#[cfg(target_arch = "wasm32")]` at 452 and 539, per-round `queue.submit(...)` at 504 (the proposed "Step 11" was already in the code).

Core design (Shape B: `array<atomic<u32>>` cross-pass on web) was sound, supporting source analysis was sloppy.

**Workaround — every brief opens with the vigilance preamble:**

> "This is a significant task in the domain of computer graphics — be vigilant. Verify every file:line reference with Read or Grep before citing. Re-read suspect cfg gates and conversion impls before stating what they do. The orchestrator will cross-check any source claim."

**How to apply:**
- Every brief — diagnose-first, architect, impl, reviewer — opens with the preamble.
- Brief instructs: verify every file:line with Read/Grep BEFORE citing.
- Brief says orchestrator will cross-check; divergence is a redirect signal.

Related: [[feedback-subagent-research-only-compliance]], [[feedback-web-runs-capture-logs]], [[feedback-multiple-runs-rule-out-false-positives]].
