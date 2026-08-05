---
name: Relaunch Unity after native library changes
description: Kill and relaunch Unity editor every time a native .so/.dll is recompiled
type: feedback
---

Always kill and relaunch the Unity editor after recompiling native libraries (e.g. qjs_shim.so, qjs.so).

**Why:** Unity caches loaded native libraries at startup. Modified .so files on disk won't take effect until the editor is restarted. Previous sessions hit DllNotFoundException from stale cached binaries.

**How to apply:** After any `cc -shared` or native rebuild, run `pkill -f "Unity"` (matches full command line, more reliable than `killall`) and relaunch before testing.
