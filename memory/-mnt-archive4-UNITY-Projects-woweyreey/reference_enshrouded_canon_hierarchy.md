---
name: Enshrouded canon hierarchy — Krause 2025 ships, Feller 2024 is postmortem
description: Krause 2025 (`krause-2025-*.md`) is the canonical shipped Enshrouded volumetric-fog methodology. Feller 2024 GPC (`feller-2024-volumetric-fog-enshrouded.md`) is a postmortem of unshipped exploration — historical context, NOT primary canon for "what we should implement".
type: reference
originSessionId: 22de7076-3343-4170-bc2f-7a5c4f1ee32e
---
When citing Enshrouded canon for foundational volumetric work:

- **Primary anchor: Krause 2025** — `docs/research/krause-2025-enshrouded-volumetric-fog.md` and `docs/research/krause-2025-enshrouded-volumetrics-talk.md`. These describe the actual shipped Enshrouded fog system (atlas formats, page-table architecture, raymarch inner loop, density erosion at sl. 56, etc.). Anchor verbatim quotes for atlas formats / pipeline ordering / parameters here.

- **Secondary cross-reference: Schneider Nubis Cubed 2023** — `docs/research/schneider-2023-nubis-cubed.md`. Source for Alligator noise lineage (the noise primitive used in detail-modulation), raymarch-inner-loop noise integration patterns. Enshrouded Krause 2025 inherits from this lineage.

- **Tertiary / historical: Feller 2024 GPC** — `docs/research/feller-2024-volumetric-fog-enshrouded.md`. Postmortem of two earlier attempts (one abandoned, one earlier-shipped iteration). Where Feller 2024 conflicts with Krause 2025 (e.g. noise-position-offset for god-ray detail vs density-domain erosion at sample time), **Krause 2025 wins**. Useful for understanding how the team got there but NOT load-bearing for current implementation.

Concrete example of where this hierarchy matters: Phase 6 of `is.zori.volumetrics` (density-domain erosion per Krause 2025 sl. 56) directly contradicts Feller 2024's sl. 51-54 noise-modulated sample-position offset. Following Feller 2024 would be wrong.
