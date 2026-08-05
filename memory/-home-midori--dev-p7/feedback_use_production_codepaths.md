---
name: use-production-codepaths
description: "When writing tests or tools that evaluate live config, run them through the production code path (real view/service layer) instead of reimplementing the math; shrinks regression surface."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b4e5b436-1461-4c83-a172-00b8174ba7a2
---

For tests and sanity-check tools that need to "evaluate what production would produce" (e.g. validating slot/currency configs, replaying pricing math), prefer wiring through the actual view/service layer with an in-memory fake of the slow boundary (DB, network) over reimplementing the transformation chain locally.

**Why:** Each reimplementation step is a place where the test and prod can drift silently. If `RepositorySlotCatalogView.calculateRealBetCoinAmounts` ever changes (e.g. coinFraction semantics, multiplier resolution order), a hand-rolled test pipeline will keep passing while serving stale answers. Going through the real view forces co-evolution.

**How to apply:**
- Identify the boundary that's actually slow/external (Prisma, Redis, HTTP). Build the smallest possible in-memory implementation of that boundary's interface.
- Bootstrap the real view/service on top of it.
- The test code should only iterate inputs and assert outputs — no replay of internal math.
- Common pattern in p7: implement `ISlotCatalogRepository` against `loadClientOnSlotLedger() + decoupleClientOnSlot()` and feed `RepositorySlotCatalogView`. Reuses `applyOverrideBuffer`, `applyCurrencyMultipliersToCoinValues`, `recalculateQuickBetCoinAmounts`, `calculateRealBetCoinAmounts` as-is.
- Acceptable to add a tiny structural adapter (e.g. collapse per-currency ledger rows into Prisma-row-shape with `currencySettings` map) — that's still "shaping the boundary," not reimplementing the transformation chain.
