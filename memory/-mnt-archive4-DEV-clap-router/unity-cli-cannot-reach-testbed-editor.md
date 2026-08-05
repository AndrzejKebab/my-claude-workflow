---
name: unity-cli-cannot-reach-testbed-editor
description: unity-cli connector does not list the clap-router-unity-testbed editor; in-editor verification goes through the user
metadata: 
  node_type: memory
  type: project
  originSessionId: 5c7d4c3e-9209-4a56-9e22-0aa05b96a233
---

Two sessions (2026-07-03 and the one before) could not reach the open `clap-router-unity-testbed` Unity editor over the unity-cli connector — it lists other open editors but not this one. Reachability unresolved.

**Why:** in-editor verification of clap-router demo changes cannot be automated until this is fixed; batchmode is forbidden while the editor is open ([[no-batchmode-while-editor-open]]).

**How to apply:** for live-editor checks, either resolve connector reachability first or hand the user exact in-editor steps and wait for their verdict. Headless gates (`ctest`, `tools/render_demo.sh`) work fine without the editor.
