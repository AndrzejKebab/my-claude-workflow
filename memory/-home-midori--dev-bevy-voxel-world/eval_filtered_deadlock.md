# eval_filtered Collapse Deadlock (fixed)

## The Bug
Commit `c13390b` introduced `eval_filtered()` (Nyquist-aware octave filtering) in `sample_volume()`/`eval_volume()` but left `eval()` (unfiltered) in `sample_single()`, `analytic_sdf_range()`, `sdf_range()`, `eval_positions()`.

## Why It Causes Overlap

At coarse LODs, `eval_filtered()` suppresses high-frequency noise octaves → smoother/flatter surface. For the heightfield sampler (SCALE=8000, 6 octaves), at LOD 6+ ALL octaves are filtered out → surface goes flat at y=0. But `sample_single()` still returns the full-detail surface with ±1500m hills.

### The deadlock chain:
1. Fine children have meshes (at their LOD, filtering preserves enough octaves)
2. Refinement says "collapse" → transition: required=[parent], protected=[children]
3. Parent meshed via `sample_volume()/eval_filtered()` → heavy filtering → surface absent from chunk → empty mesh → `known_empty`
4. **Void-prevention** (`world.rs:998-1003`): if `known_empty` parent `is_ancestor_of` any child with a real mesh → transition BLOCKED
5. Children stay visible as protected nodes forever → multiple LOD levels overlap → tree never collapses

## Void-Prevention Logic (world.rs:995-1007)
```rust
transition.required_nodes.iter().all(|n| {
  if meshes.contains_key(n) { true }
  else if known_empty.contains(n) {
    // Block if this empty node would replace a visible protected node
    !transition.protected_nodes.iter()
      .any(|p| n.is_ancestor_of(p) && meshes.contains_key(p))
  } else { false }
})
```
This correctly prevents voids (don't remove visible children if parent has nothing to show). But when filtering makes the parent artificially empty, it becomes a permanent deadlock.

## Rule
**All SDF evaluation paths must agree on where the surface is.** If `sample_volume()` uses filtering, then `sample_single()`, `analytic_sdf_range()`, `sdf_range()`, and `eval_positions()` must use the same filtering. Otherwise the pipeline's view of reality is inconsistent and the void-prevention logic deadlocks.

## Fix
Reverted `eval_filtered` → `eval` in all 5 production call sites. The `eval_filtered`/`full_amp_sum`/`octave_weight` code remains available for future use if a consistent filtering strategy is designed (all paths must filter identically).
