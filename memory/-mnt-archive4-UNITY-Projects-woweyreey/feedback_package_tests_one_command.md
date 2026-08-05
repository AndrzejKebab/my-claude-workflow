---
name: Package test suites ship a one-command entry point
description: In-package visual/integration test suites must be runnable via a single script or filter, not a ritual of three+ unity-cli invocations
type: feedback
originSessionId: 08c53ac2-4be3-4db9-bad5-2dc4fd84850a
---
In-package test suites (under `Packages/<pkg>/Tests/PlayMode/`) that span
multiple test classes must ship a single entry point that runs the whole
intended slice end-to-end. A bash script next to the tests is the
accepted form.

**Why:** Tests that require the human to memorise and chain three or more
`unity-cli test --filter ...` commands get skipped or partially-run, and
the sequential-run conventions (5s sleep between runs, correct timeouts,
correct filter strings) get lost. Packaging the invocation next to the
tests makes the suite self-documenting and reproducible.

**How to apply:** When a test suite covers >1 test class or >1 logical
phase (e.g. static + temporal + perceptual):
- Add `run-quick.sh` (and/or `run-full.sh`) under the test folder
- Chain `unity-cli test --filter ...` calls for each class's quick-subset
  method name, not category/attribute-based filters (unity-cli filter is
  method-name based)
- Insert `sleep 5` between sequential runs per `feedback_sleep_between_tests`
- Honour per-suite timeout budgets (`--timeout`)
- `chmod +x` and commit alongside the tests
- Example: `Packages/com.api-haus.volumetric-clouds/Tests/PlayMode/run-quick.sh`
