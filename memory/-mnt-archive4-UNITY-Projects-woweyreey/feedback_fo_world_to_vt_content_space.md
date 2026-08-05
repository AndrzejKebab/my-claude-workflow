---
name: Floating Origin — RWVT content-space conversion
description: Any system sampling the heightfield RWVT (_Terrain_*) from a world-space raymarch must convert to content-space via `content = world - FloatingOrigin.Origin` (and reverse Y via `world_y = content_y + Origin.y` for the stored height). Getting the sign wrong silently passes on first shift (Origin=0) and diverges on every subsequent teleport.
type: feedback
originSessionId: d1810804-8008-4c47-99df-dd06f864c891
---
When a shader samples the heightfield RWVT (`_Terrain_WorldToUV`, `_Terrain_Height_Physical`, etc.) from a world-space ray (e.g. the HF distant-shadow bake raymarching along `-_DistantShadowSunDir` from `DistantShadowUVToWorld`), it MUST convert world-space positions to VT content-space before the `RWVTWorldToUV` call, and convert the returned stored height back to world-space.

**The conventions (authoritative: `HeightfieldTerrainController.cs:764` comment):**
```
contentPos = worldPos - FloatingOrigin.Origin    // VT lookup input
worldY     = contentY + FloatingOrigin.Origin.y  // returned terrain height
```

These are the right signs. The inverse signs (`world + Origin` / `content - Origin.y`) are the easy mistake — they type-check, sample-succeed, and silently work at `Origin=0` (before any FO teleport), so they look correct until the first shift.

**Why:** The VT's `_worldToUV` is built from `HeightfieldTerrainController.ContentBounds` (centered at 0, NOT `HeightfieldMeshRenderer.ContentBounds` which is centered at `FloatingOrigin.Origin`). World-space raymarch rays live in the basis `_WorldToDistantShadow` was built in, anchored to `cameraData.worldSpaceCameraPos` — i.e. Unity-space post-FO snap. `VTShadowController.cs:280-283` spells out the same identity from the opposite direction: "Shader worldPos = actualPos - FloatingOrigin, so actualPos = shaderWorldPos + FloatingOrigin" — where "actualPos" is what the VT wants and "shaderWorldPos" is what the ray gives you. But note the VT convention in `HeightfieldTerrainController.cs:764` is the CANONICAL version and reads `content = world - Origin`; don't blend the two derivations without care.

**How to apply:**
- Push `float4(FloatingOrigin.Origin, 0)` through PassData + `cmd.SetGlobalVector` inside the render func (not via `Material.SetVector` at record time — see `feedback_rendergraph_material_state_stomp`).
- In the shader, subtract `_HfShadowWorldOrigin.xyz` (or whatever you named it) before `RWVTWorldToUV`.
- If the VT stores a Y value you're comparing against the world-space ray's Y (e.g. `above = terrainY - samplePos.y`), add `Origin.y` to the returned value to lift it back into world-space.
- Verify by teleporting across the FO threshold (scene debug: drop `FloatingOrigin.threshold` to ~100) and confirm shadows stay spatially coherent across the shift, not just before it.

Applies to: HF shadow bake (done, `HeightfieldShadowBake.shader`), and any future system that raymarches against RWVT data from a world-space basis (SSS, custom GI, screen-space terrain AO, etc.).
