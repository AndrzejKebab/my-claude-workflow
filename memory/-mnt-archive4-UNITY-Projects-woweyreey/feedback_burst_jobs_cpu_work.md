---
name: Burst jobs for CPU work
description: Move complicated CPU workloads (iteration, marshalling) into Burst-compiled IJob dispatched synchronously via Schedule().Complete()
type: feedback
---

Bring complicated CPU workloads into Burst-compiled jobs dispatched synchronously (`.Schedule().Complete()`).

**Why:** Non-Burst managed loops can be slow enough to cause editor hitches, and Burst compilation catches safety issues. User preference for consistent perf-aware code style.

**How to apply:** When writing CPU-side iteration (clear-cell computation, delta marshalling, sorting) in perf-critical systems like RWVT, wrap in `[BurstCompile] struct FooJob : IJob` and call `.Schedule().Complete()`. Don't leave raw managed loops in hot paths.
