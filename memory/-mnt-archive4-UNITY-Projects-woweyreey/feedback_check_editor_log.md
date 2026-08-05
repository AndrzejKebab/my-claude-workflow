---
name: Check editor log before assuming crash
description: When unity-cli connection fails, read Editor.log tail — Unity may be alive but recompiling/reloading
type: feedback
---

When unity-cli returns "connection refused" or "connection closed", do NOT assume Unity crashed. Always read the tail of the editor log first:

```bash
tail -50 /mnt/archive4/UNITY/Projects/woweyreey/Logs/Editor.log
```

**Why:** Unity drops the HTTP listener during domain reloads and recompilation. "Connection refused" often means Unity is mid-reload, not dead. Assuming crash leads to unnecessary kill+relaunch cycles.

**How to apply:** Before any kill/relaunch after a unity-cli failure, check `ps` and `Editor.log` to determine if Unity is actually dead vs temporarily unresponsive.
