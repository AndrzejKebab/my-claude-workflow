---
name: feedback-e2e-gates-must-fail-fast
description: e2e gates in bevy-naadf must have wall-clock budgets + fail-fast diagnostics; a hung gate is worse than one that fails
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e4081ed2-be75-401d-a246-bb2dcded1571
---

e2e gates in `crates/bevy_naadf/src/e2e/` must always have wall-clock budgets (or hard frame caps with per-cap diagnostic output) on any "wait for state X" loop. Hanging pollutes the verification surface and forces external `timeout` wraps everywhere.

**Why:** streaming-world Phase 2.5 — user invoked `cargo run --bin e2e_render -- --streaming-window` and it hung indefinitely (likely on Resident-state poll with no budget). User: *"this stupid test just hangs and does nothing."* Agent had reported it green at exit 0; pass was non-deterministic / cache-warm only.

**How to apply:**
1. Every `while !condition { sleep / yield }` loop gets `Instant::now()` + `Duration::from_secs(N)`; N ≤ ~60s total.
2. On budget exhaustion, print a diagnostic: which slots/buffers/frame counter still waiting.
3. Briefs explicitly require "every wait loop has wall-clock budget + bail-with-diagnostic".
4. From dispatched agents: wrap `cargo run` in `timeout 120s`.
5. Trust budget for "agent reported green" is bounded — re-run on cold cache may not reproduce, especially streaming/residency gates.

Related: [[subagent-gpu-app-verification-loop]].
