---
name: Don't chase GUIDs or scene references
description: Never investigate GUIDs, hunt scene/prefab references, or attempt to edit scenes for orphan/missing-script cleanup — Unity auto-updates GUID references; just flag it for manual verification.
type: feedback
originSessionId: f9ee5476-9802-4095-af11-ed96c82da3d7
---
Never investigate GUIDs in `.meta` files, never grep scenes/prefabs for fileID/GUID references, never try to edit `.unity`/`.prefab`/`.asset` files to fix orphan or missing-script entries.

**Why:** Unity auto-updates GUID references in scenes and assets — it's never actually a problem. Time spent chasing GUID/scene-ref linkages is pure waste, and editing scene YAML by hand is dangerous.

**How to apply:** When deleting a script that may be referenced from a scene/prefab, or when finding a missing-script reference: just mention "scripts/references may need manual update" in the report. Do not attempt to enumerate, locate, or fix the references. Do not grep for GUIDs. Do not read scene YAML to inventory orphans. The user handles cleanup in the editor.

Reinforced 2026-05-05 during the FloatingOrigin rework — orchestrator was hunting GUIDs and scene fileIDs after deleting three classes, instead of just noting "scripts deleted, scene refs may show as missing — handle in editor if needed".
