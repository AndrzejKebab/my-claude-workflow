---
name: Atmospherics has no Burst payback on current Deck profile
description: Burst/Jobs conversion of atmospherics record paths buys nothing — every record marker is sub-millisecond, residual GC lives in RG infrastructure
type: feedback
originSessionId: f0d244e6-6ca9-4d5c-aff5-4f00ddac6ba1
---
Atmospherics package (`Packages/is.zori.atmospherics`) is **not a Burst opportunity** on the current Steam Deck profile. Do not propose Burst conversion of fog gather, GI grid build, sky frame data, or cloud dispatcher paths without a fresh Deck profile that contradicts this.

**Why:** Profile `Builds/Linux/Profiles/profile_2026-05-07_23-27-16.raw` (post GC throttle fix, 2000 frames) shows:
- `Atmospherics.Fog.Record`: 0.147 ms self CPU/frame, 4.2 KB GC/frame
- `Atmospherics.GI.Record`: 0.0095 ms, 0 KB (steady-state; 12 MB once on EnsureResources)
- `Atmospherics.Sky.Record`: 0.040 ms, 47 B
- `Atmospherics.Clouds.Record`: 0.035 ms, 156 B
- `Atmospherics.DistantFog.Record`: 0.013 ms, 0 KB

Total atmospherics record CPU is ~0.24 ms/frame — 1.5% of the 16.6 ms 60-FPS budget. Even zeroing it cannot move Deck p95 (=20.6 ms in that profile).

The post-rewrite Drobot z-bin gather (`VolumetricFogPass.GatherAndZBinVolumes`) was confirmed cold via the `Atmospherics.Fog.Record.GatherAndZBin` sub-marker (`profile_2026-05-08_06-34-12.raw`): **0.15 KB GC/frame, 0.049 ms CPU/frame** — only 3.6% of the parent Fog.Record GC. The remaining ~4 KB/frame in Fog.Record lives in Render Graph bookkeeping (`builder.UseTexture`, `ImportTexture`, `AddUnsafePass`, `SetGlobalTextureAfterPass`) and BakeData population in the surrounding `RecordRenderGraph` body — not user-fixable without restructuring RG.

The previous audit's "RealtimeGIPass = prime suspect for 4 KB/frame" hypothesis was wrong. The flagged `new int[]/uint3[]/uint[]` allocations in `RealtimeGIPass.EnsureResources` only run on grid-resize, not per frame. Per-frame GI.Record GC on Deck is 0 bytes.

**How to apply:**
- Reject Burst-conversion proposals for any atmospherics record path until a Deck profile shows >1 ms CPU/frame in a marker.
- Do NOT add `UnityObjectRef<T>` to the package — no consumer warrants it. Wait until a Burst job actually needs it.
- The dominant CPU hotspot in user code on this profile is `Quadtree.Subdivide` (0.55 ms avg, 2 calls/frame) — terrain LOD, separate workstream.
- Full reinvestigation: `docs/atmospherics-burst-analysis.md`. Re-anchor against a fresh Deck capture if scenes get denser (≫32 fog volumes, larger GI grid).
