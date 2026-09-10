# Latios Framework — idioms for a Burst-oriented ECS engine

The Latios Framework is a useful inspiration for Burst-`ISystem` idioms. It is a suite of low-level APIs and feature sets layered on Unity ECS — it complements Unity ECS rather than replacing it, and in places adjusts ECS mechanisms to add features or performance (Latios README, `https://github.com/Dreaming381/Latios-Framework/blob/main/README.md`). This page records which idioms are useful in a stock-Unity ECS design and which require adopting Latios itself. The related Burst-`ISystem` discipline is in [`burst-isystem-patterns.md`](burst-isystem-patterns.md).

## Attribution

- **Project**: Latios Framework for Unity ECS, version 0.15.7.
- **Author**: Dreaming381 (Dustin Hauptman).
- **Repository**: `https://github.com/Dreaming381/Latios-Framework`.
- **License**: Unity Companion License — "Licensed under the Unity Companion License for Unity-dependent projects" (`LICENSE.md` at the repository root, verified against the cloned source). This is the same license Unity's own DOTS packages ship under; it covers software used together with the Unity engine.

The framework is used here as a design reference. When no Latios code is copied, its idioms — the shape of a solution — can be implemented with project-owned types. Code that is copied or adapted must follow its license and carry the appropriate attribution; design inspiration alone does not create a package dependency.

## Idioms worth adopting

### Explicit system ordering through `SuperSystem` / `RootSuperSystem`

Latios organizes systems into `SuperSystem` groups, each a `ComponentSystemGroup` subclass that overrides a `CreateSystems()` method and adds its children explicitly via `GetOrCreateAndAddManagedSystem<T>()` or `GetOrCreateAndAddUnmanagedSystem<T>()` — update order is the order they are added, rather than implicit attribute injection (`Core/Framework/SuperSystem.cs:18-20,83,131-150`). A `RootSuperSystem` is the variant that serves as a root under explicit ordering (`SuperSystem.cs:13-15`). `CreateSystems()` is abstract; a concrete group implements it (`Core/Systems/Scenes/LiveBakingSuperSystems.cs:15-19`).

The transferable principle is that system order is declared, not inferred from creation order. A stock-Unity implementation uses named `ComponentSystemGroup`s with explicit `[UpdateInGroup]`/`[UpdateBefore]`/`[UpdateAfter]` edges. For example, a `PhysicsSimulationSystemGroup` can be ordered inside `FixedStepSimulationSystemGroup` and become the stable public boundary consumers order around. Latios confirms the idiom; a project does not need Latios's `SuperSystem` base to apply it. See [`system-groups.md`](system-groups.md).

### Deterministic `Rng` / `RngToolkit` keyed by job index

Latios's `Rng` is a deterministic generator that provides a unique sequence per index for each scheduled job: one instance per job, no write-back required, suited to parallel jobs (`Calci/Rng/Rng.cs:7-12`). It is seeded from a `uint` or a hashed string such as the system name (`Rng.cs:19-38`); `Shuffle()` advances the per-job state once before scheduling, and `GetSequence(index)` is called inside the job with a deterministic index — an `entityInQueryIndex`, for instance — to get an independent stream (`Rng.cs:47-62`). The underlying step is SquirrelNoise5, a stateless hash (`Rng.cs:80-90`, attributed in-source to Squirrel Eiserloh, CC-BY-3.0). `RngToolkit` converts a raw `uint` into typed ranged values — `AsBool`, `AsInt(u, minInclusive, maxExclusive)`, vector variants (`Calci/Rng/RngToolkit.cs:7-60`).

The transferable principle is that determinism in a parallel job comes from hashing a deterministic key, not from carrying mutable RNG state. A voxel simulation can key a stateless hash on `(seed, tick, x, y, z)`, making parallel updates reproducible without shared RNG state; see [`burst-isystem-patterns.md`](burst-isystem-patterns.md) § "Hash-based determinism". Latios's index-keyed `Rng` is the variant to reach for where a job index is the natural key — a particle spray or debris ejection — rather than a grid coordinate; `RngToolkit` shows how to turn raw hash output into typed values.

