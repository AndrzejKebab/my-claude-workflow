# Memory Index

- [Prefer tools over guessing](prefer-tools-over-guessing.md) — inspect live state via MCP/Bash before speculating
- [FARTS UE5.8 BuildId mismatch](farts-ue58-buildid-mismatch.md) — per-target split is normal noise; only the enabled closure must match core (UE_5.8.0 dir holds 5.8.1)
- [UE engine update procedure](ue-engine-update-procedure.md) — bump the source build to a new tag; shallow fetch, Voxel hook re-injection, why commandlets exit 1 on success
- [VoxelMCP plugin](voxelmcp-plugin.md) — MCP toolset for Voxel graphs; canonical context is in the repo (Plugins/VoxelMCP/CLAUDE.md + DESIGN.md)
- [UE headless python authoring](ue-headless-python-authoring.md) — author FARTS assets via `-run=pythonscript` commandlet when MCP is down; gotchas (stdout, load_asset, param read-back, registry scan, level-actor persistence, IMC mappings, PIE hang)
- [FARTS ALS character foundation](farts-als-character-foundation.md) — playable character/camera/avatar on ALS-Refactored; where it lives + avatar/overlay/skeleton wiring
- [FARTS avatar part dynamics](farts-avatar-part-dynamics.md) — parts carry their own RigidBody/cloth via Copy-Pose prefab actors (not Leader Pose); why + the 3-tier test suite
- [Grz weapon mesh extraction](grz-weapon-mesh-extraction.md) — Gruzzam weapons are baked into the character mesh; extract a standalone static mesh via GeometryScript (Scripts/extract_grz_hammer.py)
- [FARTS off-hand grip IK](farts-offhand-grip-ik.md) — left-hand two-bone IK for two-handed armaments runs post-retarget in UFartsRetargetAnimInstance (visible body has no AnimBP), not source-side
- [Epic launcher under Wine + EOS](epic-launcher-wine-eos.md) — 20.x self-update never restarts under Proton; EOS gate needs dotnet48 + win10 + manual service registration; prefer fab.com/ue-asset-cli instead
- [UE nested-compositor seats](ue-nested-compositor-seats.md) — Unreal QA runs in a nested kwin (windowed for the human, --virtual offscreen w/ real GPU for the agent); no KDE session needed
- [UE editor settings corruption](ue-editor-settings-corruption.md) — force-killing the editor corrupts EditorPerProjectUserSettings.ini; loads fine, breaks viewport input, mimics a compositor/driver bug. Reset it early.
- [UE Wayland drag fix](ue-wayland-drag-sdl-videodriver.md) — UE 5.8's native Wayland SDL3 backend drops held-button+motion entirely; SDL_VIDEODRIVER=x11 fixes it, now the seat default
- [FARTS gate layer](ue-farts-gate-layer.md) — gates run through zori_skills/plugins/unreal runners; UE exits 1 on success, test filters are prefix matches, the avatar SSIM gate is knowingly RED
