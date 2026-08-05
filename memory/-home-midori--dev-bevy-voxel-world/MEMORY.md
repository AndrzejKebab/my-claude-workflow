# Project Memory

## Orchestration Rewrite — COMPLETED (commit b343e9e)
- All 5 gates pass: unit tests, WASM, void_detection_test, lod_overlap_test, visual QA
- See `memory/orchestration_rewrite.md` for detailed fix notes
- Tests: `void_detection_test` (voids), `lod_overlap_test` (overlap), `orchestration_latency_test` + `orchestration_invariant_test` (headless)

## Pipeline Essentials
- `VoxelBasePlugin` auto-attaches per-world state to `VoxelWorldRoot` entities (PreUpdate)
- `VoxelSet` order: WorldPositionUpdate → FloatingOrigin → PipelineTick → EntitySync
- No global ChunkStore — entity sync reads `PerWorldChunkStore` directly
- Renderable set: `(leaves ∩ meshes − pending_adds) ∪ (protected ∩ meshes)`
- `is_idle()` = phase Idle + no pending meshes + transition_ledger empty
- `is_converged()` = is_idle + last refine had no transitions

## Entity Sync
- One `per_world_entity_sync::<M>` per material type, registered by `VoxelPipelinePlugin<M>`
- Unconditional: full ChunkStore→entity mirror each frame, no budgeting
- Despawns before spawns (prevents LOD overlap)
- Material routing: `PerWorldMaterial<M>` → `ChunkMaterialRes<M>` fallback (only if no `HasPerWorldMaterial`) → skip
- `UV_1.y` encodes `lod_level + hash_frac` for debug vis shaders

## Debug Visualization
- `DebugVisMaterial` = `ExtendedMaterial<StandardMaterial, DebugVisExtension>`, 3 modes (LOD/Chunk/Normal)
- Mode switch = material handle swap, no mesh rebuild
- `lod_color()` / `NUM_LOD_COLORS` for test pixel classification

## Floating Origin
- `FloatingOrigin` resource with `render_origin` DVec3, threshold 100K units
- `sync_world_position_to_transform` updates ALL entities with `WorldPosition`
- ANY camera or entity that needs correct positioning MUST have `WorldPosition` component
- Without it, entity stays at its initial Transform while all other entities shift on rebase

## Bevy 0.18 Gotchas
- Observers: `On<Insert, C>` / `On<Remove, C>` (NOT `Trigger<OnInsert, ...>`). `On` derefs to event; entity via `event.entity`
- Events: `Add`, `Insert`, `Remove`, `Replace`, `Despawn` in `bevy::ecs::lifecycle`
- Vulkan screenshots: `Bgra8UnormSrgb` (BGRA order) — check `texture_descriptor.format`

## Build
- Shared target dir: `/home/midori/_dev/sim2d-target/` (CARGO_TARGET_DIR)
- Tests: `optimized + debuginfo` profile

## Shared GPU Test Harness — COMPLETED
- `crates/voxel_game/src/test_harness.rs` — single import for all 19 GPU tests
- API: `RunMode {Auto, Interactive, Visual}`, `TestArgs::parse_required/parse_optional`, `build_default_plugins(mode, title)`, `gpu_exit(pass)`
- All 19 tests migrated: OffscreenConfig + inline `_exit` + manual arg parsing all replaced
- `WindowResolution::new(1920, 1080)` takes `u32` not `f32` (Bevy 0.18)
- Flythrough/loading_benchmark/visual_qa keep local RunMode; import only `build_default_plugins + gpu_exit`

## Test Gotchas
- GPU tests gated behind `--features gpu-tests` (required-features in Cargo.toml) — `cargo test --workspace` skips them
- `just test-gpu` runs all 15 GPU tests; see `docs/TEST_MAP.md` for per-area mapping
- `harness = false` tests need main thread (winit)
- GPU tests: don't combine in single `--test` (resource contention)
- GPU warmup: ~150 frames before Vulkan pipelines produce visible output; screenshot at frame 160+
- Flythrough: `gpu_warmup_frames: 30` to avoid first-draw shader compile spike; `ReportOnly` in debug builds
- NVIDIA Vulkan SIGSEGV on atexit → GPU tests use `_exit()` bypass (via `gpu_exit()`)
- Analysis GPU compute shader runs per Camera3d in Core3d — Camera2d uses Core2d (no analysis)

## Runtime API
- `PerWorldRuntime` fields are private — use: `is_initialized()`, `is_converged()`, `is_pipeline_idle()`, `is_ready()`, `pending_count()`, `loading_progress()`
- `WorldLoadingState` component on VoxelWorldRoot, `WorldReady` marker when ready
- `AsyncRefineTask`: fire-and-poll over rayon; `build_refine_input()` → `apply_refine_result()`
- `VoxelWorld` public debug: `phase_name()`, `mesh_pending_count()`, `known_empty_count()`

## Key Patterns
- `VoxelWorldRoot::new_with_initial_lod()` seeds octree (vs `new()` = empty)
- `SphereSampler::new(radius).with_center([x,y,z])` for test geometry
- `LogDepthMaterial` for z-fighting elimination
- `CollisionInterest::default_for(world_id)` — LOD 0–2, 256m range

## Presample Grid Alignment (noise_lod sphere void bug — fixed)
- `hierarchical_grid_base(world_origin, voxel_size, lod)` snaps `world_origin/voxel_size` to nearest multiple of `GRID_ALIGNMENT=1024`
- If `world_origin` is NOT a multiple of `1024 × voxel_size`, sample positions shift by up to 1024 voxels relative to the actual node AABB
- Bug: `noise_lod.rs` used `world_origin: DVec3::splat(-half)` (−7,000,000 = not a multiple of 1024) → 64m presample offset → LOD-0 nodes near sphere surface falsely marked `known_empty` (permanent void)
- Fix: `world_origin: DVec3::ZERO` in noise_lod's planet scene branch — ZERO is always aligned
- Rule: **`world_origin` must be a multiple of `1024 × voxel_size`** for correct presample behavior
- `void_detection_sphere_test`: radius=200_017 (not mult of 32), max_lod=13, world_bounds=±262_144, ortho at y=200_317, SlowSettle phase before SlowClose tracking

## GPU Test: SlowSettle Pattern
- When a void-detection test has a large viewer jump between FastFly→SlowClose, add a `Phase::SlowSettle` that:
  1. Holds viewer at slow_start
  2. Waits for `all_ready()` + SETTLE_IDLE_THRESHOLD consecutive idle frames
  3. Only then enters tracked SlowClose phase
- Without SlowSettle: non-deterministic black pixels from pipeline catchup contaminate void counts

## User Preferences (CRITICAL)
- NEVER claim success until ALL acceptance gate tests actually pass (including GPU tests)
- `cargo test --workspace` is necessary but NOT sufficient — GPU tests are the real gates
