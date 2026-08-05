---
name: android-test-device-via-adb
description: "Drive the Android profiling device directly via adb, not QR/manual scanning"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 06ba7dee-daf5-44a9-8fd0-f58027e5e820
---

The user has an Android test device on adb (`adb devices` shows it). Drive it directly instead of giving QR codes / asking them to scan:

- Open a profiling URL: `adb shell am start -a android.intent.action.VIEW -d "'<url>'"` — wrap the URL in **double-then-single** quotes so the `&` survives both fish and the on-device shell (a bare `&` truncates the URL at the first param).
- Read the page's real console/errors: `adb forward tcp:9222 localabstract:chrome_devtools_remote`, then attach a CDP WebSocket client (`/json/list` → page tab's `webSocketDebuggerUrl`) and listen to `Runtime.exceptionThrown` / `Log.entryAdded` while reloading. `/json/new` is blocked on recent Chrome — attach to an existing tab. This is how a blackscreen got diagnosed as a 404, not a GL crash.
- Keep the screen awake during a capture: `adb shell svc power stayon true` (reset to `false` after).

**Why:** the QR + self-signed-cert dance (accept `:8870` page cert AND visit `:8871` for the wss cert) cost a lot of round-trips this session; adb removes the user from the loop entirely. See [[project-lighthouse-falling-sand]].
