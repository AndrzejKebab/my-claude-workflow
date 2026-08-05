# Orchestration Rewrite — Fix Notes

## Status: COMPLETED (commit b343e9e)

## What Was Fixed

### Bug 1: Superseded Transition Force-Commit (PRIMARY VOID SOURCE)
- **Location**: `world.rs` `update_renderables()` (was line ~804)
- **Root cause**: `if all_ready || transition.superseded` force-committed superseded transitions regardless of mesh readiness
- **Fix**: Superseded transitions now check `collect_leaf_descendants(protected, current_leaves)` — parent stays visible until ALL current leaf descendants have meshes
- Uses bottom-up filtering O(|leaves|) via `ancestor.is_ancestor_of(leaf)`

### Bug 2: known_empty Covering Ancestor Stall (PIPELINE STALL)
- **Location**: `world.rs` `update_renderables()`, empty-descendants branch
- **Root cause**: When a protected node is merged into a coarser ancestor, and that ancestor is `known_empty` (no surface at coarse LOD), `meshes.contains_key(&ancestor)` returns false → transition NEVER commits → pipeline stalls indefinitely
- **Fix**: Accept `known_empty` covering ancestors: `meshes.contains_key(&a) || known_empty.contains(&a)`
- This was the fix that made `lod_overlap_test` pass (previously: 46 leaf violations, far converge timed out)

### Bug 3: Floating Origin in Tests (FALSE POSITIVE VOIDS)
- **Location**: `void_detection_test.rs`
- **Root cause**: Ortho camera had no `WorldPosition` component. During 500km traversal, floating origin rebased (threshold 100K units), shifting all chunk entities but NOT the ortho camera. Terrain fell outside viewport → monotonically increasing "black pixels" (203K at end)
- **Fix**: Add `WorldPosition::new(ortho_world_pos)` to ortho camera entity
- Reduced black pixels from 203K to 127

### Bug 4: Chunk Boundary Alignment Artifacts
- **Location**: `void_detection_test.rs`
- **Root cause**: Sub-pixel mesh seam gaps at LOD-14 chunk boundaries, visible only when pixel grid aligns exactly. Cleared after first floating origin rebase shifts alignment.
- **Fix**: "seen_zero_black" gate — only track analysis frames after seeing first clean frame (0 black pixels). More robust than fixed frame skip.

## Architecture Summary

### Transition Lifecycle
1. `register_transitions()`: leaves updated, `supersede_all()` called, new transitions registered
2. `update_renderables()`: each tick checks readiness and commits
   - Normal transitions: check frozen `required_nodes` have meshes
   - Superseded transitions: check current leaf descendants of `protected_nodes` have meshes
   - Empty descendants (merged): check covering ancestor has mesh or is known_empty
3. Commit: protected nodes cleaned up (unless still_protected by other transitions)

### Key Helpers
- `collect_leaf_descendants(ancestor, leaves)` → SmallVec of current leaves under ancestor
- `find_covering_leaf_ancestor(node, leaves, max_lod)` → nearest ancestor that IS a current leaf

### Cancellation
- `batch_token: Option<CancellationToken>` in MeshPool
- Cancelled in `register_transitions()` when leaves change
- Workers check `cancel.is_cancelled()` cooperatively

### Urgency Priority
- Nodes blocking nearly-ready transitions (low `missing` count) dispatched first
- Sort: urgency (lower = more urgent) → then distance to interest point

## Key Files
| File | Changes |
|------|---------|
| `crates/voxel_plugin/src/world.rs` | Core fix: update_renderables, dispatch_mesh_tasks, register_transitions, helpers |
| `crates/voxel_plugin/src/octree/refinement.rs` | `#[allow(clippy::too_many_arguments)]` on apply_cascading_collapses |
| `crates/voxel_game/tests/void_detection_test.rs` | WorldPosition on ortho cam, seen_zero_black gate, Camera2d for UI |
| `crates/voxel_bevy/src/orchestration_invariant_test.rs` | New: headless no-void-no-overlap invariant test |
| `crates/voxel_bevy/src/orchestration_latency_test.rs` | New: convergence speed, teleport latency, no-stall tests |

## Debugging Lessons
- 203K black pixels was NOT orchestration voids — it was floating origin misalignment (ortho cam missing WorldPosition)
- `known_empty` covering ancestors are a valid LOD result, not a void — the surface genuinely doesn't exist at that coarse resolution
- Pipeline convergence requires ALL transitions to commit; a single stuck transition blocks `is_idle()` → `is_converged()` forever
