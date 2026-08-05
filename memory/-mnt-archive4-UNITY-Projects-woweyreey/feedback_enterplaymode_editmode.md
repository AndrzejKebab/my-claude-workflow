---
name: PlayMode test placement
description: E2E tests go in PlayMode assemblies — no EnterPlayMode/ExitPlayMode needed. Stress tests that exhaust QuickJS module cache stay in EditMode.
type: feedback
---

E2E tests go in PlayMode assemblies (no EnterPlayMode/ExitPlayMode). The test runner enters PlayMode ONCE for the entire suite.

Hot-reload stress tests (JsHotReloadE2EStressTests, JsHotReloadFixtureStressTests) stay in EditMode because they rapidly reload scripts with version suffixes, exhausting the 256-slot QuickJS module cache in a shared VM session.

**Why:** EditMode play-mode toggling takes seconds per test. PlayMode runs the whole suite in one session. Stress tests need a fresh VM per test.

**How to apply:** New E2E tests → PlayMode assembly. Tests that exhaust the VM (rapid reloads, syntax error injection at scale) → EditMode assembly.
