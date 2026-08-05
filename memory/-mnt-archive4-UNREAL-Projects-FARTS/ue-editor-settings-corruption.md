---
name: ue-editor-settings-corruption
description: "Force-killing the UE editor corrupts EditorPerProjectUserSettings.ini; it loads fine and breaks viewport input, mimicking a compositor/driver bug"
metadata: 
  node_type: memory
  type: project
  originSessionId: b50e515b-7098-4268-93e9-262ab2c101de
  modified: 2026-08-05T01:59:35.850Z
---

**The editor writes its per-project user settings during shutdown.** Kill it mid-write — or kill
its process *group*, which takes the nested compositor down at the same instant and leaves the
engine without a display — and the file is left in a state that **loads without error and
behaves wrongly**.

Measured 2026-08-05, FARTS: a dozen force-kills across a debugging session left the editor
viewport with unusable mouse-look — first wildly hypersensitive, then no camera response at all.
It presented exactly like a Wayland/Hyprland/kwin or graphics-driver problem, and hours went into
compositor-layer hypotheses (pointer rescaling, nested constraint chaining, kwin auto-grab, host
accel settings) before the real cause surfaced. Every one of those was disproven by measurement;
none of them was it.

**Fix, and the thing to try early:**

```bash
rm Saved/Config/LinuxEditor/{EditorPerProjectUserSettings,EditorSettings,EditorLayout}.ini
```

The editor regenerates defaults on next launch. Back them up first; it is one command and it is
far cheaper than another round of layer-bisecting.

**Rule: when the editor viewport misbehaves in a way no compositor or driver setting explains,
reset the persisted editor settings BEFORE theorising further.** Odd input, odd viewport
behaviour, "it worked an hour ago and nothing changed" — that shape is this bug until ruled out.

The seat runner's `--stop` was fixed to signal the **engine alone** and wait generously (up to
120 s) for it to write, letting the compositor follow it down via `--exit-with-session`, instead
of signalling the process group. It warns explicitly when it has to force one, naming this file.

Related: [[ue-nested-compositor-seats]], [[ue-wayland-drag-sdl-videodriver]] — the genuine
Wayland fix, which is separate and still stands.
