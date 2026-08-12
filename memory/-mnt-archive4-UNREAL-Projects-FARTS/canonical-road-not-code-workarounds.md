---
name: canonical-road-not-code-workarounds
description: "If the canonical way to build a thing is in the editor, use MCP as a user would — never reimplement it in code because headless couldn't reach it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8c3912f1-9627-4619-ac93-3eb314d233b9
  modified: 2026-08-05T18:12:28.849Z
---

The owner, 2026-08-05: *"you were trying to instrument code-only headless setup that used shitty ass
datatables to control it instead of going the prime road of mcp automation directly following the
tutorial? that's a huge nono and should be prohibited by the doctrine — if canonical road is to use X
with editor, use MCP's as if a user would interacted with UI of the editor. if thats impossible —
find or instrument additional MCP surface and do it anyway."*

**Why:** headless `-run=pythonscript` has no node API, so it cannot author anim graphs, Control Rig
graphs or Blueprint graphs. Hitting that wall, I invented a parametric data model to do in C++ what a
Control Rig does in a graph. That forced a solver to *derive* what the reference says to *author*,
and produced a two-handed grip nobody would use — twice, both times passing every metric built
alongside it. The substitution did not look like a mistake: it had a design doc and was defended in
comments. But it existed because of a tool limitation, not because anyone wanted it.

**How to apply:** before writing code, ask *would a person doing this properly open the editor?* If
yes it is an MCP job — open an `agent` seat and perform the same operations through the toolsets. If
the toolset lacks the verb, ADD it (`create-toolset` skill); extending the MCP surface is in scope
and cheaper than a parallel mechanism that has to be designed, gated, documented and later deleted.
Code is for the runtime that consumes authored assets, and for measurement. Authoring is the
editor's.

Exploration order, same session: engine C++ source on disk first (greppable and authoritative —
`grep 'DisplayName="Basic IK"'` → `FRigUnit_TwoBoneIKSimplePerItem`, every pin in the struct), then
official docs, then shipped content/templates and working implementations already in the project,
then dissecting live assets via MCP introspection. **Video tutorials are last, for intent only,
never as an API source.** Do not process YouTube into markdown as a first move.

Both laws are in `~/_dev/zori_skills/plugins/unreal/DOCTRINE.md` (commits b02cc1c, 1905ee2, 64d3349).

Related: [[grip-truth-from-reference-rig]], [[ue-headless-python-authoring]], [[ue-farts-gate-layer]].
