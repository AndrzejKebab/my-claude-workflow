---
name: Profile results — per-frame stats only
description: When presenting profiler results, show per-frame averages/median/p90/p95/min/max, not total ms
type: feedback
---

Show per-frame statistics (mean, median, p90, p95, min, max) when presenting profiler results. Total ms across all frames is not useful — it scales with capture duration and says nothing about frame behavior.

**Why:** Total ms is a function of how long you captured, not how the game performs. Per-frame stats are actionable.

**How to apply:** When reading analyze.sh output, convert "Self ms / Total ms" columns to per-frame by dividing by frame count. For render passes, show avg/min/max per call. For GC, show per-frame averages and spike outliers.
