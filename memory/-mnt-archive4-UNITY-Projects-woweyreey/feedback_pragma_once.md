---
name: Use pragma once in HLSL
description: Prefer #pragma once over #ifndef/#define/#endif include guards in HLSL files
type: feedback
---

Use `#pragma once` instead of `#ifndef`/`#define`/`#endif` include guards in HLSL header files.

**Why:** Cleaner, less boilerplate, avoids stale guard name mismatches.

**How to apply:** When creating or refactoring `.hlsl` files, use `#pragma once` as the first line instead of the traditional include guard pattern.
