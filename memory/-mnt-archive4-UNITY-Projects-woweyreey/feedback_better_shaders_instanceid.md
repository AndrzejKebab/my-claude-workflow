---
name: Better Shaders instanceID access pattern
description: How to access SV_InstanceID in Better Shaders surfshader ModifyVertex — use v.instanceID guarded by UNITY_ANY_INSTANCING_ENABLED
type: feedback
---

In Better Shaders .surfshader `ModifyVertex(inout VertexData v, inout ExtraV2F d)`, access instance ID via `v.instanceID` (from `UNITY_VERTEX_INPUT_INSTANCE_ID` in VertexData struct), NOT `unity_InstanceID`.

**Why:** `unity_InstanceID` is only set after `UNITY_SETUP_INSTANCE_ID()` which is called in the template Vert() before ChainModifyVertex, but only exists when instancing keywords are active. The VertexData member `v.instanceID` maps to `SV_InstanceID` directly.

**How to apply:** Guard with `#if UNITY_ANY_INSTANCING_ENABLED` and default to 0:
```hlsl
uint instanceID = 0;
#if UNITY_ANY_INSTANCING_ENABLED
instanceID = v.instanceID;
#endif
```
