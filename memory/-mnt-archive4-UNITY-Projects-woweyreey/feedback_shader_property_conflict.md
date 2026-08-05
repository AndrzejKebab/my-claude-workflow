---
name: Shader property type conflict requires Unity restart
description: Unity "Property already exists with different type" error can only be fixed by restarting Unity, not by clearing shader cache
type: feedback
---

"Property already exists with different type" in Unity is a runtime shader property registry issue. Clearing Library/ShaderCache does NOT fix it — only restarting Unity resolves it.

**Why:** The shader property registry is populated at runtime and persists in memory. Cache files are irrelevant once the registry is loaded.

**How to apply:** When changing a shader property type (e.g., StructuredBuffer → Texture2D), always plan for a Unity restart as part of the migration. Don't suggest cache clearing as a fix.
