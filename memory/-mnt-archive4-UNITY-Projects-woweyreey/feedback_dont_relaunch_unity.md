---
name: unity wrapper exit 1 = wait, do not retry
description: The `unity` wrapper (in /home/midori/_dev/my-claude-workflow/bin/, on PATH) refuses to double-launch — exit code 1 means an editor is already running. Wait for it to load; never loop launches, never pkill the running one.
type: feedback
originSessionId: 610c1e7c-6f0c-416e-bae4-8399adabeb10
---
The `unity` wrapper detects any running Unity editor process (via `pgrep -f
"/home/midori/Unity/Hub/Editor/.*/Editor/Unity"`) and exits **code 1** with a
message naming the existing pids. This is the canonical signal: **wait, do not
retry**.

**Why:** Unity does not allow two editor instances on the same project (lock
files in `Temp/`); a second launch silently hangs and the agent then loops
"launch → hang → launch" forever, stacking dead instances. The user explicitly
hardened the wrapper to break that loop after observing it.

**How to apply:**
- `unity <path>` exits 1 → the editor is already loading or already loaded.
  Probe with `unity-cli console --filter error --lines 5` until it responds,
  then proceed with whatever you intended.
- Never `pkill` the running editor to "unblock" yourself — the user's work is
  in there. Only relaunch on positive evidence Unity is dead AND a user signal,
  via the documented sequence: `killunity; rm Temp/*Lock* ; unity .`
- Never spin a launch loop, never `sleep && unity` retry.
