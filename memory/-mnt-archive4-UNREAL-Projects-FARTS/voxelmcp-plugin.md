---
name: voxelmcp-plugin
description: VoxelMCP plugin — MCP toolset for authoring Voxel Plugin 2 graphs; canonical context lives IN THE REPO
metadata: 
  node_type: memory
  type: project
  originSessionId: 8420f862-568a-48b2-9655-25aa90568860
---

**VoxelMCP** is a project plugin at `Plugins/VoxelMCP/` (to be published as its own GitHub repo)
that exposes Voxel Plugin 2 (`UVoxelGraph`) assets to the Unreal MCP Toolset Registry so MCP
clients can inspect and author voxel graphs.

**The canonical, distributable context is in the repo — read those, don't rely on this memory:**
- `Plugins/VoxelMCP/CLAUDE.md` — architecture, reflection patterns, full tool list, the built-in
  `compileErrors` channel, authoring gotchas (buffer-typed function I/O, params default 0,
  call-node pins named by I/O guid), the build/test loop (build with editor CLOSED; SaveGraph after
  every section), and the TODO list. The MCP connection **auto-reconnects** after an editor restart —
  just call the tool; only flag a reconnect if a call actually fails to reach the server.
- `Plugins/VoxelMCP/DESIGN.md` — design rationale + Voxel C++ API map.

Lesson for this shared plugin: keep design/lesson notes in the repo (CLAUDE.md/DESIGN.md), NOT in
this machine-local memory — local memory doesn't travel with the repo. This file is just a pointer.
See [[farts-ue58-buildid-mismatch]] for THIS project's engine-build quirks (which are correctly
machine/project-local).
