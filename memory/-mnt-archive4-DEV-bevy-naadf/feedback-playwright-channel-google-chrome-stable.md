---
name: feedback-playwright-channel-google-chrome-stable
description: "Playwright must use `channel: \"chrome\"` (system google-chrome-stable), never bundled chromium"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b6b284c-a4b9-4e10-80eb-a670749962ae
---

All bevy-naadf Playwright runs use system google-chrome-stable, not bundled chromium.

**Why:** different WebGPU/Vulkan/Dawn behaviors. User does visual checks in chrome-stable; tests on bundled chromium can mask or invent failures. `e2e/playwright.config.ts` pins `channel: "chrome"`.

**How to apply:**
- New specs inherit the global `channel: "chrome"` — don't override per-spec.
- Never `npx playwright install chromium` to "fix" missing-browser. Install google-chrome-stable via OS package manager.
- "Executable doesn't exist at .../ms-playwright/chromium-NNNN/..." = spec uses default channel; fix the spec, don't install chromium.

Related: [[feedback-web-runs-capture-logs]], [[playwright-e2e-must-be-headed]].
