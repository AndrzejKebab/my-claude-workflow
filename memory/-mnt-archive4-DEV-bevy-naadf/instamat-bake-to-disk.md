---
name: instamat-bake-to-disk
description: InstaMAT→Bevy uses an offline batch baker run before build via justfile; AssetProcessor rejected; bevy-naadf + bevy-instamat workspace
metadata: 
  node_type: memory
  type: project
  originSessionId: 20a9f213-013d-4133-a213-1f8893ff27cc
---

InstaMAT→Bevy bakes PBR textures to plain image files on disk via an **offline batch process pre-build**, wired through a `justfile`. Shippable game build contains zero InstaMAT code, no `.imp`, no runtime dep — consumes only baked plain textures (per-channel PNGs + `material.ron`) through stock Bevy asset loading.

**Architecture (settled 2026-05-14):**
- Single batch baker binary processes ALL `.imp` files in one run. Lives in `bevy-instamat` crate behind an `instamat` Cargo feature. `dlopen`s `libInstaMATNativeInterface.so` (discovered from dev's InstaMAT Studio install, never vendored).
- `justfile` runs the baker as pre-build step.
- `.imp` = repo source, excluded from shipped distribution. Baked PNGs + `material.ron` = committed + shipped.
- Cargo workspace: `bevy-naadf` (game) + `bevy-instamat` (feature-free `MaterialRonLoader`/`BakedMaterialPlugin` lib + the `instamat`-feature batch baker). `bevy-naadf` depends on `bevy-instamat` with default features only — game build compiles no FFI.

**Why no AssetProcessor:** rejected twice. It keeps the `.imp` + InstaMAT coupling inside the build/run loop and compiles FFI into the app. Offline batch fully decouples — InstaMAT touches the project only when dev runs `just bake`.

**Why baked-only ships:** InstaMAT SLA (non-commercial, client-side, non-redistributable runtime).

See [[instamat-bevy-orchestration]]. v2 (offline single-file CLI, full end-to-end) at checkpoint `5833c71` on `instamat-bevy`; v3 = that + batch loop + justfile + crate split + land on `main`.
