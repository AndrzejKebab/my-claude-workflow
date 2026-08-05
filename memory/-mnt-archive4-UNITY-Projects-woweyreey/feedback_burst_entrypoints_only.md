---
name: Burst entrypoints vs inlined methods
description: "[BurstCompile] attribute only goes on entry points — helper methods get auto-compiled when called from Burst context, and CAN return/accept structs by value"
type: feedback
---

`[BurstCompile]` attribute must only be placed on entry points (ISystem, IJobEntity, static methods meant to be called via function pointers). Helper/utility methods called FROM Burst-compiled code are automatically Burst-compiled without the attribute.

**Why:** `[BurstCompile]` on a method enforces Burst's entry-point calling convention, which forbids struct return values and struct arguments (only refs/outs allowed). But methods without the attribute that are reachable from Burst context get inlined/compiled by Burst automatically, and CAN freely return and accept structs by value.

**How to apply:** Never put `[BurstCompile]` on utility functions like packers, helpers, or static methods that are only called from within Burst jobs/systems. They'll be compiled by Burst anyway and can use normal C# signatures with struct returns.
