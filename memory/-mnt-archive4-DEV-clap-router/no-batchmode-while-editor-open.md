---
name: no-batchmode-while-editor-open
description: Never run Unity batchmode (or gate_unity.sh) while the editor is open on the same project — drive the live editor via unity-cli.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e7d20b1a-0acf-450d-90e4-1860226da093
---

Do NOT launch Unity batchmode against `clap-router-unity-testbed` while the user's live editor is open on it. `tools/gate_unity.sh` counts as batchmode (it also `rm`s the lockfile).

**Why:** batchmode + an open editor collide on `Library`/`Temp/UnityLockfile` and can corrupt/hang the project. The user caught me doing this; it plausibly contributed to instability I was chasing.

**How to apply:**
- Check `clap-router-unity-testbed/Temp/UnityLockfile` first. Present → editor live → **connector only**: `unity-cli exec/test/console`, `unity-cli-recompile` (the required live-editor recompile wrapper; never raw `unity-cli editor refresh`). Never touch the lockfile.
- Batchmode / `gate_unity.sh` only after the lockfile is confirmed ABSENT (editor closed).
- Standalone `render_demo` (host + device/capture, any `--block`) needs no Unity — run freely.
- With multiple editors open, `unity-cli` needs `--project <path>` (or run from the project CWD) to disambiguate.

Canonical home once it lands: the "Unity editor/batchmode coordination" section being added to `AGENTS.md`.
