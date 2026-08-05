---
name: mhf-ancestry-zori-heightfields
description: miniheightfields is a minimal port of is.zori.heightfields from zori_test_bed — check the ancestor for existing implementations before authoring
metadata: 
  node_type: memory
  type: project
  originSessionId: 4781d14e-196e-4ff9-9fcb-0f1d90b87ea1
---

`is.zori.miniheightfields` is a minimal port of `is.zori.heightfields` living in
`/mnt/archive4/UNITY/Projects/zori_test_bed/` — atmospherics stripped, several big improvements
added (user, 2026-07-15). The ancestor repo and its `is.zori.testbed` often already carry
tooling/benchmarks this project needs (e.g. a LitMotion-based motion benchmark existed there
while a session hand-rolled a new one here).

**Why:** reuse audits that only search the current repo miss the ancestor; the user has been
burned by needless rewrites of things that already existed.

**How to apply:** every reuse audit spans BOTH trees; zori_test_bed is read-only reference —
port per its consumption idiom, never modify it. Also recorded in the superproject AGENTS.md
§Ancestry.
