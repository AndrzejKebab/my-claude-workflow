# Latios Framework — idioms that inform this engine

The Latios Framework is the named inspiration for the Burst-ISystem idioms in `is.zori.pixelworld`. It is a suite of low-level APIs and feature-sets layered on Unity's ECS — it complements Unity ECS rather than replacing it, and in places tweaks ECS's underlying mechanisms to add features or performance (Latios README, `https://github.com/Dreaming381/Latios-Framework/blob/main/README.md`). This page records which of its idioms inform this engine, which we deliberately do not adopt, and why — it is inspiration and attribution, not a Latios manual. The engine's own Burst-ISystem discipline is in [`burst-isystem-patterns.md`](burst-isystem-patterns.md).

## Attribution

- **Project**: Latios Framework for Unity ECS, version 0.15.7.
- **Author**: Dreaming381 (Dustin Hauptman).
- **Repository**: `https://github.com/Dreaming381/Latios-Framework`.
- **License**: Unity Companion License — "Licensed under the Unity Companion License for Unity-dependent projects" (`LICENSE.md` at the repository root, verified against the cloned source). This is the same license Unity's own DOTS packages ship under; it covers software used together with the Unity engine.

The framework is read as a design reference. No Latios code is copied into `is.zori.pixelworld`; the engine takes its idioms — the shape of a solution — and implements them against its own types. The package's own vendoring rule applies only to code adapted into it (e.g. BurstTriangulator, MIT), which ships with `THIRD-PARTY-NOTICES` attribution (`Packages/is.zori.pixelworld/docs/orchestrate/pixelworld-engine/01-context.md` § "Attribution for vendored code"); Latios, being inspiration rather than vendored code, is attributed here in the canon rather than in shipped source.

## Idioms this engine takes

### Explicit system ordering through `SuperSystem` / `RootSuperSystem`

Latios organizes systems into `SuperSystem` groups, each a `ComponentSystemGroup` subclass that overrides a `CreateSystems()` method and adds its children explicitly via `GetOrCreateAndAddManagedSystem<T>()` or `GetOrCreateAndAddUnmanagedSystem<T>()` — update order is the order they are added, rather than implicit attribute injection (`Core/Framework/SuperSystem.cs:18-20,83,131-150`). A `RootSuperSystem` is the variant that serves as a root under explicit ordering (`SuperSystem.cs:13-15`). `CreateSystems()` is abstract; a concrete group implements it (`Core/Systems/Scenes/LiveBakingSuperSystems.cs:15-19`).

What this engine takes: the principle that system order is declared, not inferred from creation order. The engine expresses it the standard-Unity way — named `ComponentSystemGroup`s with explicit `[UpdateInGroup]`/`[UpdateBefore]`/`[UpdateAfter]` edges (`01-context.md` § "Burst compatibility": "organized into named `SystemGroup`s with explicit … edges (the DOTS domain idiom)"). mara's physics package already follows this: `Physics2DSimulationSystemGroup` is a `ComponentSystemGroup` ordered `[UpdateInGroup(typeof(FixedStepSimulationSystemGroup))]`, the stable public group consumers order around (`Packages/is.zori.entities.physics2d/Runtime/Systems/Physics2DSimulationSystemGroup.cs`). Latios confirms the idiom; the engine does not need Latios's `SuperSystem` base to apply it. The detail of how the engine wires its groups is in [`system-groups.md`](system-groups.md).

### Deterministic `Rng` / `RngToolkit` keyed by job index

Latios's `Rng` is a deterministic generator that provides a unique sequence per index for each scheduled job: one instance per job, no write-back required, suited to parallel jobs (`Calci/Rng/Rng.cs:7-12`). It is seeded from a `uint` or a hashed string such as the system name (`Rng.cs:19-38`); `Shuffle()` advances the per-job state once before scheduling, and `GetSequence(index)` is called inside the job with a deterministic index — an `entityInQueryIndex`, for instance — to get an independent stream (`Rng.cs:47-62`). The underlying step is SquirrelNoise5, a stateless hash (`Rng.cs:80-90`, attributed in-source to Squirrel Eiserloh, CC-BY-3.0). `RngToolkit` converts a raw `uint` into typed ranged values — `AsBool`, `AsInt(u, minInclusive, maxExclusive)`, vector variants (`Calci/Rng/RngToolkit.cs:7-60`).

What this engine takes: the principle that determinism in a parallel job comes from hashing a deterministic key, not from carrying mutable RNG state. The engine's `PixelHash` is the same idea keyed on a world coordinate instead of a job index: a stateless hash of `(seed, tick, x, y)` with no stored state, which is what makes the parallel simulation lock-free and reproducible (`Packages/is.zori.pixelworld/Runtime/PixelHash.cs:6-18`; see [`burst-isystem-patterns.md`](burst-isystem-patterns.md) § "Hash-based determinism"). Latios's index-keyed `Rng` is the variant to reach for where a job index is the natural key — a particle spray, a debris ejection — rather than a grid coordinate; `RngToolkit`'s ranged conversions are the reference for turning a `PixelHash` output into a typed value.

