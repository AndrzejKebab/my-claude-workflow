---
name: player-service-session-connector
description: game↔player-service seam (auth + wallet) is implemented and e2e-green; player-service is a wallet proxy; demo-mode-service owns the external REST seam
metadata: 
  node_type: memory
  type: project
  originSessionId: bf570d37-4b19-46af-a304-3d1a3d3b107c
---

The game-service ↔ player-service integration is implemented and end-to-end green (2026-07-08, branch `player-service-integration`). See `docs/player-service-integration.md`.

- **Topology**: front-end → game-service (GraphQL) → player-service (GraphQL m2m) → external Wallet API (REST `X-REQUEST-SIGN`, the "External game provider" PDF). game-service talks ONLY to player-service + front-end. The PDF's `/balance /bet /win /cancel` (decimal-string amounts, 422 `{code,message}`) is the **player-service → platform** seam, NOT game↔player. `feat/demo-mode-service` (WIP) is the mock/real platform; `WALLET_API_URL` is player-service's forwarding seam. Today player-service uses a Postgres-backed fun-mode wallet as the local mock.
- **M2M**: `libs/m2m-token` (new) — hand-rolled HS256 shared-secret (`M2M_SECRET`+`M2M_ISSUER`, node:crypto, zero deps). game-service mints `createToken`; player-service verifies in mercurius-auth. Deliberately no SuperTokens core (compose = pg/redis/kafka only). Satisfies `GraphQLM2MClient` (which decodes `exp` via fast-jwt).
- **player-service now exposes** `createGameSession(connectToken)`/`gameSession(token)` (auto-provisions player+session+starting wallet) and `createGameTransaction`(BET/WIN atomic debit/credit, funds check, idempotent by transactionId)/`playerBalance`. Added `players.balance` column. `version` public; all else requires m2m.
- **game-service two runtime tiers** by `SESSION_SOURCE`, same resolver code: `stub` = in-memory command buffer + in-memory wallet (no infra); `player-service` = `DrizzleCommandBuffer` commit to pg + real wallet. `openBet`/`instantBet`/`balance` actuated; peripheral resolvers still stubbed. neon-mirage reward=bet (1:1, net-zero settle).
- **e2e**: `apps/game-service/src/test/integration/*.integration.ts` (`pnpm --filter @gps/game-service test:integration`) — recreates `gps_game`/`gps_player` (separate DB per service — shared DB breaks `drizzle-kit push` on enum conflict), pushes both schemas via `node_modules/.bin/drizzle-kit push --force`, spawns player-service subprocess, boots game-service in-process. Needs `docker compose up -d`. Stub suite `test:e2e` needs no infra.

Bugs found + fixed this session: player-service `Tracable` subclasses used `__filename` (undefined in ESM) → `import.meta.filename`; `DrizzleCommandBuffer.commit` never exercised before, jsonb columns (winAmounts/storage) can't `JSON.stringify` bigints → encode bigints→strings at the persistence boundary; pg returns bigint columns as strings (test comparisons need `Number()`).

Still open: `common-errors` `parseApplicationError` calls `mercurius.ErrorWithProps` as a constructor — broken under ESM, so insufficient-funds surfaces as a generic 500 (abort still correct). See [[game-framework-contract-shape]] [[no-proprietary-base-references]].
