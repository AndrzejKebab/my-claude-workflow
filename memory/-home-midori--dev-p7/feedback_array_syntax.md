---
name: Use [] syntax over Array<T>
description: ESLint enforces [] array type syntax instead of Array<T> generic syntax in p7 codebase
type: feedback
---

Use `T[]` instead of `Array<T>` for type annotations.

**Why:** The p7 ESLint config has `@typescript-eslint/ban-types` rule that flags `Array` as a type. Using `Array<...>` causes a lint error.

**How to apply:** When writing TypeScript types, always use `{ foo: string }[]` instead of `Array<{ foo: string }>`.
