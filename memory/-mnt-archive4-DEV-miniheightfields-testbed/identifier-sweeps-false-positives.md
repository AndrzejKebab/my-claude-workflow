---
name: identifier-sweeps-false-positives
description: "Dead-code and citation sweeps that judge by identifier name produce confident false positives in a Unity package — a live parameter sharing a dead field's name, and code defaults that a scene overrides"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 82f1c76b-2749-4fea-bb5f-a033284a0a98
  modified: 2026-07-19T01:40:28.267Z
---

Sweeps that decide from an identifier's name alone — dead-value audits, "is this knob used anywhere", citation-drift checks — return **confident, well-argued false positives** in this codebase. Two observed, both of which would have shipped a defect while "cleaning up":

- **A dead field and a live parameter on the same call.** `VTDirtyRegion.LayerMask` had zero readers and was ported dead from the ancestor, but `VTHandle.InvalidateRegion`'s `layerMask` *parameter* of the same name is read to decide whether a rect counts as an authored height change. Grepping the identifier reads as "unused"; removing by that verdict would have silently forced shadow-pyramid re-derivation on every splat edit.
- **A code default treated as ground truth over a serialized value.** A citation sweep reported `memoryBudgetMB` as 64→128 drift and recommended rewriting two document sections. It had read the C# default; the benchmark scene serializes 64, which is what the capture measured. The document was correct.

**Why:** a Unity package's effective value comes from serialized scene/asset data, and its call graph routes through same-named parameters, properties and backing fields that grep flattens into one token.

**How to apply:** a sweep's verdict is a *candidate*, never a conclusion. Before acting, trace the specific declaration through to a consumer, and for any configured number check what the scene actually serializes rather than what the class initializes. Say this in the brief when dispatching a sweep — an agent given a clean identifier list will act on it. Related: [[six-urp-projects-are-husks]] (scope) and [[design-facts-go-in-spec-not-global-context]].
