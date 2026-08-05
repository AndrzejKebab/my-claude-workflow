---
name: durable-e2e-not-editor-qa
description: Verify render/shadow behavior ONLY with durable in-suite e2e gates; never drive the editor via unity-cli to QA/screenshot a behavior
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 81d98bbc-4384-42fb-ba68-1e61632d189f
---

The user twice, emphatically, rejected agent-driven editor QA (launching a live editor + `unity-cli`/`exec` C# to reproduce and screenshot shadow behavior) and demanded a durable e2e regression test in the suite instead — "dont fucking start using editor scripting for this, implement a durable regression test - like many others that we have already."

**Why:** editor-scripting QA is superficial, non-durable (never runs in the suite again), non-reproducible, and forcing single-frame `Camera.Render()` out of the normal pipeline sequence trips runtime asserts in abnormal states (e.g. the RC-B schedule-vs-baked-box origin assert at `ShadowFillRecorder.cs:119`), producing noise mistaken for bugs. A durable gate both proves the fix and guards forever. Extends [[verification-representatives-protocol]]: the analytical/SSIM gates are the machine arbiter; the human-eye PNG review is the FINAL layer, done by the USER on the real build — not by an agent screenshotting.

**How to apply:** to reproduce, verify, or regression-guard ANY render/shadow behavior, author a durable black-box e2e test via the test framework (test-player / test-suite skills, `.agents/skills/test-player/run.sh <proj> play "<name>"`), red-first, with an analytical oracle, committed in-suite — model it on the existing shadow gates (`HeightfieldShadowTerrainMoveStalenessTests`, `HeightfieldShadowOriginShiftTests`, `HeightfieldShadowTransformTests`). The user's canonical shape: converge → perturb (move / stack / rotate sun) → capture the shadow buffer → analytically assert the invariant (e.g. both terrains' contributions present, shadow coherent) vs a clean reference, anti-vacuity on the reference. NEVER substitute a live-editor unity-cli capture for that. Related working-style: [[evidence-over-abstract-forks]].
