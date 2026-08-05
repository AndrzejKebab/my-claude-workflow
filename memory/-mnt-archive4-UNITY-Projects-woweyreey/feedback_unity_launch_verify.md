---
name: Trust the unity wrapper's running-instance check
description: Don't pre-check Unity with ps/pgrep before launching — the wrapper does it and exits 1 if an instance exists. Don't pkill+relaunch on your own initiative either.
type: feedback
originSessionId: 610c1e7c-6f0c-416e-bae4-8399adabeb10
---
Don't run your own `ps aux | grep Unity` / `pgrep` pre-flight before
`unity <path>`. The wrapper itself refuses to double-launch and prints the
existing pids on exit 1. Just call `unity <path>` and read its output.

**Why:** Earlier guidance had the agent ps-verify and `pkill -9` before
launching. That's now wrong — it (a) duplicates a check the wrapper performs
authoritatively, and (b) the pkill step kills the user's editor session
unprompted. The user has explicitly forbidden agent-initiated kill+relaunch.

**How to apply:**
- Launch path: just `unity <project-path>`. If exit 0 → launched. If exit 1 →
  Unity is already running, wait for it to finish loading (probe via
  `unity-cli console --filter error --lines 5`), then proceed.
- Kill+relaunch is the user's call, not yours. The documented sequence
  `killunity; rm Temp/*Lock* ; unity .` is only run on explicit user request.
