---
name: verify-real-functionality
description: "Before claiming done or recommending a fix, run the actual thing and the FULL suite — not a proxy path or a subset"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 39ad7cf0-fb87-4e7a-b259-0ee6550e3537
---

Two misses in one session, both from partial verification:

1. Shipped a `spawn is not defined` bug in `launch:fun-local:proxy` because every test used `--print`, which skips the browser-`open()` path. The default path (open a browser) was never exercised until the user ran it.
2. Recommended the wrong fix direction for a wallet-gameId regression after running only the openBet **subset** (`demo-launch-balance.integration.ts`, 6/6 green). The FULL game-service suite showed the fix broke the direct-wallet-read tests — the opposite direction was correct.

**Why:** `--print`/`--json` and single-file test runs are convenient but they are not the user-facing path or the full contract. "It passed" on a proxy or a subset is not "it works."

**How to apply:** Run the real command end to end (the default flags a human uses, drive the actual flow), and run the whole owning suite (`pnpm stack:docker test`, not one `*.integration.ts`) before saying done or recommending a fix. The user asked, pointedly, to "verify basic functionality." See [[keep-feature-prs-scoped]].
