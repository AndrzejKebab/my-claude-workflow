---
name: JsTickSystemBase needs burst context
description: Any JS tick system that accesses ECS components must call UpdateBurstContext before ticking — without it GetEntityFromIdBurst returns Entity.Null silently
type: feedback
---

JsTickSystemBase must set up the burst context (ECB + transform lookup + script buffer lookup) before ticking, same as JsSystemRunner does. Without UpdateBurstContext, GetEntityFromIdBurst checks ctx.isValid → false → returns Entity.Null → bridge silently returns undefined.

**Why:** JsScriptFulfillmentSystem (InitializationSystemGroup) clears the burst context after init. FixedStepSimulationSystemGroup runs before JsSystemRunner (SimulationSystemGroup), so the burst context is invalid during fixedUpdate.

**How to apply:** Any new JS tick system must call UpdateBurstContext before ticking and UpdateAllLookups + CompleteDependency for job safety.
