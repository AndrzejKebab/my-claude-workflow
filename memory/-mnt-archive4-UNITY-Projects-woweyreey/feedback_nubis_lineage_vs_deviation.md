---
name: Nubis lineage primitives are canonical-replace, not deviation-cut
description: HG, beer-powder, in-scatter probability are all canonical across HZD 2015 → Nubis-Decima 2017 → NC23 2023 — classifying them as deviations is wrong
type: feedback
originSessionId: 18453239-4b64-4a12-ac7d-fa95ffc07a9c
---
When classifying cloud-lighting code for rewrite, distinguish **canonical Nubis primitives** (across the lineage HZD 2015 → Nubis-Decima 2017 → NC23 2023) from **deviations** (stuff we added that isn't in any Nubis slide).

**Canonical Nubis lineage** (classify as `canonical-replace` when superseded by a newer Nubis evolution, NOT `deviation-cut`):
- Henyey-Greenstein phase function (HZD 2015 p.55–57, Nubis-Decima 2017). NC23 p.136 substitutes its role with `Remap(sun_dot, 0, 0.9, 0.25, ValueRemap(cloud_distance, …))` but HG itself is canonical.
- Beer-powder: HZD 2015 sum form → Nubis-Decima 2017 `max(exp(-d), exp(-d*0.25)*0.7)` → NC23 2023 product form `dimensional_profile × exp(-summed_sun × remap)`. Structure persists; form changes.
- In-scatter probability (`depth_probability × vertical_probability` — Nubis-Decima 2017 p.89–92). NC23 supersedes with `cloud_distance` (SDF-driven depth) + `dimensional_profile` (vertical profile channel).
- Cone-march to sun (HZD 2015 p.85). NC23 supersedes with precomputed sun-summed-density LUT.

**True deviations** (we added; not in any Nubis slide — classify as `deviation-cut` unless kept as artistic knob):
- Oz-2013 multi-scatter octaves loop (`_Ms*` uniforms).
- Silver-lining (`_SilverIntensity`, `_SilverExponent`). **Keep as cheap artistic control** per user decision 2026-04-22 ("cheap thing to keep which gives us some artistic control") — classify as `deviation-keep-as-art-control` and layer additively on top of the NC23 direct term.

**Why:** User corrected multiple mis-classifications in one planning session. Calling canonical Nubis primitives "deviations" implies they shouldn't exist in any code path, when in reality they're canonical lineage — the NC23 rewrite supersedes their implementation, not their conceptual role.

**How to apply:** In any plan that rewrites cloud lighting, open `docs/research/horizon-zd-clouds.md` and `docs/research/nubis-decima.md` alongside `docs/research/nubis-cubed-2023.md` and trace each primitive through the lineage before labelling it. If a primitive has a direct ancestor in HZD 2015 or Nubis-Decima 2017, it's `canonical-replace`. If it's from Wrenninge / Oz / Schneider-pre-Nubis or we invented it, it's `deviation-cut` (or `deviation-keep-as-art-control` if user confirms artistic value).
