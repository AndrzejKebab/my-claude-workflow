---
name: Quality tiers hold raymarch steps constant
description: Visual-test quality tiers must vary only subres/accumulation; raymarch step count is a separate axis and must stay fixed across tiers
type: feedback
originSessionId: 08c53ac2-4be3-4db9-bad5-2dc4fd84850a
---
When designing quality tiers (e.g. Low/Medium/High) for volumetric/raymarched
rendering tests, hold raymarch step count **constant** across all tiers. Vary
only the axes the tier is meant to isolate — for clouds that's subresolution
and accumulation frames.

**Why:** Step count dominates the image (energy absorption, feature contrast,
silhouette darkness). Bundling step count into the tier preset makes tier-to-
tier diffs mostly about steps, not the axes you're actually testing, and
visually the tiers look like different scenes rather than different qualities
of the same scene. This was a direct correction on the volumetric-clouds
test suite: original bundled tiers (32/64/128 steps) produced "vastly
different" images and had to be flattened to a fixed 48 across all tiers.

**How to apply:** When writing a test matrix for a raymarched effect:
- Pick one step count for the whole suite (a single `FixedRayMarchSteps` const)
- Tiers vary only the subres/acc/resolution knobs
- For per-tier perceptual reference captures, match that same fixed step count
- If steps need to be tested as an axis, make them a separate matrix dimension,
  don't hide them inside tier definitions
