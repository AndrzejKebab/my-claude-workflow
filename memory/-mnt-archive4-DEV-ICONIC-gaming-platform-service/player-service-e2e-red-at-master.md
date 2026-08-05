---
name: player-service-e2e-red-at-master
description: "player-service `test:e2e` is green as of PR #34 — six wallet-counterparty tests are parked behind documented skips, not failing"
metadata: 
  node_type: memory
  type: project
  originSessionId: 153b55e5-a968-41be-a7dd-66d9b8858b40
  modified: 2026-07-21T15:01:43.100Z
---

`pnpm --filter @gps/player-service test:e2e` **is green** since `8e4ecb3` ("Merged in
fix/player-service-e2e", PR #34, on master 2026-07-21). Expect roughly 13 tests, 11 pass, 0 fail,
2+ skipped.

Before that it was red: 13 failures, all one family — a fun-mode session open calling the
integration `/balance` and getting `invalid.session.key`, because there is no fun wallet at
`INTEGRATION_FUN_URL`. PR #34 did not fix the seam; it **parked** the six affected tests behind
`t.skip()` with the reason inline, pointing at `docs/todo/player-service-wallet-counterparty.md`.

**Why:** a run of this suite now shows a wall of skips that look like someone hiding failures. They
are not — they are a documented park with a tracked todo, which is the repo's honest form. Reading
them as rot leads to re-opening a decision that was already made deliberately.

**How to apply:** treat this suite as a real gate again — 0 fail is the bar. If the parked six ever
matter to your change (anything touching the fun wallet seam or `INTEGRATION_FUN_URL`), the todo
names the gap. Related: [[shared-postgres-cross-checkout-push]], [[keep-feature-prs-scoped]].
