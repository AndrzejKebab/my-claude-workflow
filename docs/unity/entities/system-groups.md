# System groups and update ordering

All engine `file:line` citations are under `/mnt/archive4/UNITY/Projects/mara/Library/PackageCache/com.unity.entities@e00d2f1d321e/Unity.Entities/`, verified on disk against entities 6.5.0.

## `ComponentSystemGroup`

A `ComponentSystemGroup` is a system that owns and updates a set of child systems in a sorted order. It is `public abstract unsafe partial class ComponentSystemGroup : SystemBase` (`ComponentSystemGroup.cs:36`) — a managed `SystemBase`, not an `ISystem`, even though its children may be Burst `ISystem`s. The group's `OnUpdate` sorts its members by their ordering attributes and calls each child's update in turn; an author rarely overrides it.

A custom group is a one-line declaration: an empty `partial class` deriving from `ComponentSystemGroup`, tagged with the `[UpdateInGroup]` of the parent group it nests in. `mara`'s physics2d package defines exactly this as the stable public group consumers order around:

```csharp
[UpdateInGroup(typeof(FixedStepSimulationSystemGroup))]
public partial class Physics2DSimulationSystemGroup : ComponentSystemGroup { }
```

(`Packages/is.zori.entities.physics2d/Runtime/Systems/Physics2DSimulationSystemGroup.cs:14-15`). The XML summary states the intent: it is the stable boundary a consumer orders its own systems around, rather than around the package's individual systems — a consumer reading stepped poses runs `[UpdateAfter(typeof(Physics2DSimulationSystemGroup))]`, one feeding the step runs `[UpdateBefore]` it. A custom group is the right tool whenever a package exposes an ordering contract: consumers depend on the group, the package is free to reorder its internals.

## The ordering attributes

Four attributes place a system in the graph and constrain its order. All are read by the group's sort, and all target a system that is a member of the *same* group.

- `[UpdateInGroup(Type groupType)]` — `public class UpdateInGroupAttribute : Attribute` (`ScriptBehaviourUpdateOrder.cs:143`), constructor `UpdateInGroupAttribute(Type groupType)` (`:162`). Adds the tagged system to that group; the group's `Update()` then drives it. Two optional flags refine placement within the group: `OrderFirst = true` (`:149`) sorts the system before all members that are not also `OrderFirst`, and `OrderLast = true` (`:154`) sorts it after all members that are not also `OrderLast`. Setting both is invalid and throws (`:140`).
- `[UpdateBefore(Type systemType)]` — `public class UpdateBeforeAttribute : Attribute, ISystemOrderAttribute` (`ScriptBehaviourUpdateOrder.cs:22`), constructor `UpdateBeforeAttribute(Type systemType)` (`:30`). The tagged system sorts before the named system.
- `[UpdateAfter(Type systemType)]` — `public class UpdateAfterAttribute : Attribute, ISystemOrderAttribute` (`ScriptBehaviourUpdateOrder.cs:50`), constructor `UpdateAfterAttribute(Type systemType)` (`:58`). The tagged system sorts after the named system.

`mara`'s physics2d pipeline is a clean worked example of explicit edges resolving a five-system order inside one group. All five carry `[UpdateInGroup(typeof(Physics2DSimulationSystemGroup))]`, and:

- `PhysicsBody2DCleanupSystem` and `PhysicsJoint2DCreationSystem` carry `[UpdateBefore(typeof(PhysicsWorld2DSystem))]` (`…/PhysicsBody2DCleanupSystem.cs:42`, `…/PhysicsJoint2DCreationSystem.cs:39`).
- `PhysicsBody2DWriteBackSystem` carries `[UpdateAfter(typeof(PhysicsWorld2DSystem))]` (`…/PhysicsBody2DWriteBackSystem.cs:31`).

The edges pin the order `Cleanup → JointCreation → World step → JointBreak → WriteBack` without any system relying on the order it happened to be created in (`Packages/is.zori.entities.physics2d/Documentation~/runtime-systems.md:75-82`). A cross-group example: the character controller orders against the *group* — `[UpdateAfter(typeof(Physics2DSimulationSystemGroup))]` so its solve reads the just-stepped world (`…/KinematicCharacterPhysicsSolveSystem2D.cs:41-43` orders within `FixedStepSimulationSystemGroup` after `StoreKinematicCharacterBodyPropertiesSystem2D` and before `KinematicCharacterDeferredImpulsesSystem2D`).

## `[CreateAfter]` / `[CreateBefore]` — a different axis

`[CreateAfter]` and `[CreateBefore]` constrain *creation* order, not *update* order. `public class CreateAfterAttribute : Attribute, ISystemOrderAttribute` (`ScriptBehaviourUpdateOrder.cs:106`), constructor `CreateAfterAttribute(Type systemType)` (`:114`); `CreateBeforeAttribute` is its mirror (`:78`, ctor `:86`). The XML is explicit that this governs when each system's `OnCreate` runs during world initialization, and that destruction order is the reverse of creation order (`:103-104`). Use it only when one system's `OnCreate` must read state another system's `OnCreate` published (for example, a system whose `OnCreate` reads a singleton a sibling created). It does **not** affect the per-frame update order — that is what `[UpdateBefore]`/`[UpdateAfter]` are for. Like the update edges, the target must be in the same group (`:83-84`, `:111-112`).

