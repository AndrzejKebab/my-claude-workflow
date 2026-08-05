---
name: unity-6000-7-getinstanceid-drift
description: Unity 6000.7 alpha breaks GetInstanceID/EntityId; how to fix vendored packs
metadata: 
  node_type: memory
  type: project
  originSessionId: b8548c87-ac1c-41e0-84f8-900c6caa9297
---

On Unity **6000.7.0a1** (this project's editor), `Object.GetInstanceID()` is
obsolete-as-error (CS0619). The replacement is `GetEntityId()` returning
`EntityId`, but the obvious swaps all fail too:

- `(uint)EntityId` → CS0030 (EntityId is no longer an int)
- `EntityId`'s implicit `int` operator is itself obsolete (CS0619)
- `EntityId.Index` / `.Version` exist but are internal to Unity modules → CS1061 from user code

**Working fix:** `obj.GetEntityId().GetHashCode()` — a genuine public,
non-obsolete `int`. Cast `(uint)` if a uint was wanted.

Applied to vendored MudBun (`Assets/MudBun/Script/MudRendererBase.cs`). Other
vendored asset packs (`Assets/_Fabs/**`, AmplifyShaderEditor, FImpossible) may
hit the same alpha drift — also seen: `PhysicMaterial`→`PhysicsMaterial`,
`TreeViewItem`→`TreeViewItem<int>`, UxmlTraits/UxmlFactory removal.

Verify any fix with batchmode: `unity . -batchmode -quit -logFile -` (editor
must be closed — single project, shared `Temp/UnityLockfile`).
