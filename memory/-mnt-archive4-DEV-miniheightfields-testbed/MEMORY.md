# Memory index

Working-style rules live in the repo, not here: `AGENTS.md` + `docs/agent-working-rules.md`.

## Project shape

- [chajdas-freeze design phase](chajdas-freeze-design-phase.md) — reviewed tech design done; wave-0 probes gate integration; awaits user punch-card pass
- [mhf ancestry](mhf-ancestry-zori-heightfields.md) — minimal port of `is.zori.heightfields`; audits span the ancestor, port never author fresh
- [Six URP projects are husks](six-urp-projects-are-husks.md) — they only hold package refs + test runs; search only `is.zori.miniheightfields` / `is.zori.testbed`
- [Shared-tree sequencing](shared-tree-sequencing.md) — six projects compile one submodule; never parallel a package-mutating implementer with compile-dependent observers
- [Read the reference implementation](read-the-reference-implementation.md) — bevy_terrain is Kühnert's live code; derivatives filter within a tile, distance selects the tile
- [wasm defers, one backend ships](wasm-defers-never-shapes-io.md) — minimal seam over the read *operation*; mounting stays out; Burst forbids virtual dispatch
- [VT streaming: minimal C#, then native plugin](vt-streaming-minimal-then-native-plugin.md) — no Burst/Jobs IO layer; async upload is impossible from C# by construction
- [VT archive IO interface shape](vt-archive-io-interface-shape.md) — packing may block; reading must stay batch-submit/poll even while sync inside
- [Editor decides, player executes](editor-decides-player-executes.md) — builds strip source content; no runtime hash check, no build-time re-bake
- [Freeze is all-or-nothing](freeze-is-all-or-nothing.md) — no hybrid fill; clamp selection to the archive's mips and let the page-table parent walk cover the rest

## Working style

- [Act autonomously, commit freely](act-autonomously-commit-freely.md) — no confirmation seams mid-scope; checkpoint each green increment
- [-nographics by workload, not by tool](nographics-by-workload-not-by-tool.md) — compile/analysis take it (10 min → 15 s); player builds must NOT, the VT archive freeze renders
- [/research GPU jobs look dead for 90s](research-background-jobs-need-setsid.md) — check nvidia-smi before relaunching; a sub-agent that returns does kill its job
- [/research is GPU-only by policy](research-marker-oom-when-unity-open.md) — never force CPU; gate each paper on free VRAM and retry when Unity holds the GPU
- [Subagents spin no-op Idle polls](subagents-spin-noop-idle-polls.md) — 205 `echo .` in 12 min spams the owner's terminal; brief them to wait on the subject, once

## Subsystem gotchas

- [Shadow direct-trace mode](shadow-direct-trace-mode.md) — the term IS the slab trace; bake and interleaved trace removed; also feeds the cull's near tier
- [VT composite determinism](vt-composite-determinism.md) — edit-mode frozen clocks, publication≠delivery, impure weights, unstable stamp sort; normalized-gradient slope convention
- [VT fill contract is three fields](vt-fill-contract-is-three-fields.md) — pending + resident + dirty mask publish together, or a driver inherits the last tick's leftovers
- [ShaderGraph custom target](shadergraph-custom-target-mechanics.md) — asmref into URP editor asm, displayName ordering trap, interpolator-skip handoff, CorePostgraph pitfall
- [Identifier sweeps: false positives](identifier-sweeps-false-positives.md) — a live parameter sharing a dead field's name; a code default overridden by scene data

## Test construction

- [Single-editor test runs](single-editor-test-runs.md) — one URP project per run, never six, never HDRP
- [Durable e2e, not editor QA](durable-e2e-not-editor-qa.md) — red-first in-suite gates with analytical oracles; never unity-cli screenshot QA
- [Verification representatives](verification-representatives-protocol.md) — real system vs constructed representatives / analytical primitives, SSIM or exact, then human-eye review
- [Gate must exercise worst-case regime](gate-must-exercise-worst-case-regime.md) — a proxy passes while the real regime stays broken; cross the code's branch boundary
- [Pin the orthogonal dimension](pin-orthogonal-dimension-in-fixtures.md) — adaptive/wall-clock features flake gates; pin via app config, never loosen the assertion
- [WaitAllRequests hides readback races](waitallrequests-hides-cross-frame-readback-races.md) — a red-first async-readback gate must fly without Settle's force-flush
- [Terrain fixture needs DepthOnly](terrain-fixture-needs-depthonly.md) — SSS receivers reconstruct from prepass depth; without the pass it reads lit, silently
- [VTContentView gradient oracles](vtcontentview-gradient-oracles.md) — readback point-load snapping: pure-sample oracles exact, finite-difference need a wide baseline or closed form
- [adb needs an unsandboxed shell](adb-needs-unsandboxed-shell.md) — a sandboxed adb spawns a rival daemon and kills the user's wireless pairing; USB absence ≠ disconnected
- [Unity native-crash forensics](unity-native-crash-forensics.md) — the log's stacktrace is the signal handler; ptrace is descendant-only so gdb must be the parent; small addr = failed allocation
- [Deck launcher + generation staleness](deck-benchmark-launcher-and-staleness.md) — args live in the Steam shortcut not -argv.json; check build/archive/scene are one generation before measuring
- [Deck verdict mislabels machine/resolution](deck-verdict-mislabels-machine-and-resolution.md) — a Deck run's verdict prints machine=PC, resolution=1920x1080; both wrong, read floor_ms=8.0 instead
- [ps aux lies about Unity runs](unity-run-liveness-ps-aux-lies.md) — zero reported while four batchmode runs contended; check lockfile/pgrep
- [Unity liveness: never pgrep -f](unity-liveness-never-pgrep-f.md) — the pattern matches the checking shell; use `unity-ps`
- [Teardown unloads the runner's scene](unity-teardown-unloads-runner-scene.md) — blanket scene-unload in UnityTearDown hangs PlayMode silently
- [Probe code goes in the package Tests tree](probe-code-belongs-in-package-test-tree.md) — scratch/ is outside every Unity compilation root, so no gate can inherit it
- [A settle waits on the subject, never a frame count](render-gate-settle-must-wait-on-subject.md) — a frozen terrain holds a stable WRONG frame for ~15 frames at pending==0
- [Pixel error is a player axis](pixel-error-is-a-player-axis.md) — baked artifacts serve the whole quality range; one-setting capture QA proves nothing
- [Binding assertions beat surface readback](binding-assertions-beat-surface-readback.md) — a wrong pool origin still lands in some painted slot; grade the MPB for addressing claims