### Collection components — native containers associated with an entity

Latios's `ICollectionComponent` is a pseudo-component that stores native containers on an entity and has the framework track their job dependencies automatically; the interface declares a `TryDispose(JobHandle)` the framework calls on removal (`Core/Components/IManagedStructComponent.cs:21-34`). A collection component is retrieved through `GetCollectionComponent<T>(entity, readOnly)`, constrained `where T : unmanaged, ICollectionComponent`, returning the value with its accumulated use-dependency (`Core/Framework/LatiosWorldUnmanaged.cs:350,383`). It is the Burst-friendly way to attach a `NativeArray`/`NativeList`-bearing struct to a specific entity without an `IComponentData` blittability constraint forbidding the container.

What this engine takes: the shape of the answer to "how does a native-container-bearing world struct become reachable from a Burst system" — associate it with an entity (or a singleton) as an unmanaged, dependency-tracked value, never a managed field. The engine reaches this shape with standard-Unity primitives — a singleton component holding the blittable, native-container-bearing struct, read through `SystemAPI.GetSingleton`/`GetSingletonRW` ([`command-buffers-singletons.md`](command-buffers-singletons.md)) — rather than adopting Latios's framework type. The idiom informs the engine's chunk-pool-reachability decision; the Latios type is the reference for what automatic dependency tracking buys, not a dependency the engine takes.

## Idioms this engine deliberately does not adopt

### The Latios bootstrap and `LatiosWorld`

Latios replaces the default world creation with its own bootstrap and a `LatiosWorld`/`LatiosWorldUnmanaged` that hosts the framework's features — collection-component storage, blackboard entities, the explicit-ordering machinery (`Core/Framework/LatiosWorld.cs`, `Core/Framework/CoreBootstrap.cs`). Adopting any single Latios feature (collection components, blackboard entities) requires installing this world.

Why not: the engine ships as a self-contained Unity source-library package and deliberately vendors-and-adapts rather than depending (`01-context.md` § user directives: "The package is self-contained — vendor and adapt, do not depend"). Taking `LatiosWorld` is a hard runtime dependency on the entire framework and on a non-default world the consuming project must bootstrap — the opposite of self-contained. The engine adopts the idioms Latios pioneered while standing on stock Unity ECS, so a consumer drops the package into any DOTS project without a framework bootstrap.

### Blackboard entities

A `BlackboardEntity` is an entity plus its `EntityManager`, wrapping a singleton-like entity with shorthand component access — Latios provides a scene-scoped and a world-scoped one (`Core/Framework/BlackboardEntity.cs:7-13`, `SuperSystem.cs:33-34`). It is Latios's ergonomic layer over the global-state-on-an-entity pattern, including `GetCollectionComponent<T>` access (`BlackboardEntity.cs:320-322`).

Why not directly: the blackboard entity is part of the `LatiosWorld` surface (above) and its convenience comes from that world. The engine uses the underlying idiom — global/world state lives on a singleton entity reached through `SystemAPI` — without the `BlackboardEntity` wrapper, for the same self-contained-package reason ([`command-buffers-singletons.md`](command-buffers-singletons.md)).

## Source citations

| Topic | Reference |
|-------|-----------|
| License (Unity Companion License) | `https://github.com/Dreaming381/Latios-Framework/blob/main/LICENSE.md` |
| Repository / version 0.15.7 / framework purpose | `https://github.com/Dreaming381/Latios-Framework` (`README.md`) |
| `SuperSystem` / `RootSuperSystem`, `CreateSystems`, add-system API | `Core/Framework/SuperSystem.cs:13-20,83,131-150`; `Core/Systems/Scenes/LiveBakingSuperSystems.cs:15-19` |
| Deterministic `Rng` / `RngSequence` / `RngToolkit` | `Calci/Rng/Rng.cs:7-90`; `Calci/Rng/RngToolkit.cs:7-60` |
| `ICollectionComponent`, `GetCollectionComponent<T>` | `Core/Components/IManagedStructComponent.cs:21-34`; `Core/Framework/LatiosWorldUnmanaged.cs:350,383` |
| `BlackboardEntity` | `Core/Framework/BlackboardEntity.cs:7-13,320-322`; `Core/Framework/SuperSystem.cs:33-34` |
| Engine: self-contained, vendor-not-depend; named groups with explicit edges | `Packages/is.zori.pixelworld/docs/orchestrate/pixelworld-engine/01-context.md` § user directives, § "Burst compatibility" |
| Engine hash-based determinism (the `Rng` parallel) | `Packages/is.zori.pixelworld/Runtime/PixelHash.cs:6-18` |

(Latios paths above are relative to the repository root; clone with `git clone https://github.com/Dreaming381/Latios-Framework` to reach them.)
