---
name: Unity safe mode popup on compile errors
description: Unity shows a blocking safe mode UI popup on startup if compile errors exist — cannot be dismissed programmatically
type: feedback
---

If Unity detects compilation errors during startup, it shows a "safe mode" UI popup requiring manual user interaction. This blocks the editor from loading.

**Why:** Launching Unity with known compile errors wastes time — the editor won't become usable without user clicking through the popup.

**How to apply:** Before killing+relaunching Unity (e.g., after native .so rebuild), ensure C# compiles cleanly first. If unsure, warn the user that compile errors may trigger the safe mode popup.
