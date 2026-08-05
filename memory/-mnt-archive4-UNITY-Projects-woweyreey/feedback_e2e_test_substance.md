---
name: E2E tests must use real code paths
description: E2E tests call the same public API the user would — no partial simulation, no mocks, no parallel reimplementation
type: feedback
---

E2E tests must exercise the exact same code path the user would use. Not a simulation, not a partial reimplementation, not a mock.

**Why:** A test that manually constructs rsync commands proves nothing about the Deploy() pipeline. When the test passes but the button fails, the test is worthless — it tested a parallel code path that doesn't exist in production.

**How to apply:** E2E tests call the public API directly (e.g., `SteamDeckDeploy.Deploy()`). If the API fails, the test fails. Use `Assume.That` to skip when prerequisites (network, device) are unavailable, but never simulate the functionality being tested.
