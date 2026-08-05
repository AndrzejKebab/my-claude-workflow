---
name: pipewire-jack clients can wreck Bluetooth audio via forced graph rate
description: When BT audio sounds mangled after running a JACK client, clear pw-metadata force-rate/quantum
type: feedback
originSessionId: 4887e00b-609e-48c9-ae07-a2ac802bc0d1
---
After installing `pipewire-jack` (replaces `jack2`) and running a JACK client (e.g. wineasio in a wine app), Bluetooth A2DP can start producing mangled audio. Cause: the JACK client sets `clock.force-rate` / `clock.force-quantum` on the global PipeWire graph (`pw-metadata 0`), and BT codec can't renegotiate to that rate.

**Why:** PipeWire's JACK API shim pins the graph config when a JACK client connects. A leftover wineserver keeps the lock. Bluetooth codecs (SBC/AAC) need the graph at codec-native rates.

**How to apply:** When BT audio breaks after wine/JACK use:

```
pw-metadata 0 clock.force-rate ''
pw-metadata 0 clock.force-quantum ''
```

Or nuke and restart all of pipewire:

```
systemctl --user restart wireplumber pipewire pipewire-pulse
```

Long-term: only set `pw-jack` env at app launch time, kill `wineserver` after closing the app to release the lock.
