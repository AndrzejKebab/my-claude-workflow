---
name: Never edit Unity assets directly
description: Don't hand-edit .asset/.prefab/.unity YAML files — prompt the user to make changes in the Unity editor
type: feedback
originSessionId: 3ebaa41e-c0e5-4c11-8b63-e1941d7e8b07
---
Never try to edit Unity asset files (`.asset`, `.prefab`, `.unity`, `.preset`, etc.) directly.

**Why:** Unity serialized YAML has internal consistency requirements (feature maps, GUIDs, serialized references) that break when hand-edited. The editor is the only safe way to modify these.

**How to apply:** When a change requires modifying a Unity asset (e.g. adding a render feature to a URP renderer asset), tell the user what to do in the editor instead of editing the file.
