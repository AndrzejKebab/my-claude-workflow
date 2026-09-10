# Language

Shared vocabulary for every suggestion this skill makes. Use these terms exactly — don't substitute "component" (collides with `UnityEngine.Component` *and* ECS `IComponentData`), "manager," "service," "API," or "boundary." Consistent language is the whole point.

## Terms

**Module**
Anything with an interface and an implementation. Deliberately scale-agnostic. In Unity this applies equally to: a static Burst-compatible function set, a plain C# class, a `MonoBehaviour` plus its helpers, an `ISystem` plus the component data it owns, a `ScriptableObject` type, an asmdef assembly, or a prefab together with its scripts.
_Avoid_: unit, component, manager, service, system (bare — say "the pathfinding module" even if it happens to be an `ISystem`).

**Interface**
Everything a caller — *or a scene author* — must know to use the module correctly. In Unity that is far more than the C# surface: serialized fields and their valid ranges, required components and tags, script execution order assumptions, lifecycle ordering (`Awake` vs `OnEnable` vs `Start`), which thread/world it runs on, Burst compatibility constraints, scene setup it silently assumes, and events it fires. A `[SerializeField]` is interface. An implicit "must live under the GameManager object" is interface — undocumented, but interface.
_Avoid_: API, signature.

**Implementation**
What's inside a module. Distinct from **Adapter**: a Postgres-style repo is a small adapter with a large implementation; an in-memory fake is a large adapter with a small implementation. Reach for "adapter" when the seam is the topic.

**Depth**
Leverage at the interface — behaviour a caller (or test, or scene author) can exercise per unit of interface they must learn. **Deep** = a lot behind a little. **Shallow** = interface nearly as complex as the implementation. A `MonoBehaviour` with 14 public fields wired in the inspector and 6 public methods called from 3 other scripts is shallow no matter how small its body is.

**Seam** _(Feathers)_
A place where behaviour can be altered without editing in that place. Unity's seams, roughly in order of cheapness: a plain C# interface injected via DI (VContainer); ECS **component data between systems** (the writer/reader contract *is* the seam); an asmdef boundary; a message topic (MessagePipe); a `ScriptableObject` channel; a prefab variant. Choosing where the seam goes is its own design decision.
_Avoid_: boundary.

**Humble shell**
The Unity-specific adapter shape: a thin `MonoBehaviour`/`ISystem` that only touches engine state (read input, move transform, schedule job) and forwards everything to a deep, engine-free core. The shell is an adapter at the engine seam; the core is the module.

**Adapter**
A concrete thing that satisfies an interface at a seam. Role, not substance.

**Leverage**
What callers get from depth: more capability per unit of interface learned. One implementation pays back across N call sites, M tests, and every scene that uses it.

**Locality**
What maintainers get from depth: change, bugs, knowledge, and verification concentrate in one place. In Unity, locality also means *one place in the scene/prefab hierarchy* — behaviour smeared across five inspector-wired objects has no locality even if the code is tidy.

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module may be internally made of small swappable parts — they just aren't interface. Internal seams (used by the module's own tests) are fine; don't promote them to the external seam.
- **The deletion test.** Imagine deleting the module. Complexity vanishes → it was a pass-through (most `*Manager` classes fail here). Complexity reappears across N callers/scenes → it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. If testing requires building a scene, adding components, and pumping frames, the *engine* is inside the interface — usually a sign the core should be extracted behind a humble shell.
- **One adapter means a hypothetical seam. Two adapters means a real one.** Typically production + test. In Unity the test adapter is often "EditMode test calling the core directly."
- **Serialized surface is interface.** Refactors that shrink the C# surface but explode the inspector wiring have made the module shallower, not deeper.

## Relationships

- A **Module** has exactly one **Interface**.
- **Depth** is measured against that **Interface** — including its serialized and scene-setup surface.
- A **Seam** is where the **Interface** lives; an **Adapter** (often a humble shell) sits at it.
- **Depth** produces **Leverage** for callers and scene authors, **Locality** for maintainers.

## Rejected framings

- **Depth as implementation-lines ÷ interface-lines**: rewards padding. Depth-as-leverage instead.
- **"Interface" as the C# `interface` keyword**: too narrow — interface includes every fact a caller or scene author must know.
- **"Decouple everything with events."** Event/message soup trades visible coupling for invisible coupling and destroys locality — nobody can answer "what happens when this fires." A message topic is a seam like any other: it must pass the two-adapter test and someone must own the contract.
- **"Manager" / "Controller" as architecture.** These names mark modules that failed the deletion test. Renaming them is not deepening them.
- **"MonoBehaviour = bad, ECS = good."** Paradigm migration is not deepening. A shallow `ISystem` tangle is worse than a deep `MonoBehaviour` module.
