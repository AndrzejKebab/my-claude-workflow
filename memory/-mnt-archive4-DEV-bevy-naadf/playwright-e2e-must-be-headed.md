---
name: playwright-e2e-must-be-headed
description: bevy-naadf web Playwright e2e suite must always run headed; headless Chromium kills the WebGPU device mid-render and hides real failures
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 573f4782-337e-47b1-8fd5-585150b770cf
---

Always run bevy-naadf Playwright e2e (`e2e/`) **headed**.

**Why:** NAADF render is WebGPU-only with heavy compute (`render::construction` GPU producer + ray-traversal shaders). Default headless Chromium routes WebGPU through `chrome-headless-shell` → SwiftShader fallback, which times out and panics with `Caught DeviceLost error: Destroyed Device was destroyed.` before `.vox` install / first frame. That noise masks real failures (wgpu validation, buffer-flag mismatches, wasm panics in `populate_cpu_mirror_from_gpu_producer`, etc.).

Headed Chrome routes through real Dawn + GPU-process pipeline, picks the host adapter (real GPU when present) — catches the bugs a user would.

**How to apply:**
- Default headed in justfile/CI (`npx playwright test --headed`).
- New `*.spec.ts`: don't design around headless DeviceLost — run headed.
- `test-wasm-headless` recipe = diagnostic escape hatch only; expected-to-fail unless isolating a non-GPU bug. Headed `test-wasm` gates correctness.
- `e2e/playwright.config.ts` pins `channel: "chrome"`. Without system Chrome, Playwright silently falls back to bundled chromium-headless-shell → install `google-chrome-stable`.

See [[web-vox-streaming]] context — first hit was the wgpu `getMappedRange` panic on `naadf_block_voxel_count_w2_placeholder` reproducing only with `--headed`.
