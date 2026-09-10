# Command buffers, singletons, and the chunk-pool-on-a-singleton pattern

Engine `file:line` citations refer to the installed `com.unity.entities` package under `Library/PackageCache/com.unity.entities@<version>/Unity.Entities/`. Verify line numbers against the version used by the current project.

## `EntityCommandBuffer`

An `EntityCommandBuffer` (ECB) records structural changes — create/destroy an entity, add/remove a component, set a buffer — to be played back later at a single sync point, rather than applied immediately. It exists because a structural change mid-iteration invalidates the chunk layout a query is walking; recording into an ECB and playing it back after the loop is the safe form. The type is `[BurstCompile] public unsafe partial struct EntityCommandBuffer : IDisposable` (`EntityCommandBuffer.cs:85-86`) — itself Burst-compiled, so recording into one is legal inside a `[BurstCompile] OnUpdate` and inside a Burst job.

The main recording surface:

- Construct: `public EntityCommandBuffer(AllocatorManager.AllocatorHandle allocator)` (`EntityCommandBuffer.cs:172`); also `(Allocator label, PlaybackPolicy)` (`:182`). A short-lived ECB drained the same frame is built with `Allocator.Temp`.
- `public Entity CreateEntity()` (`EntityCommandBuffer.cs:380`) and `CreateEntity(EntityArchetype archetype)` (`:369`).
- `public void AddComponent<T>(Entity e, T component) where T : unmanaged, IComponentData` (`EntityCommandBuffer.cs:547`); the zero-value overload `AddComponent<T>(Entity e)` (`:582`).
- `public DynamicBuffer<T> AddBuffer<T>(Entity e)` (`EntityCommandBuffer.cs:486`) and `SetBuffer<T>` (`:508`).
- `public void Playback(EntityManager mgr)` (`EntityCommandBufferPlayback.cs:42`) — apply the recorded commands, then `Dispose()`.

The canonical inline-ECB pattern constructs `new EntityCommandBuffer(Allocator.Temp)`, records commands such as `ecb.AddComponent(entity, new PhysicsBody { … })` during a query loop, then calls `ecb.Playback(state.EntityManager); ecb.Dispose()` at the end of `OnUpdate`. Recording during the loop and playing back afterward lets the loop add components to entities it is iterating without invalidating the iterator.

When the structural change must be applied from a *static* loop or deferred to a standard frame point rather than played back inline, obtain the ECB from a standard ECB-system singleton instead (next section).

## `EntityCommandBuffer.ParallelWriter`

When the structural changes are recorded from inside a *parallel* job (one `Execute` per entity across worker threads), each thread needs a writer that does not race the others. `AsParallelWriter()` (`EntityCommandBufferParallelWriter.cs:15`) returns the `ParallelWriter` nested struct (`:53`). Every `ParallelWriter` command takes a leading `int sortKey` that the others do not — `public void AddComponent<T>(int sortKey, Entity e, T component)` (`EntityCommandBufferParallelWriter.cs:230`), `CreateEntity(int sortKey)` (`:107`), and so on. The sort key makes playback deterministic regardless of which thread recorded which command; the conventional key is the `unfilteredChunkIndex` an `IJobChunk.Execute` receives (or the `[ChunkIndexInQuery]` an `IJobEntity.Execute` can take). Pass the parallel writer into the job by value as a field; do not hold the ECB itself across threads.

## Obtaining an ECB from a standard ECB-system singleton

The standard begin/end `EntityCommandBufferSystem`s (placed `OrderFirst`/`OrderLast` in each group — see [`system-groups.md`](system-groups.md)) play back ECBs at fixed frame points. A system gets an ECB whose playback those systems own through the ECB system's nested `Singleton` component:

```csharp
var ecb = SystemAPI
    .GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>()
    .CreateCommandBuffer(state.WorldUnmanaged);
```

The `Singleton` is `public unsafe struct Singleton : IComponentData, IECBSingleton` (`DefaultWorld.cs:23`), and its `public EntityCommandBuffer CreateCommandBuffer(WorldUnmanaged world)` (`DefaultWorld.cs:35`) returns an ECB already registered with the parent system's pending list — no manual `Playback`, no `Dispose`; the `End…`/`Begin…` system flushes it at its own update. This is the Burst-legal path (the singleton read is source-generated, `CreateCommandBuffer` takes the Burst-callable `WorldUnmanaged` from `state.WorldUnmanaged`, `SystemState.cs:233`). Pick the `Begin…` variant to apply early in the group update, or the `End…` variant to apply at the end of the group update.

Choosing between the two ECB forms: an inline `new EntityCommandBuffer(Allocator.Temp)` + `Playback` makes the changes visible *within the same `OnUpdate`*, immediately after playback (what `PhysicsWorld2DSystem` needs — its new bodies must be live for the next step). The singleton ECB defers playback to the standard sync point and is the right form when the system is Burst, schedules its recording into a parallel job, or simply wants the changes batched at the frame's structural-change boundary.

