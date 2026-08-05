---
name: Serialized field types follow code types (no legacy compat)
description: When modernising to Unity.Mathematics, convert serialized field types too (Vector3 → float3, etc.). Don't preserve the legacy serialized shape for .asset/.prefab compatibility — matches the project-wide "no legacy" rule.
type: feedback
originSessionId: 60fb3067-7f45-4e65-9083-e5b990f27c43
---
During the atmospherics + heightfields Unity.Mathematics modernisation, the user explicitly instructed: change serialized field types too. Do NOT leave `[SerializeField] Vector3` fields as Vector3 "for compatibility" when the rest of the file is `float3`.

**Rule:** Serialized fields (`[SerializeField]`, `public` fields on `MonoBehaviour` / `ScriptableObject` / `[Serializable] struct`) follow the in-code type. If the code uses `float3`, the field is `float3`. Existing `.asset` / `.prefab` files that reference these fields will break — that is expected and accepted.

This matches the project-wide rule in `feedback_no_legacy.md`: no backwards-compat shims for data on disk.

**Why:** Unity.Mathematics types are `[Serializable]`, work in the inspector, and have `x`/`y`/`z`/`w` fields that match Unity's Vector* layout on disk in most cases. The risk of disk-format drift is real but explicitly accepted — we rebuild assets rather than preserve stale shapes. The alternative (keep Vector3 field, convert to float3 at read sites) spreads boilerplate across every caller and defeats the readability gain of modernisation.

**How to apply:** When converting a file, change every `[SerializeField] Vector3 foo` to `[SerializeField] float3 foo`. Don't create intermediate wrapper properties. Don't worry about `.asset` migration — if an asset breaks, either rebuild it or edit the YAML by hand.
