---
name: decouple-is-catalog-build
description: "`decoupleClientOnSlot(loadClientOnSlotLedger())` is the catalog build, not a cheap shortcut — any test that scans all triples must use the integration suite."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b4e5b436-1461-4c83-a172-00b8174ba7a2
---

In client-api, do NOT treat `decoupleClientOnSlot(loadClientOnSlotLedger())` as a fast "in-process replacement" for the DB-backed catalog when iterating over more than a handful of (client, slot, currency) triples. That call IS the catalog build (it's what `reconcile.ts` and `seed-sqlite.ts` use to populate Postgres / SQLite) and it is slow — multiple minutes of single-threaded CPU just to walk every pair.

**Why:** It eagerly slot-by-slot deep-merges all commits × clients × currencies, producing tens of thousands of `IClientOnSlot` rows. Cheap for one specific triple (filter inputs first), bottleneck-grade for full scans.

**How to apply:**
- Targeted lookup of one or a few (client, slot, currency) triples: fine in a unit test if you pre-filter the ledger to only commits referencing the target slot/client, OR mock `slots.barrel` + `clients.barrel` to expose only the targets (pattern from `decoupleClientOnSlot-unit.spec.ts`).
- Full-catalogue sweeps (sanity checks, audits, "fail CI if any config is bad"): live in `pnpm test:integration`, not `pnpm test:unit`. The integration suite auto-seeds the DB and gives you a wired-up `app.slotCatalogView` via `src/test/fixtures/catalog-loader.ts` and `appTestSetup.ts`; the live view is much faster than rebuilding the catalog per process because Prisma backs it with already-collapsed rows.
- The Prisma row shape (one row per (client, slot) with `settings` + `currencySettings` map) is precisely the collapsed form `decoupleClientOnSlot` produces, then loses to ad-hoc grouping in JS — letting the DB hold the collapsed form is what makes the runtime fast.
