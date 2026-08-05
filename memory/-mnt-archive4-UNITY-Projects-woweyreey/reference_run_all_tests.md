---
name: run-all-tests.sh aggregated test runner
description: Single command to run EditMode+PlayMode sequentially with clean aggregated output
type: reference
---

`scripts/run-all-tests.sh "UnityJS"` runs both EditMode and PlayMode sequentially, outputs two summary lines:

```
EditMode: total=89 passed=89 failed=0 skipped=0 duration=211.8s
PlayMode: total=278 passed=278 failed=0 skipped=0 duration=23.2s
```

Failures print inline. Exits non-zero if either suite has failures.

Default filter is `UnityJS`. Override with first argument: `scripts/run-all-tests.sh "Project.Tests"`
