---
name: project-lighthouse-falling-sand
description: "zori.is is a lighthouse reference work studying falling-sand CA techniques, not just an app; downstream Unity/Bevy plugins depend on it"
metadata: 
  node_type: memory
  type: project
  originSessionId: d9a77483-d6d9-4212-bea0-9620f01f7ebe
---

zori.is (the `particle-fix` repo, Rust/WASM falling-sand CA + off-grid particle layer) is not merely
an app — it is a **quintessential reference work** on falling-sand cellular-automata game techniques:
a portable minimal harness where techniques are **tested, documented, and studied**.

It is the **lighthouse** for downstream production efforts — a Unity plugin and a Bevy plugin, each a
production-grade falling-sand CA game-engine plugin — which are validated against the techniques proven
here.

**How to apply:** treat the test harness + technique docs as first-class deliverables, not scaffolding.
Rigor, conservation/stability proofs, and domain-split documentation are the product. The `docs/`
technique pages (handoff, deposition, occupancy, scheduling stability, tile-border) are study/reference
material a porter rebuilds from. See [[stability-harness-is-load-bearing]], [[blackbox-test-harness]].
