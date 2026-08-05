---
name: netcode-6-inprocess-session-harness
description: "Hard-won rules for driving netcode 6.6 server+clients+thin-clients in-process in tests (world creation, time, thin-client input, input actions)"
metadata: 
  node_type: memory
  type: project
  originSessionId: ed62fdaa-80a8-4140-90b5-7452588fa52e
  modified: 2026-07-21T22:38:19.417Z
---

Netcode 6.6.0 in-process session testing (working harness: `Assets/Tests/Runtime/NetcodeSessionHarness.cs`; full defect log: `docs/orchestrate/box3d-entities/03-session-log.md`).

**Why:** each of these was a silent failure costing a debug cycle; none is documented upstream.

**How to apply:**
- Create worlds ONLY via `ClientServerBootstrap.CreateServerWorld/CreateClientWorld/CreateThinClientWorld` — the server rate manager hard-casts `group.World` to the internal `NetcodeWorld`; a plain `new World(...)` throws `InvalidCastException` on first tick.
- For manual ticking: `ScriptBehaviourUpdateOrder.RemoveWorldFromCurrentPlayerLoop(world)`, disable `UpdateWorldTimeSystem`, `world.SetTime` per tick, update Init/Sim/Presentation groups server-first, and advance `NetworkTimeSystem.s_FixedTimestampMS` (+dt ms per tick) — it is an internal static **property** (`GetProperty`, not `GetField`); without it, client tick estimation runs on the real stopwatch and commands are stamped for wrong ticks (server receives zeros).
- Thin clients: the generated `CopyInputToCommandBufferSystem` requires **`GhostOwner` (= own NetworkId) on the input entity** in addition to `CommandTarget` on the connection; and thin-client worlds must load the same subscenes as the server or `GhostCollectionSystem` disconnects everyone ("ghost ... does not have a valid prefab").
- A connection has **one `CommandTarget` slot**, and `CommandSendSystem` sends ONLY that entity's buffer (plus enabled `AutoCommandTarget` ghosts, which thin clients never have). Two thin-client input systems for two input types (e.g. `CharacterInput` vs `CarInput`) silently race for the slot; the winner is system creation order, which resolved DIFFERENTLY in editor vs player build (bots drove in one, sat parked in the other, 2026-07-22). Gate each thin-client input system on its game's content singleton (`RequireForUpdate<CarSpawner>` / `<CharacterSpawner>`) so only one exists per world.
- Input actions only process in play mode → session tests are PlayMode; drive with `InputSystem.AddDevice<Gamepad>()` + `QueueStateEvent` and let real frames pump. `Unity.InputSystem.TestFramework` cannot compile in inputsystem 1.19 (duplicate `versionDefines` key kills its define constraint).
- The game bootstrap auto-creates+connects default worlds on play-mode entry — dispose them in harness setup and use a non-default port.
- A dynamic body placed in a subscene WITHOUT ghost authoring simulates on the server but never replicates — clients render it frozen at its baked pose with no warning anywhere. Prespawned ghosts must be **prefab instances** (a plain scene GameObject with `GhostAuthoringComponent` won't bake); interpolated default mode is the fit for server-simulated props. Symptom in a hosted session: "I can't push the crates" while the server-side crate is actually moving.
- Simulated latency in code: `NetworkSimulatorSettings.Enabled` has a private setter outside the editor — the ONLY code path is a custom `INetworkStreamDriverConstructor` on `NetworkStreamReceiveSystem.DriverConstructor` (set before world creation, restore after) that builds the client UDP driver manually with `WithSimulatorStageParameters` + `DefaultDriverBuilder.CreateClientSimulatorPipelines` (needs UNITY_INCLUDE_TESTS/NETCODE_DEBUG/editor). `PacketDelayMs` is ONE-WAY — pass RTT/2. Loopback UDP supports many in-process clients.
- Custom graphical smoothing that overwrites a root entity's `LocalToWorld` does NOT affect child entities — `LocalToWorldSystem` composes children from the parent's raw `LocalTransform`, so a mesh on a visual child keeps stepping while the root (and a camera reading it) glides. Recompose the subtree (childLocal × PostTransformMatrix, recursive) from the smoothed matrix, and make presentation oracles measure the RENDERED (child) pose, not the root.
- Gate oracles under prediction: same-moment client-vs-server position of a fast predicted body measures prediction lead × velocity, not error — use post-hoc trajectory alignment (min distance from each client sample to the full server path). The manual-clock harness ignores netcode's time-scale feedback, making `NumPredictedTicksExpected` bimodal (median tiny, resync spikes ~30) — bound the median and the MaxPredictAhead ceiling, and prove "predicts ahead" via contact-response < RTT instead. Single-sample probes flake on correction frames: assert majorities.

Related: [[burst-aot-extern-struct-rule]].
