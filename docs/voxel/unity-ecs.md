# Unity ECS patterns for voxel chunks

## Chunk presentation

Use Entities Graphics when chunks are data-driven and numerous. A practical
pattern is one prefab/prototype entity per mesh-and-material combination, then
instantiate it for each visible chunk through an `EntityCommandBuffer`. Give
the prototype the `Prefab` tag so it is excluded from ordinary queries and is
stripped from instances.

`ICleanupComponentData` is not copied by `Instantiate`. Add cleanup data to an
instance explicitly instead of assuming `SetComponent` can replace copied data.

Keep a stable chunk key separate from the presentation entity. The key should
identify chunk coordinates and, if used, LOD; the entity is a disposable view
of that state.

## Structural changes and system lifecycle

Do not make structural changes while iterating a `SystemAPI.Query`. Collect
targets first (for example in a `NativeList<Entity>`), then create, destroy, or
alter entities after the query. Query iteration carries an implicit lock, so
even apparently unrelated structural changes can fail.

If a system must process both active chunks and cleanup work, express that
explicitly with an appropriate update requirement such as
`RequireAnyForUpdate`; otherwise cleanup can be skipped when no live chunks
remain.

## Baking and transforms

For physics-driven or otherwise world-space chunk children, declare
`TransformUsageFlags.Dynamic | TransformUsageFlags.WorldSpace` at bake time.
Trying to remove `Parent` later from a default baking system is unreliable:
transform baking may assign it after that system runs.

Validate the transform the renderer sees. Presentation checks should compare
`LocalToWorld`, not just `LocalTransform`, because a hidden parent can make a
locally correct value render at the wrong world position.

## Tests and native boundaries

Use a graphics-enabled PlayMode run for Entities Graphics coverage:
`-nographics` prevents the rendering systems from exercising their normal
path. Keep deterministic data/meshing tests in EditMode where possible, and
reserve PlayMode tests for world scheduling and presentation.

If Burst code calls native functions, test a player build. Editor Burst JIT can
accept interop signatures that desktop Burst AOT rejects, particularly structs
passed or returned by value. Keep the affected glue managed until a tested
pointer-based ABI exists for every shipping platform.
