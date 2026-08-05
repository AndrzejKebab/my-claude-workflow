---
name: feedback-e2e-must-drive-actual-main
description: "e2e harness must drive the actual main binary, not duplicate its install/launch path; otherwise CLI flags drift between e2e and interactive launch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e4081ed2-be75-401d-a246-bb2dcded1571
---

E2E gates must drive the **same code path** the user runs interactively. Shape:

```
fn main_e2e() {
    begin_running_actual_main();   // start real App with real args
    control_actual_main();         // observe / manipulate from outside
}
```

If `bin/e2e_render.rs` has its own short-circuit dispatch ladder installing presets internally and bypassing `AppArgs`/`setup_test_grid`, that's not e2e — it's a parallel reality. The user later types the same flags into the main binary and nothing happens.

**Why:** streaming-world session — interactive launch blocked because `e2e_render.rs` had its own arg parsing + per-gate install path, while `bevy-naadf.rs` only parsed default-scene args. User: *"obviously e2e path is once again not e2e ... if its shape is not like that - rewrite it to hell."* Second occurrence of this class.

**How to apply:**
1. Brief requires gate to launch via shared `AppArgs`/clap parser. Gate adds its own flag, but it composes with the regular CLI; gate ATTACHES observers/controllers, not constructs a parallel App.
2. Every new CLI flag goes on shared `AppArgs`, parsed once.
3. New `GridPreset` variants get clap-derived selection (`#[derive(ValueEnum)]` / struct-variant) — works interactively without per-binary wiring.
4. When agent claims gate works: push back — does same invocation work for `cargo run --release --bin bevy-naadf -- ...`? If no, e2e is fake.

Related: [[feedback-e2e-gates-must-fail-fast]].
