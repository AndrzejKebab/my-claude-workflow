---
name: measurement-reports-committed
description: User wants benchmark/measurement runs catalogued as detailed in-project markdown and committed to git
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0e8979ab-e848-4720-aa7c-43ef3163fcdb
---

When running benchmarks, profiling sweeps, or any empirical measurements, record a **detailed**
measurement report in markdown **inside the project** (not just chat output or scratch) and **commit
it**. Every run's raw numbers must be catalogued, not just summarized.

**Why:** The user treats measurement data as a durable project artifact — decisions (e.g. the
adaptive quality ladder) are derived from it and must be auditable/reproducible later. Chat-only or
gitignored (`prof-artifacts/`) data is considered lost.

**How to apply:** Write/append to a committed docs file (e.g. `docs/orchestrate/<topic>/...md`) as
each run completes — include device meta, baseline, full per-effect/per-knob tables, and caveats.
Copy raw `summary.json` artifacts into the committed tree too (prof-artifacts is gitignored). Relates
to the adaptive-ladder work in [[adaptive-ladder-device-findings]].