## Structural-change patterns

- **From a non-job `OnUpdate` loop** — record into an inline `Allocator.Temp` ECB during the loop, then `Playback` + `Dispose` afterward.
- **Collect-then-apply without an ECB** — gather the affected entities into a `NativeList<Entity>` during the query loop, then apply the structural change in a second loop after the iterator is done. For a *whole-query* structural change, use an `EntityManager` overload that takes an `EntityQuery` directly.
- **From a parallel job** — `ecb.AsParallelWriter()` with `sortKey` per command.

## Singletons

A singleton is a component (or buffer) with exactly one instance in the world; it is the canonical home for per-world shared state and the channel between systems that do not share a job dependency. The access surface, all source-generated `SystemAPI` members usable inside Burst (see [`systems.md`](systems.md) for the full table):

- `SystemAPI.GetSingleton<T>()` (`SystemAPI.cs:558`) — read by value; throws if not exactly one.
- `SystemAPI.TryGetSingleton<T>(out T)` (`SystemAPI.cs:569`) — read if present; **throws on more than one**, so duplicate configuration entities fail loudly rather than being selected arbitrarily.
- `SystemAPI.SetSingleton<T>(T)` (`SystemAPI.cs:608`) — write the value back.
- `SystemAPI.GetSingletonEntity<T>()` (`SystemAPI.cs:619`) — the entity carrying it.
- `SystemAPI.GetSingletonBuffer<T>(bool isReadOnly = false)` (`SystemAPI.cs:642`) — a singleton `DynamicBuffer`.

Creating a singleton is a structural change, done through `EntityManager`: `public Entity CreateSingleton<T>(FixedString64Bytes name = default) where T : unmanaged, IComponentData` (`EntityManager.cs:1762`), with a value-taking overload (`:1781`) and `CreateSingletonBuffer<T>` (`:1797`). A system can create its world singleton lazily, attach per-frame event buffers to the same entity, and use the read-modify-write cycle: read with `GetSingleton`/`TryGetSingleton`, mutate the struct, then `SetSingleton` it back.

## Holding a native-collection-bearing struct on a singleton — the chunk-pool pattern

This is the pattern the pixelworld engine needs and the one a system author most often gets wrong. A Burst `ISystem` cannot reach a managed object, and per-system fields are private to one system — so when several Burst systems must share one large native data structure (a chunk pool, the cell grid, a residency table), that structure lives **on a singleton component as a value type whose fields are native containers**. The component is blittable and unmanaged (it holds `NativeArray`/`NativeList`/`NativeHashMap`/`UnsafeList` handles, which are themselves blittable handles into native memory, not managed objects), so it is a legal `IComponentData`; any Burst system reaches it through `SystemAPI.GetSingleton<T>()`.

The shape:

- Define `struct WorldChunkPool : IComponentData` whose fields are native containers — e.g. an `UnsafeList<Chunk>` of pooled chunks and a `NativeHashMap<int2, int>` from chunk coordinate to pool slot.
- One owning system allocates the containers (`Allocator.Persistent`) and publishes the struct with `CreateSingleton` in `OnCreate`, and disposes every container in `OnDestroy`. The singleton is the sole owner of the allocation's lifetime.
- Consumer Burst systems read it with `SystemAPI.GetSingleton<WorldChunkPool>()` and operate on its native containers directly — inside their `[BurstCompile] OnUpdate` or inside jobs the pool's containers are passed into as fields. A consumer that *grows* the pool writes the mutated struct back with `SetSingleton` (the container handles are value-copied, so a structural mutation of the containers themselves is visible without `SetSingleton`, but a reassignment of a field — a reallocation — needs the write-back).

A physics integration can use the same native-handle-on-a-singleton form at smaller scale: a world singleton carries an unmanaged physics-world handle, while `DynamicBuffer<…>` event streams live on the same singleton entity and are refilled each step. A voxel chunk pool is this pattern with native containers in place of the handle: the singleton is the seam that lets a fully Burst-compiled system graph share one allocation without a managed owner.

Two lifetime rules this pattern lives or dies by: the native containers must be allocated `Allocator.Persistent` (they outlive any single frame), and the owning system's `OnDestroy` must dispose every one of them, or world teardown leaks.

## Blob assets

A blob asset is immutable, unmanaged, relocatable read-only data referenced from components by a `BlobAssetReference<T>` — `public unsafe struct BlobAssetReference<T> : IDisposable` (`Blobs.cs:420`) — and built at bake time (or once at runtime) with a `BlobBuilder` (`BlobBuilder.cs:104`), which lays out `BlobArray<T>`/`BlobString`/nested structs in one contiguous allocation. The reference is blittable, so a component holding one is Burst-legal and a job reads through `blobRef.Value` with no managed access. Use a blob for large per-archetype data that is identical across many entities and never mutated after construction (collision outlines, material tables, or a baked palette); for per-entity mutable shared state use the singleton-with-native-containers pattern above, not a blob.
