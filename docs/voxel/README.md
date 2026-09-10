# Unity ECS voxel-game reference

This is project-neutral working guidance distilled from the repository's
previous voxel notes. It is a reference, not a specification: choose concrete
world size, voxel resolution, meshing, rendering, networking, and native-code
boundaries for the current game before treating any pattern here as a rule.

## Start here

- [Unity ECS patterns](unity-ecs.md) covers chunk presentation, baking, and
  Burst/native-code boundaries.
- [Voxel architecture](architecture.md) separates field evaluation, edits,
  residency, meshing, and replication so each can be designed and tested
  independently.
- [GPU voxel foundations](gpu-foundations.md) is relevant only when the game
  needs GPU-resident voxel data, SDFs, or raymarching.

## Design order

1. Define the player-visible contract: edit latency, supported world scale,
   multiplayer model, visual style, and target hardware.
2. Choose the authoritative voxel representation and the persistence/edit log.
3. Build a deterministic chunk/evaluation path with unit tests.
4. Add meshing and ECS presentation, including seam and lifecycle tests.
5. Add streaming, networking, and GPU acceleration only when measurements show
   they are needed.

Keep project-specific decisions in the game's own `AGENTS.md` and design docs;
do not put them back into a global personal-memory archive.
