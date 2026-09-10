# Deepening

How to deepen a cluster of shallow modules safely, given its dependencies. Assumes the vocabulary in [LANGUAGE.md](LANGUAGE.md) — **module**, **interface**, **seam**, **adapter**, **humble shell**.

The category of a module's dependencies determines how the deepened module is tested across its seam — and in Unity, whether those tests are **EditMode** (milliseconds, no scene) or **PlayMode** (seconds, full player loop). Every deepening should push as much behaviour as possible into a category testable in EditMode.

## Dependency categories

### 1. Engine-free (in-process)

Pure C# over plain data: math, meshing, pathfinding cost functions, priority rules, save-data transforms. Includes Burst-compatible static functions over blittable structs and `NativeArray`s — Burst code that takes data in and returns data out is category 1 even though it ships inside jobs. Always deepenable: merge the shallow modules, test through the new interface directly with EditMode tests. No adapter needed.

### 2. Engine-value

Code that only needs *values* the engine provides: `Time.deltaTime`, `Input`, `Random`, `Application.persistentDataPath`, `Physics.Raycast` results. Deepenable to category 1 by **passing the values across the interface** instead of reading globals inside — dt is a parameter, input is a struct the shell fills, raycast hits arrive as data. The deepened core becomes engine-free; the humble shell does the reading. This is the highest-value move in most Unity codebases and needs no port: the interface just takes data.

### 3. Engine-loop-bound (humble shell)

Behaviour inseparable from the player loop: physics stepping, animation, coroutines/UniTask timing chains, NavMesh, rendering, `OnCollisionEnter`. Define the seam between *deciding* and *doing*: the deep core decides (pure, category 1), a thin humble shell does (touches engine state, no logic). The shell is one adapter; an EditMode test driving the core directly is the second. Keep a *small* number of PlayMode tests only for the shell's wiring — the loop itself — not the logic.

For **ECS**, the component data *is* the seam. Deepen by concentrating a feature's logic into one system (or static function set the system calls) whose contract is "reads these components, writes those." Test in EditMode by creating a `World`, inserting entities with the input components, updating the system, asserting on the output components. Burst logic in static methods can skip the world entirely and be tested as category 1.

### 4. Remote but owned (ports & adapters)

Your own code across a process/network seam — game server endpoints, Netcode for Entities RPCs/ghosts, a companion backend. Define a **port** at the seam; the deep module owns the logic, transport is an injected adapter. Tests use an in-memory adapter (for Netcode: local/IPC transport driving client+server worlds in one process). Production uses the real transport.

Recommendation shape: *"Define a port at the seam, implement the Netcode transport adapter for production and an in-memory adapter for tests, so the colony command logic sits in one deep module even though it executes across client and server."*

### 5. True external (mock)

Third-party services you don't control — Steamworks, platform services, analytics, storefronts. Injected port; tests provide a mock adapter. Never let `SteamAPI.*` calls leak past one adapter file.

## Seam discipline

- **One adapter means a hypothetical seam. Two adapters means a real one.** Don't introduce a port unless at least two adapters are justified (typically production + test / humble shell + EditMode harness). A single-adapter seam is just indirection — and in Unity, indirection often costs a virtual call in a hot loop for nothing.
- **Internal seams vs external seams.** A deep module can have internal seams private to its implementation and its own tests. Don't expose them through the interface — and don't serialize them: a `[SerializeField]` reference to an internal collaborator promotes it to interface via the inspector.
- **asmdef the seam once it's real.** When a deepened module has a genuine external seam, give it an asmdef so the compiler enforces the dependency direction (and compile times improve as a side effect). Don't asmdef speculatively — that's the single-adapter mistake in folder form.
- **Hot-path seams must be data seams.** Where Burst/jobs are involved, the seam must be component data or blittable structs, not managed interfaces — a C# `interface` cannot cross into Burst. Choose seam *placement* accordingly: decide in managed land, execute in Burst land, with data as the contract.

## Testing strategy: replace, don't layer

- Old tests on the shallow modules become waste once tests exist at the deepened module's interface — delete them.
- Write the new tests at the deepened interface. **The interface is the test surface.** Prefer EditMode; every PlayMode test should justify why it needs the loop.
- Tests assert on observable outcomes through the interface — output components, returned data, emitted messages — not internal state, not `GameObject` hierarchies, not private fields via reflection.
- Tests should survive internal refactors. If a test breaks when the implementation changes shape (MonoBehaviour → ISystem, managed → Burst), it was testing past the interface.
- Put tests in a test asmdef next to the module's asmdef, mirroring the seam.
