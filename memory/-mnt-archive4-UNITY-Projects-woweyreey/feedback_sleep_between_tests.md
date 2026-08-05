---
name: Sleep between unity-cli test runs
description: Must sleep 5 seconds between sequential unity-cli test commands to avoid conflicts
type: feedback
originSessionId: 7c0ad9af-26c3-49fb-ad26-509f09d28e90
---
Sleep 5 seconds between sequential unity-cli test runs.

**Why:** Unity test runner needs time to reset between test suite executions. Running them back-to-back without a gap causes the second run to queue/hang or produce empty results.

**How to apply:** When running multiple `unity-cli test` commands sequentially, insert `sleep 5` between them. This applies to both foreground and background test runs.
