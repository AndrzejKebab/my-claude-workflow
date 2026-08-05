---
name: e2e-only-with-published-fixtures
description: "In p7 client-api, prefer GraphQL-API e2e tests using real published client+slot configs over unit tests that synthesize IClientOnSlot/coinValueSettings."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9a66a85-19ed-4627-8340-ac72a41766bf
---

Unit tests that hand-roll an `IClientOnSlot` or call `applyCurrencyMultipliersToCoinValues` with synthetic `coinValueSettings` are not useful for validating currency/bet behavior — they bypass the catalog build (`decoupleClientOnSlot`/DB reconciliation), the resolver chain, and the GraphQL boundary. They can pass while production is broken because the synthetic inputs don't match what the real config produces.

**Do:** Write tests that look like `src/test/integration/realbet-bif-graphql-e2e.spec.ts`:
- Import real published clients from `src/slot-catalog/public/clients/` (e.g. `Hub88B2BEU`, `demoCasinoAdapter`).
- Import real slot definitions from `src/slot-catalog/public/slots/` (e.g. `P7_028S_MAVIAN_WREATH`).
- Boot the test app, get a real GraphQL `SlotCatalog` client (`@phoenix7dev/slot-catalog` package), call `batchGetClientSlotSettings` / equivalent.
- Assert hard-coded literals against the response.

**Don't:** Synthesize `IClientOnSlot` with `CASH_HACK_COMMIT.clientOnSlotCommit[0]!.partialSettings.settings` and feed it through `applyCurrencyMultipliersToCoinValues` directly. That's what `bif-bet-range-cash-hack.spec.ts` does — it passes while the real (Hub88 + V3 BIF) pipeline is broken.

**Why:** The bug surface lives in the interaction between published client config (`clientSettings.coinCurrencyMultipliers`), published slot config (`coinValueSettings`, `backendVersion`), the catalog build, and the runtime selector. Each unit-level reimplementation is a place where the test and prod can drift. The integration suite already auto-seeds the DB and gives a wired-up `app.slotCatalogView` — use it.

**How to apply:** New currency/bet/limit tests → put under `src/test/integration/<name>-graphql-e2e.spec.ts`, use the `SlotCatalog` client over HTTP against the booted app, hard-code expected outputs from a real (client, slot, currency) triple. Skip the unit-style version unless you're testing a pure function with no config dependency.

Related: [[use-production-codepaths]], [[decouple-is-catalog-build]].
