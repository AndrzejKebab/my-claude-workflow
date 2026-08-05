---
name: reference_unity_relaunch
description: How to kill and relaunch Unity editor — MUST use the `unity` launcher (on PATH from my-claude-workflow/bin)
type: reference
originSessionId: 610c1e7c-6f0c-416e-bae4-8399adabeb10
---
When Unity editor genuinely needs a restart (native library rebuild, hang
confirmed, etc.) AND the user has authorised it:

```bash
killunity
nohup unity /mnt/archive4/UNITY/Projects/woweyreey > /dev/null 2>&1 &
```

Both `killunity` and `unity` live in `/home/midori/_dev/my-claude-workflow/bin/`
and are on PATH; always invoke by bare name, not by absolute path.

**CRITICAL**: NEVER launch Unity directly via the Hub binary path
(`/home/midori/Unity/Hub/Editor/.../Unity -projectPath …`). ALWAYS use the
`unity` launcher — it parses the project's editor version, applies the
LD_PRELOAD DnD crash fix, cleans `Temp/__Backupscenes`, and refuses to
double-launch (exit 1 with the running pid).

- `killunity` matches `Unity.*-projectPath|Unity.*-batchMode` so it leaves Unity
  Hub alone.
- After kill, wait for `unity-cli console --filter error --lines 5` to respond
  before issuing further unity-cli commands.
- Kill+relaunch is the user's call, not yours — the canonical sequence is
  `killunity; rm Temp/*Lock* ; unity .` and only on explicit instruction.
