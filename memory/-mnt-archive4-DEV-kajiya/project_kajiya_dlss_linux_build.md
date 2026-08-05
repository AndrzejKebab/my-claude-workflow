---
name: kajiya DLSS Linux build setup
description: How kajiya was patched to compile with DLSS on Linux against the modern (4.5) NGX SDK and Rust 1.93
type: project
originSessionId: f00af19e-11e8-4fb7-8449-8bf15d1b61fd
---
Built `cargo build --release --bin view --features dlss` on Linux against the public NGX SDK clone reused from the Blender DLSS work at `/mnt/archive4/BLENDER/vendor/dlss-sdk` (headers under `include/`, link lib `lib/Linux_x86_64/libnvsdk_ngx.a`, runtime plugins `lib/Linux_x86_64/{dev,rel}/libnvidia-ngx-dlss.so.310.6.0`).

**Why:** Kajiya is unmaintained; its DLSS support targets DLSS 2.x on Windows. Three orthogonal blockers had to be solved to build on modern Rust + new SDK on Linux:

1. **`com-rs 0.2.1` fails on stable Rust** — pulled in via `hassle-rs 0.10` (DXC bindings), uses unconditional `extern "stdcall"` which 1.85+ rejects on non-x86-Windows targets. Fixed by vendoring it at `vendor-com-rs/` (outside `crates/` so cargo doesn't auto-include it; added to workspace `exclude`; standalone `[workspace]` table) with `extern "stdcall"` → `extern "system"` in `src/macros.rs` + `src/unknown.rs`, then a `[patch.crates-io] com-rs = { path = "vendor-com-rs" }` override in the root Cargo.toml.

2. **`crates/lib/ngx_dlss/build.rs` was Windows-only** — patched to: pick `Lib/Linux_x86_64` + link `libnvsdk_ngx.a` (not `nvsdk_ngx_d`) on Linux; link `stdc++`, `dl`, `pthread` for the C++ static lib; bumped bindgen 0.59 → 0.69 (older bindgen panics on the new SDK's anonymous-union name `NVSDK_NGX_Resource_VK_union_(unnamed_at_...)` because `proc-macro2` rejects parens in idents); fall back to `/usr/include/vulkan` when `VULKAN_SDK` is unset.

3. **`crates/lib/kajiya/src/renderers/dlss.rs` calls drifted** — DLSS 4.5 SDK API changes: `NVSDK_NGX_VULKAN_Init` now takes 9 args (added `InGIPA`, `InGDPA` proc-addr fns — pass `None`); typo `NGSDK_NGX_LoggingInfo` → `NVSDK_NGX_LoggingInfo`; `NVSDK_NGX_Parameter_SetI` now takes `i32` (cast `u32` values); `NVSDK_NGX_VK_DLSS_Eval_Params` got a new `InExposureScale` field (set to `1.0`); replaced Windows-only `OsStrExt::encode_wide()` with a portable `to_wchar_z()` helper because Linux `wchar_t = c_int` (32-bit), not u16.

**NGX layout in the kajiya tree:** `crates/lib/ngx_dlss/NGX/Include` and `crates/lib/ngx_dlss/NGX/Lib/Linux_x86_64/libnvsdk_ngx.a` are symlinks into the Blender SDK clone — no duplication. The runtime plugin `libnvidia-ngx-dlss.so.310.6.0` is symlinked at the kajiya repo root and at `target/release/` so NGX finds it regardless of cwd (kajiya's DLSS code passes the `/kajiya` VFS path which resolves to cwd by default).

**How to run:**
```
cd /mnt/archive4/DEV/kajiya
__NV_SIGNED_LOAD_CHECK=none ./target/release/view --temporal-upsampling 1.5 --width 1920 --height 1080
```
The `__NV_SIGNED_LOAD_CHECK=none` env var and `~/.config/nvidia-ngx-conf.json` with `allow_ngx_updater: false` are required (already set up — see the DLSS-Linux reference memory in the Blender project).

**How to apply:** When this build breaks again (driver bump, rust toolchain bump, SDK bump), check those three blockers in order — the `com-rs` patch is the most fragile because it depends on hassle-rs's transitive resolution.
