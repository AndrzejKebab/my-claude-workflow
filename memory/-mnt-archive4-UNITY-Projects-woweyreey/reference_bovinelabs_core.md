---
name: bovinelabs.core native collections
description: Reference to com.bovinelabs.core repo for Burst-compatible NativeContainers and ISystem patterns — copy and adapt, don't add as dependency
type: reference
---

Repository: https://github.com/tertle/com.bovinelabs.core

Key files:
- `BovineLabs.Core/Collections/BitArray.cs` — native bit array
- `BovineLabs.Core/Collections/NativeKeyedMap.cs` — native keyed map (like Dictionary but unmanaged)

Use case: when we need Dictionary/List equivalents that are fully unmanaged and Burst-compatible.
Pattern: copy and adapt the source into our codebase rather than adding a package dependency.
