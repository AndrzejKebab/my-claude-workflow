# GPU voxel foundations

Use this path only when CPU meshing and regular chunk streaming do not meet the
game's measured needs. Build the primitives in isolation before integrating
them into terrain, fog, or gameplay systems.

## Recommended order

1. Sampling and storage helpers with a documented world-to-voxel coordinate
   convention.
2. Tile/brick addressing and residency, including allocation and eviction.
3. SDF sampling and sphere tracing, with clear inside/outside transition rules.
4. A distance-field builder if dynamic SDF generation is required.
5. A generic raymarch loop whose density, lighting, and output are supplied by
   the caller.
6. Unit, integration, and image-based regression tests at every layer.

## One authoritative field

When several render paths need the same density or shape, sample one
authoritative voxel field rather than deriving each path from a different
intermediate texture. Different resolutions are fine; different sources create
visible disagreement at sharp boundaries.

An SDF can skip empty space during a raymarch, but it is not a replacement for
the voxel field. Keep signed distance, density/material attributes, and
lighting inputs conceptually separate so each has a clear owner and update
path.

## Verification

Test coordinate alignment at chunk and LOD boundaries. A grid-origin mismatch
can classify valid terrain as empty and create persistent voids that look like
meshing failures. Include deliberately awkward origins, non-power-of-two
feature sizes, chunk borders, teleports, and rapid edit sequences in the test
set.
