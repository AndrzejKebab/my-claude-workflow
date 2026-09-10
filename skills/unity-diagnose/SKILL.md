---
name: unity-diagnose
description: Disciplined diagnosis loop for hard Unity bugs and performance regressions — build an agent-runnable feedback loop (EditMode test, batchmode run, scratch ECS World, replay harness), then reproduce → hypothesise → instrument → fix → regression-test. Use when the user says "diagnose this" / "debug this", reports a Unity bug, says something is broken/throwing/failing/NaN/flickering, describes editor-vs-build divergence, or reports a frame-time or GC regression.
---

# Unity Diagnose

A discipline for hard bugs. Skip phases only when explicitly justified.

When exploring the codebase, use the project's domain glossary (CONTEXT.md) to get a clear mental model of the relevant modules, and check ADRs in the area you're touching. Also note the paradigm of the buggy area — MonoBehaviour, ECS/DOTS, or hybrid — because it decides which feedback loops are even available.

## Phase 1 — Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a fast, deterministic, agent-runnable pass/fail signal for the bug, you will find the cause — bisection, hypothesis-testing, and instrumentation all just consume that signal. Without one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.** In Unity the gravity well is "enter play mode and eyeball it" — resist it; that loop is slow, human-gated, and non-deterministic. Climb down this ladder only as far as you must:

1. **EditMode test** at whatever seam reaches the bug — engine-free logic, Burst static functions called directly, editor tooling code. Milliseconds, fully deterministic, agent-runnable. Always ask first: *can the buggy logic be reached without the player loop?*
2. **Scratch ECS World harness** (ECS projects). EditMode test that creates a `World`, inserts entities with the input components, updates the suspect system(s), asserts on output components. No scene, no subscene streaming, no frame pump.
3. **PlayMode test** when the loop itself is implicated — physics steps, lifecycle order, coroutine/UniTask timing, subscene load.
4. **Batchmode CLI run** — `Unity -batchmode -runTests` or `-executeMethod` on a repro method that prints a parseable verdict and exits nonzero on failure (template: `scripts/BatchmodeRepro.template.cs`). This is how a test or repro becomes agent-runnable without the editor UI. Slow to boot (~tens of seconds) but fully unattended — cache a warm editor with `-quit`-less runs only if boot cost dominates.
5. **Replay a captured artifact.** Save the real thing that triggers the bug — a save file, a chunk/region blob, a recorded input stream, a netcode command log, the exact def/JSONC data — and replay it through the code path in an EditMode or batchmode harness. Real data beats synthetic repros for serialization and world-gen bugs.
6. **Throwaway repro scene/harness** under `Assets/_Prototypes/` rules: minimal scene, one MenuItem to run, verdict printed to the log with a greppable tag.
7. **Bisection harness.** Bug appeared between two known states? Automate "checkout, batchmode run, report" and `git bisect run` it. Unity adds non-git axes worth bisecting too: **scene bisection** (delete half the objects, re-test), **asset bisection**, package-version bisection.
8. **Differential loop.** Same input, two configurations, diff outputs. Unity's config axes are diagnostic gold: **Burst on vs off**, **jobs parallel vs `JobWorkerCount = 0`**, **safety checks on vs off**, Mono vs IL2CPP, editor vs development build, domain-reload on vs off. A bug that vanishes when Burst is off or jobs are single-threaded has just told you its category.
9. **HITL script.** Last resort, for device-only or feel-dependent bugs. If a human must click, drive *them* with `scripts/hitl-loop.template.sh` so the loop is still structured and the output feeds back to you.

Build the right feedback loop, and the bug is 90% fixed.

### Iterate on the loop itself

Treat the loop as a product:

- **Faster?** EditMode over PlayMode; skip domain reload (Enter Play Mode settings) while iterating; narrow the test filter; reuse a warm editor for batchmode.
- **Sharper?** Assert the specific symptom — the NaN, the wrong voxel, the dropped command — not "didn't throw".
- **More deterministic?** Seed every `Random` (`Unity.Mathematics.Random` with fixed seed), pin dt (`Time.captureDeltaTime` or pass dt explicitly), force `JobWorkerCount = 0` to serialize job execution, disable frame-rate-dependent code paths, isolate the filesystem, fake time instead of waiting it.

A 30-second flaky loop is barely better than no loop. A 2-second deterministic loop is a debugging superpower.

### Non-deterministic bugs

Goal: **higher reproduction rate**, not immediate cleanliness. Loop the trigger 100× in one process, add stress (entity counts, chunk churn), shrink or widen timing windows, inject frame-length jitter, run jobs single-threaded *and* over-parallelised. Race-shaped bugs in jobs often flip from 1% to 100% when safety checks and leak detection (full stack traces) are enabled — turn those on before anything else.

### When you genuinely cannot build a loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) the environment that reproduces it (device build, specific hardware, their editor with their scene open), (b) a captured artifact — `Player.log`/`Editor.log`, a profiler capture (`.raw`), a memory snapshot, a save file, a video with timestamps, or (c) permission to add temporary tagged instrumentation to a build they run. Do **not** proceed to hypothesise without a loop.

## Phase 2 — Reproduce

Run the loop. Watch the bug appear.

