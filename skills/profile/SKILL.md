---
name: profile
description: Profile Unity projects and attribute CPU, memory, jobs, rendering, and ECS performance costs using repeatable captures.
---

# Unity profiling

Measure a specific performance question with a repeatable scenario. Do not optimize from code inspection alone, and do not compare captures made with different scenes, build settings, workloads, or profiler configurations.

## Establish the target

Before capturing, record:

- project path and Unity version from `ProjectSettings/ProjectVersion.txt`;
- Editor or Player, build configuration, platform, graphics API, and Burst/jobs safety settings;
- scene, camera position, world seed, warm-up duration, measured duration, and workload size;
- the symptom and metric being tested, such as frame time, a spike, allocation rate, memory growth, or job starvation.

Prefer a Development Player for representative CPU and rendering measurements. Use Editor captures for iteration and editor-only problems, but do not treat Editor timings as Player timings.

On Windows, resolve the matching editor with `unity editors path <version>` when the official Unity CLI is available. Otherwise use the configured editor installation root; this workflow defaults to `F:\Unity Editors\<version>\Editor\Unity.exe`. Do not assume a Linux/macOS path or infer the editor location from the Unity Hub application directory. The repository's `unity-editor` launcher already performs this resolution.

## Capture narrowly

Enable only the Profiler modules and call-stack options needed for the question because profiling itself has overhead. Warm up asset loading, shader compilation, Burst compilation, and world generation before the measured interval unless one of those is the subject.

Capture a baseline before changing code. For each candidate change, repeat the same scenario and retain enough frames to distinguish steady-state cost from isolated spikes. Prefer medians or distributions over one favorable frame.

Useful tools by question:

- Unity Profiler: frame timing, main thread, jobs, rendering, GC allocations, and counters.
- Profile Analyzer: compare frame ranges or two captures and find regressions hidden by frame variance.
- Memory Profiler: snapshots, retained objects, native allocations, fragmentation, and growth between equivalent checkpoints.
- Burst Inspector: generated code and vectorization for a known hot Burst job.
- Entities Systems window and system timing data: ECS update order and expensive systems.
- Frame Debugger or GPU tooling: draw calls, passes, uploads, overdraw, and GPU-bound work.

Do not enable Deep Profile for the primary benchmark. It changes execution substantially; use it only as a short diagnostic capture when ordinary samples cannot identify managed call paths.

## ECS voxel workloads

Separate the pipeline into independently measurable stages rather than reporting one total "voxel cost":

1. world/chunk selection and streaming;
2. voxel generation or edits;
3. meshing and collider generation;
4. entity creation and structural changes;
5. job scheduling, dependencies, and completion points;
6. mesh or buffer upload;
7. culling and rendering;
8. disposal, pooling, and memory reuse.

Check these common failure modes:

- forced synchronization through `Complete`, main-thread reads, or dependency mistakes;
- many tiny jobs whose scheduling overhead exceeds their work;
- heterogeneous work assigned in batches too large for effective work stealing;
- structural changes or command-buffer playback concentrated into spikes;
- temporary native allocations, buffer resizing, managed allocations, or failed pooling;
- false sharing or memory access that defeats Burst vectorization and cache locality;
- remeshing unchanged chunks, duplicate collider work, or redundant GPU uploads;
- performance scaling with visible chunks, edited chunks, voxel density, or triangle count differently than expected.

When testing batch sizes, keep the workload identical and compare worker utilization and total stage time. Uniform per-element work can tolerate moderate batches; heterogeneous chunk or mesh work often benefits from smaller batches.

## Report evidence

For every conclusion, report:

- capture conditions and the exact measured range;
- baseline and candidate values with units;
- the responsible marker, system, job, allocation, render pass, or synchronization point;
- whether the result is CPU-bound, GPU-bound, memory-bound, scheduling-bound, or inconclusive;
- capture limitations and the next discriminating measurement.

Save profiler captures outside source-controlled project assets unless the user explicitly wants benchmark artifacts committed. Do not add custom build entry points or instrumentation to a project unless the task authorizes code changes.

## Important caveat

Avoid `-nographics` when the scenario imports, creates, or measures GPU resources. Headless graphics behavior can invalidate RenderTexture, shader, rendering, and GPU measurements. For CPU-only automation, confirm the behavior with the Unity version and target platform instead of treating this as a universal ban.
