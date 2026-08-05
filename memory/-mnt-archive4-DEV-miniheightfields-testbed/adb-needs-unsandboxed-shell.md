---
name: adb-needs-unsandboxed-shell
description: "adb from a sandboxed shell spawns a competing daemon and breaks the user's wireless device pairing — always run adb with the sandbox disabled"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 76a4e5a2-8bf6-4cbd-9c81-a369d77a9270
  modified: 2026-07-20T18:15:08.960Z
---

Every `adb` invocation must run with `dangerouslyDisableSandbox: true`, including any script
that shells out to it (the `test-player` `android` mode, and Unity itself when the test framework
deploys an APK).

**Why:** adb is a per-user daemon on tcp:5037. A sandboxed shell cannot reach the existing one, so
it silently starts *its own* in an isolated network namespace. That daemon lists zero devices — and
worse, it displaces the daemon holding a **wireless** (`_adb-tls-connect._tcp`) pairing, so the
device disappears for the user too until they restart the server. The failure reads as "the tablet
is not plugged in", which is what it looked like when the device was connected the whole time.

**How to apply:** never probe adb from a sandboxed shell "just to check" — that probe is what
breaks it. If `adb devices` comes back empty, confirm the transport before concluding anything:
a wireless device shows nothing in `lsusb`, so USB absence is not evidence of disconnection.
Backgrounding is fine and keeps the exemption; only sandboxing is the problem.

Related: [[single-editor-test-runs]] — same family of mistake, where checking process state
mid-run and acting on it produced two spurious RED suites in one session. Wait for the completion
notification instead of polling.
