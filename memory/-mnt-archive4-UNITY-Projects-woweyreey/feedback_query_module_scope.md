---
name: ecs.query() must be at module scope, never inside onUpdate/onTick
description: JS queries must be built once at module scope — never lazily initialized inside tick functions. Lazy init is wrong for performance and architecture.
type: feedback
---

ecs.query().withAll(...).build() must always be at module scope (top of the file), never inside onUpdate or onTick.
**Why:** Lazy initialization inside the tick function rebuilds the query object on every call. The query builder creates JS objects each invocation. Module-scope initialization runs once at load time — the correct pattern.
**How to apply:** When writing or modifying any .ts system/component script, always place `const myQuery = query().withAll(...).build()` at the top level of the module, outside any function.
