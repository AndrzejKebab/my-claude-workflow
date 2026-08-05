---
name: Steam Deck 60 FPS is the minimum perf target
description: All perf deliberation is anchored to Steam Deck 60 FPS — the minimum frame budget that dictates scope and fallback trade-offs
type: project
originSessionId: d4d1fc59-37c2-407e-bc20-7f70d1a18579
---
Minimum performance target is **Steam Deck at 60 FPS** (16.6 ms/frame budget).
Every rendering / compute cost decision and every "ship vs defer" scope call
is measured against this target.

**Why:** The Deck is the floor device — anything slower than 60 FPS there ships
broken. Desktop headroom is secondary; if a feature is Deck-viable it's
desktop-viable, so the Deck budget drives scope.

**How to apply:**
- Budget new compute passes against the Deck frame, not a desktop card.
  A "~1 ms on Deck" cost is a substantial fraction of the per-frame budget
  and needs explicit justification.
- When proposing LUT resolution, step counts, or per-froxel tap counts,
  state the Deck cost and compare to the current budget line for that pass.
- Prefer cheaper reconstructions (Catmull-Rom, dither) over resolution bumps
  when both would plausibly resolve an artifact — resolution bumps scale
  multiplicatively with the pass cost.
- If a fix lands at the Deck perf ceiling, schedule a profile pass (see
  `.claude/skills/profile/`) before declaring the task done.
- "Acceptable on desktop" is not acceptable.
