---
name: mobile-256mib-binding-cap
description: "All mobile GPU backends (iOS Safari WebGPU, Android Mali Vulkan, Android Adreno) report `max_storage_buffer_binding_size = 256 MiB` — the WebGPU spec mandatory minimum. Universal mobile ceiling for storage-buffer bindings."
metadata: 
  node_type: memory
  type: project
  originSessionId: 06185122-138a-425f-b330-f7de6251fc99
---

Mobile WebGPU/Vulkan caps storage-buffer **bindings** (not buffers) at **256 MiB exactly** (268,435,456 bytes), the WebGPU spec mandatory minimum. Confirmed 2026-05-21 on Mali-G52 / Vulkan / Android 12 via the `feat/android-build` probe (`crates/bevy_naadf/src/android_main.rs`). Same number on iOS Safari WebGPU. Desktop wgpu reports 1-4 GiB.

`max_buffer_size` is separately ~2 GiB on Mali — a buffer can be huge, but the bound *slice* is what's capped. So "shrink the buffer" and "shrink the binding" are different fixes; sliding-window binding into a single large buffer is spec-valid.

**Why:** The full-world NAADF allocations (`voxels` 1024 MiB, `blocks` 512 MiB) are 4×/2× over this cap on any mobile target. Killed the Galaxy Tab A8 with a kernel-OOM reboot when attempted natively. The cap is the universal mobile ceiling — solving it once (in [[android-build]]'s Task #7, see `docs/todo/android-build.md`) unblocks both Android native and iOS WebGPU.

**How to apply:** When designing mobile-capable buffer layouts for `bevy-naadf`, treat 256 MiB binding × 75% headroom = 192 MiB as the per-binding budget. Use `device.limits().max_storage_buffer_binding_size` at startup to read the actual cap (will be 256 MiB on mobile, more on desktop) and scale the world / TAA ring / per-pixel buffers accordingly. Don't pre-allocate the C# 256×32×256 fixed-world container unconditionally — derive from this cap.
