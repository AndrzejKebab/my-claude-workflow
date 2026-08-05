---
name: ue-wayland-drag-sdl-videodriver
description: "UE 5.8's native Wayland SDL3 backend drops held-button+motion entirely; SDL_VIDEODRIVER=x11 fixes it and is now the seat default"
metadata: 
  node_type: memory
  type: project
  originSessionId: b50e515b-7098-4268-93e9-262ab2c101de
  modified: 2026-08-05T01:45:22.790Z
---

**Solved 2026-08-05, after this had gone unsolved across multiple prior attempts including
hand-built canary programs.**

Symptom: on UE 5.8 under Wayland, a **held mouse button plus pointer motion never reaches the
engine**. Clicks land. Held-button + WASD works. RMB-drag to orbit the editor viewport, and
in-game mouse-look, do nothing at all. Not intermittent once isolated — the drag path is
simply dead.

**Root cause: UE 5.8's native Wayland SDL3 backend** (`LogInit: Using SDL video driver
'wayland'`, SDL 3.4.4 — 5.8 moved from SDL2 to SDL3). **Fix:**

```
SDL_VIDEODRIVER=x11
```

The SDL2 spelling still works in SDL3; `SDL_VIDEO_DRIVER` also works. It is a *complete*
backend switch — Vulkan follows from `VK_KHR_wayland_surface` to `VK_KHR_xlib_surface`. Verify
it engaged by reading `LogInit: Using SDL video driver` in the log, never by assuming.

This is now the **seat runner's default for every mode** in
`~/_dev/zori_skills/plugins/unreal/`, emitted before `ZORI_UE_SEAT_ENV` so a repo can override
with `SDL_VIDEODRIVER=wayland`. **If drag ever dies again, read that log line first.**

What was ruled out along the way, so it is not re-investigated:

- **Not missing protocols.** Both Hyprland and the nested kwin advertise
  `zwp_pointer_constraints_v1` and `zwp_relative_pointer_manager_v1`.
- **Not host-window rescaling.** A tiled nested seat *is* rescaled (2542x1422 host window vs a
  2560x1440 virtual output on a 2560x1440 monitor with 8px gaps + 1px border ≈ 0.993
  downscale), and that theory was tested directly: forcing the seat fullscreen and 1:1 did
  **not** fix the drag. The Xwayland fix then survived many fullscreen toggles, workspace
  moves and resizes, which is the same conclusion from the other direction.
- **Not the nested compositor.** It reproduced without any nesting.

**PIE mouse-look in the seat is a separate, ABANDONED problem — do not re-investigate.** The
x11 fix covers everything riding on an *implicit* grab (button held), which is all the editor
camera needs. PIE requests *persistent capture with no button held*, and that explicit lock
succeeds in the standalone game on the host but dies in the nesting chain (Unreal → Xwayland →
nested kwin → Hyprland): a nested compositor is a host client like any other and cannot take
the pointer just because its client asked. kwin's manual grab is hardcoded to **right Ctrl**
(no config; this keyboard has none) and can be synthesised with `hyprctl dispatch sendshortcut
",Control_R,address:<seat>"` — the window title flipping to "Press right control to ungrab
pointer" is a reliable machine-readable grab-state signal — but **grabbing broke the editor**,
so it was abandoned 2026-08-05 at the owner's call. Standing answer: `/unreal:playtest` for
anything needing mouse-look, or a gamepad for in-viewport play sessions.

Method note worth keeping: what cracked the main bug was two arms with **one variable each**,
host geometry held constant and verified identical between them, each arm's engagement
confirmed in the log. The geometry arm failing is what made the backend arm conclusive.

Seats and their constraints: [[ue-nested-compositor-seats]]. Gate layer: [[ue-farts-gate-layer]].
