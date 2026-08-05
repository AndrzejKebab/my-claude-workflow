---
name: solo-dev-agent-first-principles
description: "Hypertino core design principles — solo dev, minimal everything, agent-first debugging (no vision), editor is 100% human level design"
metadata: 
  node_type: memory
  type: project
  originSessionId: 069108a5-de18-445a-9999-df2891ddd754
---

Stated 2026-07-05 during spec-book orchestration, binding project-wide:

- User is a solo developer empowered by agentic tools; everything must be very minimal.
- Development and debugging surfaces are agent-first: machine-readable, deterministic, non-visual (metrics, checksums, structured dumps, single-command gates). Agents do most implementation/debugging; the human does final verification and gauges where agents fail.
- Claude cannot use vision to accurately diagnose graphics-programming issues. Rendering/VFX systems must expose non-visual verification (numeric invariants, tool-computed pixel metrics like FLIP/SSIM, buffer stats). "Look at the screen" is not a debug story. Related: [[representative-e2e-not-manual-qa]], [[suite-may-be-vacuous]].
- The editor empowers level design, which is 100% human-driven; editor UI is a human instrument, MCP/introspection is the agent instrument.

**Why:** sizes every design decision (spec TARGET choices, tooling, UI scope) for one human + agents.
**How to apply:** in design/spec work prefer smallest viable v1; reject team-scale surfaces; require machine-readable verification paths in any new system design. Recorded in repo at docs/orchestrate/spec-book/01-context.md §Core design principles.
