---
name: URP6P3 shader deleted
description: HeightfieldTerrain_URP6P3.shader was a debugging leftover and has been deleted — only the .surfshader matters
type: feedback
originSessionId: 750d3b46-b0a7-42a5-9157-d3e7e398e3ec
---
HeightfieldTerrain_URP6P3.shader was a leftover from previous debugging and has been deleted. The standalone shader path is only HeightfieldTerrain.surfshader (Better Shaders format). Do not reference or modify the URP6P3 file.

**Why:** User deleted the generated shader — Better Shaders regenerates it at compile time from the .surfshader source.
**How to apply:** Only edit .surfshader files for the standalone heightfield path, never manually edit generated .shader files.
