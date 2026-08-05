---
name: naadf-getraydir-monogame-conventions
description: "NAADF's HLSL getRayDir bakes in 3 MonoGame conventions that silently break on every non-MonoGame port target (WebGPU, Silk.NET, Bevy — Unity next)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2fb32083-ec99-43c8-a26a-d2dfbd3951f6
---

NAADF's renderer (`getRayDir` in `commonRenderPipeline.fxh`, fed by `Camera.cs`'s `invViewProjTransform`) bakes in three MonoGame/HLSL/D3D conventions that are invisible in the original but silently produce broken perspective on any other graphics stack — the symptom is "scene distributed around a point, barely responds to camera rotation, inverts when the camera moves":

1. **Origin-based (translation-free) view matrix.** NAADF builds `invCamMatrix` from `CreateLookAt(Vector3.Zero, camDir, Up)` — rotation only, no camera translation. `getRayDir` therefore treats the unprojected vector as a pure *direction*; the ray *origin* is supplied separately (the int+frac `PositionSplit`). Targets that hand `getRayDir` a full translated view-proj inverse leak the camera position into the ray direction.
2. **Standard-Z projection.** MonoGame `CreatePerspectiveFieldOfView` is standard-Z (near→NDC z=0, far→z=1). Bevy/wgpu default to reverse-Z (`perspective_infinite_reverse_rh`, near→z=1). `getRayDir`'s hardcoded `ndc.z=1` means different things per target.
3. **Row-major `mul(rowVec, matrix)`.** HLSL `mul(v, M)` on a row-major MonoGame matrix; column-major stacks (glam/WGSL) need `M * v` plus the perspective `w`-divide that NAADF skips (it gets away with skipping it only because its matrix is translation-free).

The user has hit this exact class of bug porting NAADF to WebGPU, C#/Silk.NET, and Bevy. The three bugs compound. Full diagnosis + the Bevy fix: `docs/orchestrate/naadf-bevy-port/05-review.md` (2026-05-14).

**Why:** the bugs are invisible in the MonoGame original — they only surface as broken perspective on a port, and because they compound, a partial fix still looks wrong. Easy to burn a day re-diagnosing from scratch on each new target.
**How to apply:** when porting NAADF's renderer to a new target (Unity is the next one the user expects), audit `getRayDir` + the camera-matrix upload against the target's conventions FIRST — handedness, Z-direction, matrix majorness / multiply order — and confirm the view matrix fed to the unprojection is rotation-only with the origin supplied separately. Unity is left-handed (vs MonoGame and Bevy both right-handed), so expect a handedness flip on top of the three issues above; verify Unity's depth convention per target platform rather than assuming.
