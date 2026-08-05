---
name: web-haptics-platform-reality
description: "Web haptics on zori.is — Android Vibration API works, iOS 26 Safari has closed the synthetic-switch-click Taptic hack"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6250a7d2-824f-4660-9776-ed93ce712255
---

Confirmed on-device (iPhone 13 Pro, iOS 26.5 Safari, 2026-06):

- **Android** (Chrome/Firefox): `navigator.vibrate(ms)` works. No permission prompt; needs sticky activation (one prior user interaction). Short `vibrate(10)` reads as a soft tick; patterns `vibrate([...])` for events.
- **iOS Safari**: no Vibration API at all. The old `<input type="checkbox" switch>` + synthetic `.click()` Taptic hack is **dead as of iOS 26** — Apple gates the Taptic Engine on `isTrusted` events against a real native control. Synthetic clicks fire nothing, even synchronously inside a genuine `pointerdown` handler. Only a REAL finger toggle of a rendered native control fires haptics.
- The surviving iOS web-haptic technique (Project Fathom, github.com/m1ckc3s/project-fathom): overlay the REAL native `<input switch>` invisibly under the finger so the user's own tap actuates it → iOS fires the system tick. Must NOT pointer-capture or preventDefault the press, or the native click (and thus the haptic) is suppressed. Direct taps only — a continuous drag is one touch, so it can't tick per-sector on iOS.
- Passive game events (earthquake/meteor/sink) have NO iOS web path — no user gesture exists to ride.

Implemented in zori.is: `src/web/haptics.js` + `palette.js` branch on `usesNativeSwitchHaptic` (= !navigator.vibrate). Android = canvas host, captured, `tick()` per sector crossing. iOS = invisible `.palette-wheel-haptic` switch overlay (hud.css) on the wheel, tap → native tick + sector pick; drag scrubs silently. Full writeup: docs/haptics.md.

Beware: Safari held an undeletable cache that survived URL `?v=` changes during testing — verify a real bundle is loaded before concluding code is broken.