## The standard groups

The default world's top-level groups update once per frame in this order, each a `ComponentSystemGroup` in `DefaultWorld.cs`:

- `InitializationSystemGroup` — `public partial class InitializationSystemGroup : ComponentSystemGroup` (`DefaultWorld.cs:153`).
- `SimulationSystemGroup` — (`DefaultWorld.cs:683`). The default home for gameplay/simulation systems; an `ISystem` with no `[UpdateInGroup]` lands here.
- `PresentationSystemGroup` — (`DefaultWorld.cs:769`). Rendering-rate work. `mara`'s NSprites `SpriteRenderingSystem` lives here (`…/SpriteRenderingSystem.cs:12`).

### The fixed-step group

`FixedStepSimulationSystemGroup` — `public partial class FixedStepSimulationSystemGroup : ComponentSystemGroup` (`DefaultWorld.cs:329`) — nests inside `SimulationSystemGroup` and updates its children at a fixed timestep, sub-stepping (catching up) to track wall-clock. Its `Timestep` property (`DefaultWorld.cs:335`) defaults to `1/60` s and is clamped to `[0.0001, 10.0]`; the default constructor installs a `FixedRateCatchUpManager` (`DefaultWorld.cs:348-353`). The timestep is a group-global property shared by every member of the group, not a per-system value. `mara`'s physics simulation runs here precisely for the determinism and framerate-independence this gives: `Physics2DSimulationSystemGroup` is `[UpdateInGroup(typeof(FixedStepSimulationSystemGroup))]`, so its `Simulate(dt)` steps at the group's fixed `dt` with no bespoke sub-stepping (`…/Physics2DSimulationSystemGroup.cs:14`, `…/runtime-systems.md:51`). The package's binding rule names this organization directly: systems belong in named groups with explicit ordering edges, never implicit creation-order dependence (`Packages/is.zori.pixelworld/docs/orchestrate/pixelworld-engine/01-context.md:46,104`).

## The built-in `EntityCommandBufferSystem`s

Each standard group ships a begin/end pair of `EntityCommandBufferSystem`s — the sanctioned sync points where a deferred ECB is played back. They are placed with the `OrderFirst`/`OrderLast` flags so they bracket the group's other members:

| ECB system | Declaration | Placement |
|------------|-------------|-----------|
| `BeginInitializationEntityCommandBufferSystem` | `DefaultWorld.cs:13` | `[UpdateInGroup(typeof(InitializationSystemGroup), OrderFirst = true)]` (`:12`) |
| `EndInitializationEntityCommandBufferSystem` | `DefaultWorld.cs:84` | `OrderLast = true` (`:83`) |
| `BeginFixedStepSimulationEntityCommandBufferSystem` | `DefaultWorld.cs:178` | `FixedStepSimulationSystemGroup`, `OrderFirst` (`:177`) |
| `EndFixedStepSimulationEntityCommandBufferSystem` | `DefaultWorld.cs:249` | `OrderLast` (`:248`) |
| `BeginSimulationEntityCommandBufferSystem` | `DefaultWorld.cs:534` | `SimulationSystemGroup`, `OrderFirst` (`:533`) |
| `EndSimulationEntityCommandBufferSystem` | `DefaultWorld.cs:605` | `OrderLast` (`:604`) |
| `BeginPresentationEntityCommandBufferSystem` | `DefaultWorld.cs:699` | `PresentationSystemGroup`, `OrderFirst` (`:698`) |

A system that wants its structural changes applied at one of these points records into an ECB obtained from that system's singleton (the `Begin…`/`End…` choice picks when in the frame the playback happens) rather than playing back its own ECB inline. `mara`'s `StoreDynamicBodyDataSystem2D` documents using `EndSimulationEntityCommandBufferSystem` for a newly-seen-body component add (`…/StoreDynamicBodyDataSystem2D.cs:28-30`). The mechanics of obtaining and recording into one are in [`command-buffers-singletons.md`](command-buffers-singletons.md).

## Explicit edges are the binding idiom

The group sort is deterministic only to the extent the edges constrain it; two systems with no edge between them sort in an unspecified order, and a system that *reads* what another *writes* with no `[UpdateAfter]` between them is a latent ordering bug that no compile catches. The rule for `mara`'s engine, stated in the package's shape discipline: systems live in named groups with explicit `[UpdateInGroup]`/`[UpdateBefore]`/`[UpdateAfter]` edges, never implicit creation-order dependence — idiom deviation here is a real defect even when no generic code smell fires, because the engine is judged against how regarded DOTS packages organize this work (`…/01-context.md:104`). State every data-dependency edge between two systems explicitly; reserve `[CreateAfter]`/`[CreateBefore]` for the rarer creation-order case.
