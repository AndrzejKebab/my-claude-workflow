---
name: Visual blend modes are artistic, not a perf tier axis
description: Distinct-look blend enums (cascade-vs-ring, light-add-vs-min, etc.) stay on artist settings — never fold into QualityLocked tier specs
type: feedback
originSessionId: c0a5115d-78c3-488c-8e79-0221b77f09a5
---
Blend-mode enums that drive a **distinct visual look** belong on artist-facing settings (`*Settings`), not quality-tier specs (`*QualitySpec`). Quality tiers govern perf knobs (resolution, step counts, accumulation factors); blend modes pick which look you ship.

**Why:** User correction principle — "shadowBlend — that has nothing to do with quality — purely artistic control." Even when a blend mode has measurable perf cost (e.g. cascade-multiply samples the shadow atlas per froxel), the cost difference is usually small enough that the *look* matters more than the tier. Folding artistic choice into `[QualityLocked]` strips the artist's ability to tune across platforms.

**How to apply:**
- New blend-mode enum → put it on `*Settings`, leave it artist-tunable.
- Do NOT add `[QualityLocked]` to blend-mode fields.
- Do NOT drive blend modes from `*QualitySpec` per-tier values.
- Default the principle to "artistic unless proven a tier axis."

**Historical context:** This rule originated with `VolumetricFogSettings.mainLightShadowBlend` (`DistantShadowCascadeBlend` enum). That specific field was deleted in the 2026-05-03 Bauer-canonical fog rework — fog no longer samples cascade per-froxel. The principle survives for future blend-mode additions; the canonical reference example is now the deferred ShadowSample fog volume contributor's blend-mode field (when implemented).
