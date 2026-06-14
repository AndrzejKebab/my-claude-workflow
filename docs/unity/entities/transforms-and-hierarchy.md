# Transforms and hierarchy — `LocalTransform`, `LocalToWorld`, `Parent`

The Unity.Transforms package layout. The **read-only-vs-read-write** distinction matters here — `LocalToWorld` is computed by a system, not authored.

## `LocalTransform` — author-side, read-write

```csharp
public struct LocalTransform : IComponentData {
    public float3     Position;
    public quaternion Rotation;
    public float      Scale;       // uniform; non-uniform requires PostTransformMatrix

    public static readonly LocalTransform Identity =
        new LocalTransform { Scale = 1.0f, Rotation = quaternion.identity };

    public static LocalTransform FromMatrix(float4x4 m);       // discards non-uniform & shear
    public static LocalTransform FromMatrixSafe(float4x4 m);   // throws if non-uniform / shear
    // ... + many helpers (FromPosition, FromRotation, FromPositionRotationScale, etc.)
}
```

Cited at `Unity.Transforms/LocalTransform.cs:13–100`.

- **Uniform scale only.** `Scale` is a single float. For non-uniform / shear, add a `PostTransformMatrix` component.
- **Local relative to parent**, if the entity has a `Parent` component. Otherwise relative to world.
- **Read-write**. This is what gameplay code modifies.

## `LocalToWorld` — system-computed, read-only

```csharp
public struct LocalToWorld : IComponentData {
    public float4x4 Value;        // the world-space matrix

    public float3 Right    => Value.c0.xyz;
    public float3 Up       => Value.c1.xyz;
    public float3 Forward  => Value.c2.xyz;
    public float3 Position => Value.c3.xyz;
    public quaternion Rotation;   // computed via math.quaternion(...)
}
```

Cited at `Unity.Transforms/LocalToWorld.cs:29–60`.

**Read-only from gameplay code.** Computed by `LocalToWorldSystem` from the entity's `LocalTransform` and parent chain. Updates run inside `TransformSystemGroup`, which is **inserted at the end of `SimulationSystemGroup`** (cited `Unity.Transforms/EndFrameTransformSystems.cs:13–22`).

Implication: if your system runs **before** `TransformSystemGroup`, the `LocalToWorld` you read is **stale** — it reflects the previous frame's world matrix.

To force fresh `LocalToWorld` mid-frame:
1. Move your system to run **after** `TransformSystemGroup` (rare; usually you want fresh-and-ready by start-of-presentation).
2. Or: read `LocalTransform` + parent chain manually and compute. This is what most gameplay code does — they want **last frame's transform**, which is correct because most calculations are "where am I now, given last frame's physics step".

## `Parent` and `Child`

```csharp
public struct Parent : IComponentData {
    public Entity Value;          // reference to parent entity
}

public struct Child : ICleanupBufferElementData {
    public Entity Value;          // one buffer element per child
}

public struct PreviousParent : ICleanupComponentData {
    public Entity Value;          // internal, used by ParentSystem
}
```

Cited at `Unity.Transforms/Parent.cs:19–63`.

- **Add/remove a `Parent` component** to set or unset parent. The `ParentSystem` automatically maintains the parent's `Child` buffer in response.
- **Don't mutate `Child` directly.** It's a cleanup buffer — `ParentSystem` is the only writer.
- **`PreviousParent`** is used by `ParentSystem` to detect re-parenting. Internal. Don't touch.

## `TransformSystemGroup` — when matrices update

```
SimulationSystemGroup (group)
├── ... your gameplay systems ...
└── TransformSystemGroup
    ├── ParentSystem            — maintains Child buffers
    └── LocalToWorldSystem      — computes LocalToWorld for every entity
```

Cited at `Unity.Transforms/EndFrameTransformSystems.cs:13–22`.

Order:

1. Gameplay systems run (writing `LocalTransform` / `Parent`).
2. `ParentSystem` updates `Child` buffers.
3. `LocalToWorldSystem` walks the hierarchy and computes `LocalToWorld` for every entity.

By the start of `PresentationSystemGroup`, every entity has a fresh `LocalToWorld`.

## Adding non-uniform scale

```csharp
// Add at bake time:
GetEntity(TransformUsageFlags.Dynamic | TransformUsageFlags.NonUniformScale | TransformUsageFlags.Renderable)

// At runtime, modify the post-transform matrix:
em.SetComponentData(entity, new PostTransformMatrix {
    Value = float4x4.Scale(2.0f, 1.0f, 0.5f)
});
```

`PostTransformMatrix` is a 4×4 multiplied **after** the standard `LocalTransform` to produce the final `LocalToWorld`. Use for non-uniform scale, shear, or any custom matrix-tail transform.

Project canon: prefer uniform `LocalTransform.Scale` when possible — it's cheaper and works with the simple transform path. Add `PostTransformMatrix` only when you specifically need non-uniform / shear (e.g. squash-and-stretch animation).

## Reading transforms from a job

```csharp
[BurstCompile]
partial struct MoveJob : IJobEntity {
    public float Dt;
    // ref → write LocalTransform; in → read LocalToWorld
    public void Execute(ref LocalTransform t, in LocalToWorld ltw) {
        // Walk forward in world-space direction:
        t.Position += ltw.Forward * Dt;
    }
}
```

Note `LocalToWorld` here is the **previous frame's** matrix (because `MoveJob` runs in `SimulationSystemGroup` before `TransformSystemGroup`). For most gameplay this is correct — you're applying movement based on facing-direction-as-of-now, and the next-frame `LocalToWorld` reflects this frame's `LocalTransform.Position` after `LocalToWorldSystem` runs.

## Source citations

| Symbol                              | File                                                   |
|-------------------------------------|--------------------------------------------------------|
| `LocalTransform`                    | `Unity.Transforms/LocalTransform.cs:13–100`            |
| `LocalToWorld`                      | `Unity.Transforms/LocalToWorld.cs:29–60`               |
| `Parent`                            | `Unity.Transforms/Parent.cs:19–27`                     |
| `Child` (cleanup buffer)            | `Unity.Transforms/Parent.cs:56–63`                     |
| `PreviousParent`                    | `Unity.Transforms/Parent.cs:37–43`                     |
| `TransformSystemGroup` insertion    | `Unity.Transforms/EndFrameTransformSystems.cs:13–22`   |
| `PostTransformMatrix`               | `Unity.Transforms/PostTransformMatrix.cs`              |
| `TransformUsageFlags`               | `Unity.Transforms/TransformUsageFlags.cs`              |
