---
name: shared-postgres-cross-checkout-push
description: "running another checkout's suite against the shared dev postgres drops your branch's columns — re-run `pnpm db:push` before believing an integration failure"
metadata: 
  node_type: memory
  type: project
  originSessionId: 153b55e5-a968-41be-a7dd-66d9b8858b40
  modified: 2026-07-21T14:07:33.535Z
---

The docker infra (`gaming-service-postgres-1`, compose project `gaming-service`) is **one database
for every worktree** — the compose file hard-names the project, so a second checkout does not get
its own. Booting another checkout's player-service (e.g. running master's `test:e2e` to compare a
failure set) syncs *that* checkout's schema over the shared `gps_player`, and a column your branch
added is **dropped**.

Observed 2026-07-21 on `feat/dynamic-bet-ladder`: game-service integration went 237 pass → 8 pass /
187 fail between two runs of an unchanged branch. Every failure was one insert into
`player_sessions` naming `min_bet`/`max_bet`/`default_bet`, which no longer existed. `pnpm db:push`
from the branch's own worktree restored all 237.

**Why:** the failure surfaces as a wall of unrelated-looking assertion errors (auth, paging, wallet,
error-contract), so it reads as "my change broke everything" rather than "my columns are gone" — and
the honest-looking conclusion is the wrong one.

**How to apply:** before diagnosing a mass integration failure, check the live schema
(`docker exec gaming-service-postgres-1 psql -U postgres -d gps_player -c '\d <table>'`) and re-run
`pnpm db:push` from this worktree. Better, don't boot another checkout's service against the shared
infra at all — use `pnpm stack:docker up` for a per-worktree container block. Related:
[[player-service-e2e-red-at-master]].
