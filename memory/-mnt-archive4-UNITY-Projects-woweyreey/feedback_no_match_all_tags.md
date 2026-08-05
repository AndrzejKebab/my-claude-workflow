---
name: No match-all tag behavior
description: Spatial query tags are strict layers (per-tag KDTrees), no wildcard/match-all concept
type: feedback
---

Tags in the spatial query system are strict layers — each tag gets its own KDTree. There is no "match all" or wildcard tag concept (e.g. tagHash=0 matching everything). Nobody needs that functionality.

**Why:** Simplifies the mental model — a query always targets exactly one layer. Also enables per-tag tree optimization (smaller trees = faster queries).

**How to apply:** When designing query APIs, always require an explicit tag parameter. Never add fallback/wildcard behavior for tags.