### Collection components — native containers associated with an entity

Latios's `ICollectionComponent` is a pseudo-component that stores native containers on an entity and has the framework track their job dependencies automatically; the interface declares a `TryDispose(JobHandle)` the framework calls on removal (`Core/Components/IManagedStructComponent.cs:21-34`). A collection component is retrieved through `GetCollectionComponent<T>(entity, readOnly)`, constrained `where T : unmanaged, ICollectionComponent`, returning the value with its accumulated use-dependency (`Core/Framework/LatiosWorldUnmanaged.cs:350,383`). It is the Burst-friendly way to attach a `NativeArray`/`NativeList`-bearing struct to a specific entity without an `IComponentData` blittability constraint forbidding the container.

The transferable shape answers "how does a native-container-bearing world struct become reachable from a Burst system": associate it with an entity or singleton as an unmanaged, dependency-tracked value, never a managed field. With stock Unity, use a singleton component holding the blittable native-container-bearing struct and read it through `SystemAPI.GetSingleton`/`GetSingletonRW` ([`command-buffers-singletons.md`](command-buffers-singletons.md)). Latios's collection component shows what automatic dependency tracking adds, without requiring every project to adopt that dependency.

## Idioms that require adopting Latios

### The Latios bootstrap and `LatiosWorld`

Latios replaces the default world creation with its own bootstrap and a `LatiosWorld`/`LatiosWorldUnmanaged` that hosts the framework's features — collection-component storage, blackboard entities, the explicit-ordering machinery (`Core/Framework/LatiosWorld.cs`, `Core/Framework/CoreBootstrap.cs`). Adopting any single Latios feature (collection components, blackboard entities) requires installing this world.

Trade-off: taking `LatiosWorld` creates a runtime dependency on the framework and a non-default world that the consuming project must bootstrap. A project that wants to remain on stock Unity ECS can adopt the underlying idioms without adopting this infrastructure.

### Blackboard entities

A `BlackboardEntity` is an entity plus its `EntityManager`, wrapping a singleton-like entity with shorthand component access — Latios provides a scene-scoped and a world-scoped one (`Core/Framework/BlackboardEntity.cs:7-13`, `SuperSystem.cs:33-34`). It is Latios's ergonomic layer over the global-state-on-an-entity pattern, including `GetCollectionComponent<T>` access (`BlackboardEntity.cs:320-322`).

Trade-off: the blackboard entity is part of the `LatiosWorld` surface, and its convenience comes from that world. A stock-Unity project can use the underlying idiom — global or world state on a singleton entity reached through `SystemAPI` — without the `BlackboardEntity` wrapper ([`command-buffers-singletons.md`](command-buffers-singletons.md)).

## Source citations

| Topic | Reference |
|-------|-----------|
| License (Unity Companion License) | `https://github.com/Dreaming381/Latios-Framework/blob/main/LICENSE.md` |
| Repository / version 0.15.7 / framework purpose | `https://github.com/Dreaming381/Latios-Framework` (`README.md`) |
| `SuperSystem` / `RootSuperSystem`, `CreateSystems`, add-system API | `Core/Framework/SuperSystem.cs:13-20,83,131-150`; `Core/Systems/Scenes/LiveBakingSuperSystems.cs:15-19` |
| Deterministic `Rng` / `RngSequence` / `RngToolkit` | `Calci/Rng/Rng.cs:7-90`; `Calci/Rng/RngToolkit.cs:7-60` |
| `ICollectionComponent`, `GetCollectionComponent<T>` | `Core/Components/IManagedStructComponent.cs:21-34`; `Core/Framework/LatiosWorldUnmanaged.cs:350,383` |
| `BlackboardEntity` | `Core/Framework/BlackboardEntity.cs:7-13,320-322`; `Core/Framework/SuperSystem.cs:33-34` |
| Stock-Unity system ordering alternative | [`system-groups.md`](system-groups.md) |
| Hash-based determinism for voxel simulation | [`burst-isystem-patterns.md`](burst-isystem-patterns.md) |

(Latios paths above are relative to the repository root; clone with `git clone https://github.com/Dreaming381/Latios-Framework` to reach them.)
