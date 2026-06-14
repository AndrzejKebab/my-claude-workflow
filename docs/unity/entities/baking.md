# Baking — `IBaker` and component types

The authoring-side conversion pipeline: GameObjects + MonoBehaviours → entities + components.

## `Baker<TAuthoring>` — the standard pattern

```csharp
// Authoring-side MonoBehaviour, drag onto a sub-scene GameObject.
public class EnemyAuthoring : MonoBehaviour {
    public float Health = 100f;
    public GameObject ProjectilePrefab;
}

// Baker — runs in the editor during sub-scene baking. Not a MonoBehaviour.
public class EnemyBaker : Baker<EnemyAuthoring> {
    public override void Bake(EnemyAuthoring authoring) {
        var entity = GetEntity(TransformUsageFlags.Dynamic);
        AddComponent(entity, new HealthComponent { Value = authoring.Health });
        var projectileEntity = GetEntity(authoring.ProjectilePrefab, TransformUsageFlags.Dynamic);
        AddComponent(entity, new ProjectileSpawnerComponent { Prefab = projectileEntity });
    }
}
```

Cited at `Unity.Entities.Hybrid/Baking/Baker.cs:18–250`.

`Baker<T>` is generic over the authoring component type. Override `Bake(T authoring)` and use the inherited helpers:

| Method                                     | Purpose                                                            |
|--------------------------------------------|--------------------------------------------------------------------|
| `GetEntity(TransformUsageFlags flags)`     | The entity for the GameObject this baker is running on.            |
| `GetEntity(GameObject obj, flags)`         | The entity for a referenced GameObject (e.g. a prefab field).      |
| `AddComponent<T>(Entity, T)`               | Add a component to the entity.                                     |
| `AddBuffer<T>(Entity)` → `DynamicBuffer<T>` | Add an empty `IBufferElementData` buffer.                         |
| `SetComponentEnabled<T>(Entity, bool)`     | Toggle an `IEnableableComponent`.                                  |
| `DependsOn(Component c)` / `DependsOn(GameObject g)` / `DependsOn<T>(T asset)` | Record a dependency for incremental baking. |
| `GetComponent<T>()` / `GetComponents<T>()` | Read another component on the same GameObject (records dependency). |
| `GetComponentInParent<T>()` / `GetComponentInChildren<T>()` | Hierarchy walks (record dependency on the structure).     |
| `IsActive()` / `IsStatic()`                | Read GameObject state (records dependency).                        |

### Incremental baking

Whenever you read authoring data, **call the corresponding `DependsOn` / `GetComponent`-style helper**, not raw `MonoBehaviour` field access. The baker tracks dependencies for incremental rebakes — without recorded dependencies, edits to the authoring data won't trigger a rebake.

## Component-data interfaces

| Interface                  | Purpose                                                                            | Storage                            |
|----------------------------|------------------------------------------------------------------------------------|------------------------------------|
| `IComponentData`           | Standard per-entity blittable struct.                                              | One slot per entity per chunk.     |
| `ISharedComponentData`     | Per-archetype-and-value. Two entities with the same value live in the same chunk. | One slot per chunk.                |
| `IBufferElementData`       | Element type for `DynamicBuffer<T>` (per-entity dynamic-length array).             | Inline + heap (overflow).          |
| `IEnableableComponent`     | Marker. Component can be enabled/disabled per-entity without structural change.    | Per-entity bit alongside the slot. |
| `ICleanupComponentData`    | Persists across `DestroyEntity`. Holds resources that need a cleanup pass.         | Like `IComponentData`.             |
| `ICleanupSharedComponentData` | Cleanup variant of shared component.                                            | Like `ISharedComponentData`.       |
| `ICleanupBufferElementData` | Cleanup variant of buffer element. Used by `Child` (cited).                       | Like `IBufferElementData`.         |

Project canon — choose by access pattern:

- **Position, velocity, hitpoints**: `IComponentData`. Default.
- **Material index, team ID, render layer**: `ISharedComponentData`. Lets you query/iterate per-team without per-entity branching.
- **Inventory items, hit list, attached effects**: `IBufferElementData`.
- **Active flag, ready-to-fire, alive**: `IEnableableComponent`. Cheaper than add/remove for transient state.
- **Renderable handle, audio source handle**: `ICleanupComponentData` if you need to release the handle when the entity is destroyed.

## `TransformUsageFlags`

Passed to `GetEntity(...)` in a baker; controls which transform components Unity adds to the entity:

| Flag               | Adds                                                |
|--------------------|-----------------------------------------------------|
| `None`             | No transform components.                            |
| `Renderable`       | `LocalToWorld`. Sufficient if the entity only renders, never moves. |
| `Dynamic`          | `LocalTransform` + `LocalToWorld`. Allows runtime movement. |
| `WorldSpace`       | Strips the `Parent` component — entity transform is in world space. |
| `NonUniformScale`  | Adds `PostTransformMatrix` for non-uniform scale.   |

Combine via `|`:

```csharp
GetEntity(TransformUsageFlags.Dynamic | TransformUsageFlags.Renderable)
GetEntity(TransformUsageFlags.WorldSpace | TransformUsageFlags.Renderable)
```

Project rule of thumb: pick the **minimum flags** needed. `Dynamic` adds `LocalTransform` (24 bytes) — for entities that never move (terrain chunks, static decor), use `Renderable` only.

## Baking systems (`[BakingType]`)

For multi-step or cross-entity baking that doesn't fit a single `Baker<T>`:

```csharp
[WorldSystemFilter(WorldSystemFilterFlags.BakingSystem)]
[BakingType]
partial struct PostProcessBakingSystem : ISystem {
    public void OnUpdate(ref SystemState state) {
        // Runs during the baking pass, after all Baker<T>s.
        // Read authoring components, write runtime components.
    }
}
```

Cited at `Unity.Entities.Hybrid/Baking/Baker.cs:11–15` (`[BakingType]` example).

Use cases: cross-entity wiring, query-driven baking decisions, baking-time validation.

## Sub-scenes — where bakers run

Bakers run when:
1. The author saves a sub-scene asset, or
2. The user opens it for editing in Edit Mode (live-baking), or
3. A build is made (build-time baking).

The output is a serialized `EntityScene` — a flat blob of entities and components. At runtime, `Unity.Scenes` loads it and instantiates the entities into the live world.

Bakers do **not** run at runtime. They are pure editor-time conversions.

## Source citations

| Symbol                                       | File                                                       |
|----------------------------------------------|------------------------------------------------------------|
| `IBaker` / `Baker<TAuthoring>` API           | `Unity.Entities.Hybrid/Baking/Baker.cs:18–250`             |
| `[BakingType]` attribute (example)           | `Unity.Entities.Hybrid/Baking/Baker.cs:11–15, 21–22`       |
| `IComponentData` / `ISharedComponentData` / etc. | `Unity.Entities/IComponentData.cs` and siblings        |
| `IEnableableComponent`                       | `Unity.Entities/IEnableableComponent.cs`                   |
| `TransformUsageFlags`                        | `Unity.Transforms/TransformUsageFlags.cs`                  |
