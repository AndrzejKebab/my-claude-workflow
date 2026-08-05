---
name: Blender DLSS branch build location
description: Where the working DLSS-enabled Blender build lives and how it's configured
type: project
originSessionId: 4e537afa-4cbc-436a-986e-8b8dae00d40b
---
Working DLSS-RR-enabled build of PR #153077 (`dlss` branch, Patrick Mours, NVIDIA):

- **Source**: `/mnt/archive4/BLENDER` (moved off `~/_dev/blender` for disk space; symlink left at `~/_dev/blender → /mnt/archive4/BLENDER`)
- **Binary**: `/mnt/archive4/BLENDER/build_linux_release/bin/blender`
- **DLSS SDK headers** (build-time): `/mnt/archive4/BLENDER/vendor/dlss-sdk` (cloned `github.com/NVIDIA/DLSS`, headers under `include/`)
- **DLSS runtime plugins** (also from the SDK clone): `lib/Linux_x86_64/rel/libnvidia-ngx-{dlss,dlssd,dlssg}.so.310.6.0` — copied next to the blender binary so NGX can find them via `ApplicationDataPath`.
- **CMake flags used**: `-DWITH_DLSS=ON -DDLSS_SDK_ROOT=/mnt/archive4/BLENDER/vendor/dlss-sdk -DCUDA_TOOLKIT_ROOT_DIR=/opt/cuda -DOPTIX_ROOT_DIR=/opt/optix -DCUDA_HOST_COMPILER=/usr/bin/g++-15` plus the `release ninja ccache` config.

**Why:** PR #153077 adds NVIDIA DLSS-RR as a Cycles viewport denoiser. Build was straightforward once CUDA 13.2 and OptiX 9.1.0 were installed — CUDA 12.3 had glibc-mathcalls.h conflicts on gcc 15.

**How to apply:** The DLSS denoiser dropdown is gated on (a) `_cycles.with_dlss == True` (compiled in) AND (b) at least one CUDA device enabled in Edit→Preferences→System→Cycles Render Devices→CUDA tab. To make the runtime work, also need `__NV_SIGNED_LOAD_CHECK=none` and a user-side `~/.config/nvidia-ngx-conf.json` with `allow_ngx_updater: false` (see DLSS-Linux reference memory).
