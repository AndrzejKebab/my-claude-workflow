---
name: Perceptual artefact fixes — verify manually, not with mechanism tests
description: When fixing visual/temporal artefacts (streaks, flicker, oscillation, ghosting), don't propose RED-GREEN tests that assert on the fix's internal mechanism. Verify manually via frame debugger / RenderDoc / visual inspection.
type: feedback
originSessionId: 417000a8-f75c-468f-974a-f6f8e2f4282f
---
When fixing a perceptual artefact — streak-oscillation in an accumulator, ghosting, flicker, directional smear — do **not** propose an automated RED-GREEN test that asserts on the fix's internal mechanism (e.g. "assert that the BN seed UV is identical across a one-texel camera shift"). Go straight to manual visual verification: frame debugger / RenderDoc / live play.

**Why:** A mechanism assertion proves *the lever you pulled moved*, not *the artefact disappeared*. The artefact is in the temporal accumulator or EMA, only visible across many frames, and usually has multiple stacking contributors. A single-frame equality test covers one hypothesis in isolation and hides the others. The user pays with CI/asset-churn cost for a test that doesn't gate on what they actually care about.

**How to apply:**
- If the bug brief is "this looks wrong over time" (streak, flicker, oscillation, advecting pattern, ghosting, halo), default to manual verification: static-camera hold, motion sweeps, projection toggles, temporal-disabled control.
- Automated tests still apply for structural invariants (a pass produces the right handle lifetime, a global is published with the right quantum) and for functional regressions (a ray returns the right hit distance) — just not for "does the image look right now."
- If unsure, ask the user before writing a test harness for a perceptual fix.

Related: `feedback_only_e2e_tests` (no trivial mechanism assertions), `feedback_red_green` (still correct for logic bugs, not for visual artefacts).
