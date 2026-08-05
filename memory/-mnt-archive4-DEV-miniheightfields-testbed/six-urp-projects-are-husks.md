---
name: six-urp-projects-are-husks
description: "The six URP projects are empty husks that only establish package references and host test runs; all real content lives in is.zori.miniheightfields and is.zori.testbed"
metadata:
  node_type: memory
  type: project
  originSessionId: 82f1c76b-2749-4fea-bb5f-a033284a0a98
  modified: 2026-07-18T21:23:05.303Z
---

Only two places in this superproject carry meaningful content: **`is.zori.miniheightfields`** (the package) and **`is.zori.testbed`** (the testbed package, including `Scenes/` where the authored demo scenes live). The six URP version projects (URP17.0, URP17.3, URP17.5, …) are empty husks whose only purpose is to establish package references and give each Unity version somewhere to compile and run tests.

**How to apply:** when searching for callers or references — dead-code sweeps, "is this knob used anywhere" — scope to those two packages plus their Tests, editor tooling and shaders. Do not search the husk projects.

Related, and a mistake worth not repeating: **serialized references are not a reason to hesitate on a removal.** Deleting a serialized field just orphans its key in the asset YAML, and Unity discards it on the next re-serialize — no error, no corruption, nothing lost. Never audit `.unity`/`.asset` files for references to a field being removed, and never downgrade a dead field to "report rather than delete" on serialization grounds. The one removal that genuinely needs care is **public API**, because the package ships to third parties and a consumer's compile break is not repaired by re-serializing.

This does NOT contradict [[shared-tree-sequencing]] (all six still compile the one submodule, so a package-mutating agent still cannot run beside compile-dependent observers) or [[single-editor-test-runs]] (still one URP project per suite run, never all six).
