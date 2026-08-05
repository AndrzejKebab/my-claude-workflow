---
name: Test real code paths
description: E2E tests must exercise the same registration/lifecycle flow as the editor — shortcuts like RegisterImmediate create false positives
type: feedback
---

Tests must go through the same systems as the editor. Don't bypass the real flow with shortcuts.

**Why:** The auto-flush stale-entry bug was invisible to tests because E2E tests used `JsEntityRegistry.RegisterImmediate()` (direct registration) instead of `JsScriptFulfillmentSystem` → `__componentInit` → `__tickComponents` (the real editor path). The test-created entities only called `get()` once per flush window, so the multi-get stale-entry bug never triggered.

**How to apply:** When writing E2E tests for JS component behavior, ensure the entity goes through the full lifecycle: `JsScriptRequest` → fulfillment → `__componentInit` → `start()` + `update()` in `__tickComponents`. If a test bypasses this (e.g., direct `RegisterImmediate`), it should be clearly scoped to testing only the bypassed mechanism, not end-to-end behavior.
