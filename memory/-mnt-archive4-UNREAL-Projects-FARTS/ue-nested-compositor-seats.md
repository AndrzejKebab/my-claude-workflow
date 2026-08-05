---
name: ue-nested-compositor-seats
description: "Unreal QA on Hyprland runs in a nested kwin — windowed for the human, --virtual (offscreen, real GPU) for the agent; no KDE session needed"
metadata: 
  node_type: memory
  type: project
  originSessionId: b50e515b-7098-4268-93e9-262ab2c101de
  modified: 2026-08-05T01:22:24.631Z
---

**KDE window management is a hard requirement, permanently.** Unreal's tooltips and popups are
unusable under a tiling WM — the owner's words: "we can't ever work without KDE due to Unreal's
tooltips and popups." Never propose dropping the nested compositor or running the editor
directly on Hyprland. It is the *human's* UI interaction that needs it; an agent driving the
editor over MCP does not, but uses the same mechanism.

**Bare `kwin_wayland` is sufficient** — confirmed by the owner ("the black screen and unreal in
it was ok"). `ZORI_UE_SEAT_COMPOSITOR=plasma` starts a full Plasma shell in the seat and is
verified working, but it is *not* needed and renders the owner's entire desktop for nothing.
Leave the default alone.

Manual Unreal QA on this machine no longer needs a booted KDE session. `kwin_wayland` runs
**nested** two ways, and both were measured working 2026-08-05:

- `kwin_wayland --wayland-display $WAYLAND_DISPLAY --xwayland --socket <name> --width W
  --height H --no-lockscreen --exit-with-session <app>` — one Hyprland window, kwin owns
  tooltip/popup/menu placement inside it. This is the thing the KDE session was for.
- `kwin_wayland --virtual --xwayland …` — **offscreen with full GPU access**: measured direct
  rendering, NVIDIA RTX 5080, Vulkan 1.4, rootless Xwayland on `:1`, full Slate, KDE window
  decorations. So the agent can hold a *headful* editor with no window on the user's desktop.

Load-bearing details found the hard way:

- `--exit-with-session <path>` ties the compositor's life to the app's; without it a nested
  compositor outlives its engine and keeps the GPU context and the project's locks.
- Screenshots of a nested kwin come from `org.kde.KWin.ScreenShot2`, which the nested instance
  registers on the **session** bus — `env -u DISPLAY WAYLAND_DISPLAY=<socket> spectacle -b -n -f
  -o out.png`. `grim` does NOT work (kwin has no wlr-screencopy). `env` wants its options
  **before** any assignment; `env FOO=x -u BAR cmd` passes `-u` to cmd.
- Only one nested kwin at a time — two both claim `org.kde.KWin`.
- `gamescope --backend headless` exists and is how the game-seat path gets verified without a
  window.

**The game does NOT use a nested compositor.** `seat play` runs it directly on Hyprland:
a game is a single window, so the reason the editor needs kwin does not apply, and on the
host the WM owns fullscreen and resize. Verified — it comes up as a *native Wayland*
toplevel (class `UnrealEditor`, `xwayland: false`) and accepts the WM's tile geometry
(asked 2560x1440, took 2542x1422). `-windowed` is passed explicitly because
`GameUserSettings.ini` persists a fullscreen mode that would otherwise win.

Operating the visible editor seat: **right Ctrl grabs/releases the pointer** (until
grabbed, the editor reads as frozen); the seat window has an **empty app-id**, so host WM
rules must match its title (`KDE Wayland Compositor WL-<n>`); the editor opens at default
size in a corner on first launch and must be maximized once (Unreal then persists it).

User-facing entry points are `/unreal:qa_editor` and `/unreal:playtest` (both brief the
user first, then build → validate → launch); `seat` is the mechanism plus
`--status/--shot/--stop`. For kimi and anything else reading flat `~/.agents/skills/`,
`~/_dev/zori_skills/tools/install-agents-skills.sh unreal` symlinks them in as
`unreal-qa-editor` etc. Law in the plugin's `DOCTRINE.md`; FARTS bindings in
`.agents/project.sh`. See [[ue-farts-gate-layer]].
