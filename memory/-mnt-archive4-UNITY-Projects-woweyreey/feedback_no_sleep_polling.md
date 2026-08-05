---
name: Never sleep-poll for test results
description: Run tests in foreground, never use sleep+cat to poll background tasks
type: feedback
---

Never use `sleep N && cat output` to poll for background task results. This is unreliable and wastes time.

**Why:** Background tasks notify when complete — no polling needed. And test runs should be foreground anyway since we need the result before proceeding.

**How to apply:**
- Run tests in foreground: `scripts/run-tests.sh EditMode "UnityJS"` — tokf filters the output cleanly
- If running EditMode+PlayMode sequentially, chain with `&&`: `scripts/run-tests.sh EditMode "X" && scripts/run-tests.sh PlayMode "X"`
- Only use `run_in_background` when genuinely doing other work in parallel
- Never prefix commands with `sleep`
