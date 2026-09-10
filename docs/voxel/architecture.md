# Voxel architecture decisions

## Separate the layers

Model the game as independently testable layers:

1. **Base field** — deterministic terrain from a seed and generation graph.
2. **Edits** — additive/subtractive stamps, brushes, or operations applied to
   the base field.
3. **Residency** — which chunks/bricks are currently cached or streamed.
4. **Meshing** — the derived mesh for a chunk and its LOD boundaries.
5. **Presentation** — ECS entities, materials, and renderer registration.
6. **Replication** — the compact data needed for another client to reproduce
   the same field and edits.

This avoids treating a visible chunk entity as the source of truth. Entities
can be created and destroyed freely; the field and edit history cannot.

## Editing and networking

Represent an editable brush as game-side data that produces one or more core
stamps/operations. A large brush may affect many chunks, so its identity and
the affected operations should be distinct. For multiplayer, replicate the
smallest authoritative edit representation and use region snapshots/baselines
only as recovery or catch-up data.

Choose edit latency, conflict rules, persistence, and bandwidth limits before
choosing an implementation. A 60 Hz digging target is a requirement to prove
with profiling, not an inherited default.

## LOD and seams

LOD work needs explicit invariants and tests. At minimum, verify that adjacent
chunks have no holes, duplicate surfaces, or long-lived overlap while their
LODs change. Treat a mesh as ready only after its data and its boundary
dependencies are ready; despawn obsolete presentation before showing its
replacement if overlap is visually harmful.

Surfacenets, marching cubes, dual contouring, and block meshing have different
seam and material tradeoffs. Pick one based on the game's terrain style and
editing needs, then build a focused seam harness before optimizing it.

## Streaming

Clipmaps and brick caches are useful patterns for large worlds, but they are
not prerequisites. Introduce them after measuring chunk generation, meshing,
memory, and travel latency. Keep cache eviction separate from persistence so a
resident chunk can disappear without losing edits.
