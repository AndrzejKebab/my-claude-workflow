---
name: Don't delete tests — rework them
description: When migrating infrastructure, convert existing tests to the new API instead of deleting them and their fixtures
type: feedback
---

When replacing infrastructure, rework existing tests to use the new API — don't delete them along with their fixtures. The tests and fixture data are valuable; only the mechanism needs updating.

**Why:** Tests cover real scenarios. Deleting them loses coverage. The fixture data (e.g. hot-reload-fixture .ts files) is test infrastructure, not dead code tied to the old implementation.

**How to apply:** When cleaning up after an infrastructure change, identify tests that use the old API, then rewrite their plumbing to use the new API while preserving their test logic and assertions.