- [ ] The loop produces the failure mode **the user described** — not a nearby different failure. Wrong bug = wrong fix.
- [ ] Reproducible across runs (or at a rate high enough to debug against).
- [ ] The exact symptom is captured (error + stack, wrong output values, frame timing) so later phases can verify the fix addresses *it*.
- [ ] Reproduced in the environment that matters: an editor-only repro does not confirm a build-only bug (IL2CPP stripping, serialization differences, `#if UNITY_EDITOR` divergence). If the report is from a build, the loop must eventually run against a development build.

Do not proceed until you reproduce the bug.

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any. Single-hypothesis generation anchors on the first plausible idea. Alongside domain logic, weigh Unity's recurring suspects — but only the ones that exist in the buggy area's paradigm:

- **Any paradigm**: serialization surprises (what Unity does and doesn't serialize), stale editor state a Reimport/Library-delete would clear, editor-vs-build divergence (`#if UNITY_EDITOR`, IL2CPP stripping), frame-rate/dt-dependent logic, asset import order.
- **MonoBehaviour/OO**: lifecycle and execution order (`Awake`/`OnEnable`/`Start`, script execution order), `OnValidate` timing, destroyed-but-not-null objects, event subscriptions outliving their targets, coroutine lifetime tied to the wrong object, hidden state in statics/singletons surviving domain-reload-off.
- **ECS/DOTS/jobs**: data races and missing job dependencies, unintended sync points and structural changes mid-frame, system update order, stale `ComponentLookup`s, Burst-specific behaviour (float math, uninitialized memory, aliasing), entity remapping across serialization or netcode.
- **Hybrid**: staleness at the managed↔ECS handoff — copies made at the wrong time, one side mutating while the other reads.

Each hypothesis must be **falsifiable**:

> "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

If you can't state the prediction, it's a vibe — discard or sharpen. The differential axes from Phase 1 (Burst off, jobs serial, safety checks on) are prediction machines: most good Unity hypotheses map to one.

**Show the ranked list to the user before testing.** They often re-rank instantly ("that system changed yesterday") or have already ruled some out. Don't block on it — proceed with your ranking if the user is AFK.

## Phase 4 — Instrument

Each probe maps to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger** (Rider/VS attach) — for MonoBehaviour/managed code this just works and one breakpoint beats ten logs; make it the default there. **Burst-compiled code won't hit managed breakpoints**: either disable Burst for that assembly while probing (and confirm the bug survives — if it doesn't, that *is* the finding) or probe with logs. For parallel jobs, breakpoints also serialize reality — set `JobWorkerCount = 0` first so what you step through is what actually runs.
2. **Targeted logs** at the boundaries that distinguish hypotheses. `Debug.Log` works inside Burst with fixed-string/interpolation limits; `[BurstDiscard]` methods let you run rich managed probes from bursted code without disabling it.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup becomes a single grep. Untagged logs survive; tagged logs die. Same tag goes on any temporary MenuItems, debug scenes, or gizmo drawers.

**Perf branch.** For frame-time or GC regressions, logs are the wrong instrument. Baseline first, fix second:

- Measure in a **development build**, not the editor — editor overhead and leak-detection settings lie.
- `ProfilerMarker`s around suspects; capture with the Profiler; diff against the baseline capture. Rendering issues → Frame Debugger; memory → Memory Profiler snapshots, allocation call stacks for GC spikes.
- For job-heavy code, read the timeline view: bubbles, sync points (`Complete()` calls, structural changes), and worker starvation are usually visible before any code is read.
- Bisect with the measurement as the signal, exactly like a correctness bug.

## Phase 5 — Fix + regression test

Write the regression test **before the fix** — but only at a **correct seam**.

A correct seam exercises the real bug pattern as it occurred: right data, right ordering, right concurrency. A unit test that can't replicate the triggering chain (single-threaded test for a race, synthetic data for a serialization bug, EditMode test for a lifecycle-order bug) gives false confidence.

**If no correct seam exists, that itself is the finding.** Usually it means logic is trapped behind the engine with no humble shell, or a system has no component-data contract to assert on. Note it and flag it for Phase 6.

If a correct seam exists:

1. Turn the minimised repro into a failing test there — EditMode if the seam allows, PlayMode only if the loop is genuinely part of the pattern.
2. Watch it fail. 3. Apply the fix. 4. Watch it pass.
5. Re-run the Phase 1 loop against the original, un-minimised scenario — including the original environment (build, not just editor) if that's where it was reported.

## Phase 6 — Cleanup + post-mortem

Required before declaring done:

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes (or the absence of a seam is documented)
- [ ] All `[DEBUG-...]` instrumentation removed — grep the prefix across code, MenuItems, and scenes
- [ ] Settings restored: Burst re-enabled, `JobWorkerCount` reset, safety-check/leak-detection levels back to normal, Enter Play Mode settings reverted
- [ ] Throwaway repro scenes/harnesses deleted (or moved under `Assets/_Prototypes/` with a NOTES.md)
- [ ] The winning hypothesis stated in the commit/PR message — the next debugger learns

**Then ask: what would have prevented this bug?** If the answer is architectural — no good test seam, logic locked inside the engine, a system with no data contract, hidden coupling through inspector wiring or statics — hand off to the `/unity-refactor` skill with the specifics. Make that recommendation **after** the fix is in, not before: you have more information now than when you started.
