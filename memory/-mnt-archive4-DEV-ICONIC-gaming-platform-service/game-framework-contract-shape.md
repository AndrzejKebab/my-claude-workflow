---
name: game-framework-contract-shape
description: How games plug into the game-service framework — the manifest contract + multi-game rule
metadata: 
  node_type: memory
  type: project
  originSessionId: 41c63f81-da93-4526-a80b-78a7f65f59f9
---

`apps/game-service` will host **dozens of games**. Architecture invariants the user pinned down (do not
regress toward a single-game shape):

- **Auto-discovery is retained.** `app/graphql/storage/discovery.ts` globs every `games/*/manifest.ts` and
  aggregates them. Never rework this into an explicit single list or a single-game manifest.
- **The game↔framework seam is `games/<g>/manifest.ts`** exporting a single decoupled `GameManifest` const:
  `{ id, name, game: GameConstructor, storage: Partial<Record<StorageKind, z.ZodObject>> }`. It's a *game*
  manifest (carries the class + storage schemas), not a storage-only manifest.
- **The game is a class** (`games/<g>/game.ts`) implementing framework feature hooks (`placeBet`, …). It
  **uses its own storage types internally** (via `z.infer` of its `storage.ts` schemas) to build the typed
  component tree `Wager → BetChain → Bet → Outcome → Reward`. That internal use is what tightens the types.
- **Rejected shapes:** a `static storage` field on the game class (too coupled); `defineGame()` that
  *consumes/produces* the game types (backwards — types originate in the game's `storage.ts` and flow out).
- Storage schemas are published to GraphQL storage unions; member names derive by convention
  `pascal(id)+Kind+"Storage"`. Money stays `bigint` end-to-end (no number↔bigint boundary).

**Why:** the user iterated hard on this contract; getting it wrong wastes rounds. **How to apply:** when
touching game registration / storage routing, keep the manifest-glob-discovery shape and the class-uses-its-
own-types principle. See [[no-proprietary-base-references]].
