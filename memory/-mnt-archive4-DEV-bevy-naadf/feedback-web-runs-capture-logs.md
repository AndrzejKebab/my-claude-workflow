---
name: feedback-web-runs-capture-logs
description: "Playwright/web-test agents MUST capture stdout/stderr AND browser-console to disk BEFORE retrying; never loop guessing without reading logs"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b6b284c-a4b9-4e10-80eb-a670749962ae
---

Any `npx playwright test ...` / `just test-wasm*` / `just diag-web` MUST:

1. Tee Playwright stdout + stderr to `target/diagnostics/playwright-<spec>-run-<N>.log`.
2. Capture every `page.on('console')` line to same/sibling file — browser-console panics (`panicked at .../sys/time/unsupported.rs:35:9: time not implemented on this platform`) ONLY appear in the console stream, NOT in Playwright stdout.
3. BEFORE any retry, grep captured logs for `panicked|error|FATAL|DeviceLost|Uncaught` and report matches. If matches, STOP and surface — do NOT silently retry.

**Why:** prior dispatch looped re-launching the web test without reading captured logs. Logs had a `std::time::Instant` panic from `async_vox.rs` (wasm can't impl `std::time::Instant`). Each retry was wasted tokens until user manually checked.

**How to apply:**
- Brief touching Playwright: "Tee stdout+stderr to `target/diagnostics/playwright-<spec>-run-<N>.log`. Capture browser-console via `page.on('console')` to the same file. Before any retry, grep for panic/error markers and report."
- Bevy-on-wasm: ALL time/instant code paths MUST use `web_time::Instant`, never `std::time::Instant`. Repo has `just lint-wasm-compat` (`scripts/lint/wasm-compat.sh`) — run before any wasm build.

Related: [[feedback-playwright-channel-google-chrome-stable]].
