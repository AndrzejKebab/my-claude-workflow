---
name: DLSS Ray Reconstruction on Linux — required runtime bits
description: Where to find the Linux NGX feature plugins and the env vars / config file needed to actually load them on a consumer setup
type: reference
originSessionId: 4e537afa-4cbc-436a-986e-8b8dae00d40b
---
DLSS-RR works natively on Linux but the consumer driver's plugin distribution path is broken (CDN endpoints return 403 / "Unable to download config files"). Use the SDK-shipped plugins directly:

- **Plugins**: `github.com/NVIDIA/DLSS` clone has them at `lib/Linux_x86_64/rel/libnvidia-ngx-{dlss,dlssd,dlssg}.so.310.6.0`. (`dlssd` = Ray Reconstruction.)
- **Place plugins** at the app's `ApplicationDataPath` (for Cycles: the dir containing the `blender` binary, since `path_user_get()` returns `path_dirname(this_program_path())`) **and/or** at `ngx_models_path` from the conf file.
- **Conf file**: `~/.config/nvidia-ngx-conf.json` (XDG, user-writable, takes precedence over `/usr/share/nvidia/nvidia-ngx-conf.json`):
  ```json
  { "file_format_version": "1.0.0",
    "ngx_models_path": "/usr/share/nvidia/ngx",
    "allow_ngx_updater": false }
  ```
  `allow_ngx_updater: false` is critical — true triggers CDN updater that spams "Unable to download config files" on every NGX init.
- **Env var**: `__NV_SIGNED_LOAD_CHECK=none` is required because the SDK-shipped plugins fail the driver's default signature check. Without this, every `NVSDK_NGX_*_GetFeatureRequirements` call returns `0xBAD00012` (NotImplemented).
- **Discovery probe**: result `0xBAD00012` from `GetFeatureRequirements` means "no plugin found at the expected path"; result `0x00000001` with `FeatureSupported=0 (Supported)` means it works.

The DLSS-RR Integration Guide PDF in the SDK (`doc/DLSS-RR Integration Guide.pdf`, sections 2.1 and 2.2) documents the NGX-side discovery API (`FeatureCommonInfo::PathListInfo` for explicit paths, `nvngx_dlssd.dll` on Windows / `libnvidia-ngx-dlssd.so` on Linux). Linux requirements are glibc ≥ 2.11 and driver after Aug 2023.
