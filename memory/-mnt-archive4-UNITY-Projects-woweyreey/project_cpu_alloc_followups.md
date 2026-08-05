---
name: CPU allocation follow-ups (Steam Deck)
description: Known per-frame managed allocations flagged during 2026-04-13 atmospherics profiling — revisit when GC spikes show up
type: project
originSessionId: 094763bb-74cb-4ce0-b59f-e2472133aa04
---
Deferred from the atmospherics optimization pass on 2026-04-13. Currently NOT causing GC spikes (frame-GC p95 = 20 KB, all from PlayerLoop itself) but they are steady per-frame churn that will bite in long sessions.

From terrain-bench Steam Deck profile (2000 frames):

- **FloatingOrigin.LateUpdate** — 742 KB total, ~380 B/frame. Likely iterating transforms and allocating a managed list each update. Cache the list.
- **CloudPresetInterpolator.Update** — 340 KB total, ~170 B/frame. Similar pattern; precompute interpolation keys.
- **LogStringToConsole** — 457 KB / 254 calls. Dev build only, gone in release. Not worth fixing.

**Why:** Fine now because GC never triggers within a frame, but at ~700 B/frame × 60 fps × 30 min ≈ 75 MB of Gen 0 churn per session.

**How to apply:** Revisit when you see GC spikes in a future profile, or when optimizing for long-play stability. Don't preemptively refactor — the current behaviour is invisible in frame times.
