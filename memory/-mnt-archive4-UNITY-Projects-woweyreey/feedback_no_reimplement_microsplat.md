---
name: No reimplementing MicroSplat sampling
description: Never manually sample _Diffuse, _NormSAO, or other MicroSplat texture arrays — always call through MicroSplat's own SurfImpl/SampleSplats chain
type: feedback
originSessionId: 911998dd-79b4-423b-a0a7-fcc54669b2aa
---
Never re-implement parts of MicroSplat sampling (e.g. directly sampling _Diffuse or _NormSAO texture arrays). Always call through MicroSplat's own code path (SurfImpl, SampleSplats, Setup, etc.) and write a harness around it.

**Why:** MicroSplat's sampling includes anti-tiling, height blending, triplanar, clustering, and dozens of feature-dependent branches. Manual reimplementation is fragile, incomplete, and diverges from the real output.

**How to apply:** When writing fulfiller passes or alternate render paths for MicroSplat shaders, construct proper inputs (ShaderData, Input structs) and call SurfImpl. Only intercept at well-defined injection points (OnPostGeneration replacements, preprocessor branches) — never bypass the MicroSplat function chain.
