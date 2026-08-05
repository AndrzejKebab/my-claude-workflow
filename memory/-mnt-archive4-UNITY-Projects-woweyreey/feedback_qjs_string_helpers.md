---
name: Use QJS.ToManagedString / QJS.GetStringProperty
description: Always use QJS helper methods instead of raw ToCString→PtrToStringUTF8→FreeCString pattern
type: feedback
---

Use `QJS.ToManagedString(ctx, val)` and `QJS.GetStringProperty(ctx, obj, propName)` instead of ad-hoc `JS_ToCString` → `Marshal.PtrToStringUTF8` → `JS_FreeCString` sequences.

**Why:** The 3-line unsafe pattern is duplicated across ~15 callsites in Packages/unity.js/Runtime/ and is error-prone (forgetting to free, null checks). The helpers in `QJS.cs` (lines ~300-330) handle null pointers, freeing, and intermediate JSValue cleanup.

**How to apply:** When touching any code that reads a string from a JSValue or a string property from a JS object, use the helpers. Migrate existing callsites opportunistically when editing those files.
