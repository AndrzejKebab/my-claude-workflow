---
name: PlayMode bridge crash on structural changes
description: Codegen'd JS bridges (JsLocalTransformBridge) crash with SIGSEGV when ComponentLookup is invalidated by structural changes during PlayMode test runs
type: project
---

PlayMode tests crash Unity when entities are created/destroyed between tests. The codegen'd JS bridges (JsLocalTransformBridge, etc.) cache ComponentLookup<T> that gets invalidated by structural changes (entity creation, destruction, component add/remove).

**Symptom**: `ObjectDisposedException: Attempted to access ComponentLookup<NativeText.ReadOnly> which has been invalidated by a structural change` followed by `SIGSEGV` in `JS_CallInternal`.

**Why:** The bridge's ComponentLookup is obtained once and not refreshed after structural changes. In EditMode (EnterPlayMode/ExitPlayMode per test), each test gets a fresh world — no stale lookups. In PlayMode, the world persists and lookups go stale between tests.

**How to apply:** This blocks running the full PlayMode test suite with entity destruction between tests. Two workarounds: (1) Don't destroy test entities (causes memory growth + eventual crash from accumulation), (2) Fix the bridge codegen to call `componentLookup.Update(ref state)` before accessing. The real fix is (2) — in `JsGameCodegen/JsBridgeGenerator`.
