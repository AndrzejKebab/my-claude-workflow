---
name: Shapes are immutable declarative data
description: Never mutate SpatialShape fields (e.g. shape.center += pos) — pass world position as a separate parameter
type: feedback
---

Never mutate `SpatialShape` struct fields like `shape.sphere.center += pos`. Shapes are declarative, immutable data.

There is no concept of external/internal position. Two categories:
- **Query** = just a shape (its `.center` IS the world position)
- **Agent** = shape × matrix → construct a NEW world-space shape via factory (`SpatialShape.Sphere(radiusSq, pos + localCenter)`), never mutate the source

**Why:** `shape.center += pos` mutates declarative data — it conflates local geometry with world transform and looks like clueless code.

**How to apply:** Extensions (`ComputeWorldAABB`, `Overlaps`) take shapes only, no `worldPos` params. When building KDTree entries from agents, construct fresh world-space shapes using factory methods. Never touch the agent component's shape.
