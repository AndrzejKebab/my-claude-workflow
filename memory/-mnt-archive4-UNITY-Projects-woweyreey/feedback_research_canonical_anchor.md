---
name: Anchor technical decisions to canonical research
description: When a research doc (NC23, HZD15, FB16, Hillaire, Kühnert, etc.) specifies an approach, follow it verbatim — don't invent "adapted" variants based on supposed project-specific constraints
type: feedback
originSessionId: df67e33e-e762-4246-99c0-12d49cc96485
---
Follow the canonical approach laid out in `docs/research/` verbatim. Don't invent "adapted" variants because our setup seems different.

**Why:** Inventing project-specific adaptations based on misread constraints (e.g. baking a cloud altitude assumption to justify an in-volume-distance split instead of NC23's canonical world-space-from-camera split) produces non-canonical behaviour, diverges from the reference artists/engineers are calibrating to, and compounds across systems. If the canonical approach doesn't solve the specific perf phase we're targeting, that's a fact to surface — not a license to invent.

**How to apply:**
- When planning a feature that has a research reference (NC23, HZD, FB, etc.), cite the paper's exact parameters and semantics. If something in our setup seems to conflict, assume the conflict is in how I'm interpreting our setup, not in the research.
- Never special-case on project-specific numbers (altitudes, distances, sizes) that are consumer-configurable in a package. Package consumers (and internal presets) set whatever they want.
- If the canonical approach buys less for our specific profile than the handoff hopes, state it as a trade-off in the plan — don't invent a novel variant to close the gap without discussion.
- Related: `feedback_defaults_vs_serialized.md` (same family — don't treat script defaults as ground truth when `.asset` values override them).
