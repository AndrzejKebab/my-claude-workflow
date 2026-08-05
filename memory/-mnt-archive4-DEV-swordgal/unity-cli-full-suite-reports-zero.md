---
name: unity-cli-full-suite-reports-zero
description: "unity-cli PlayMode runs with no --filter report total 0 though the tests execute; use a filter or batchmode, and clear the stale lockfile first"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 0a7baa00-068d-4c5d-87f8-3a5ffa21f031
  modified: 2026-07-25T00:09:40.017Z
---

`unity-cli test --mode PlayMode --project /mnt/archive4/DEV/swordgal` with **no `--filter`**
returned `{"total":0,"passed":0,"failed":0}` on two consecutive attempts while the tests
demonstrably ran — the editor entered play mode for ~25 minutes and the fixtures' own log markers
appeared in `Logs/Editor.log`. The same command **with** `--filter Swordgal.Tests.<Class>` reports
correctly every time. Measured 2026-07-25.

So a full-suite answer comes from batchmode, which also gives a parseable XML:

```bash
processqueue gpu ~/_dev/my-claude-workflow/bin/unity /mnt/archive4/DEV/swordgal \
  -batchmode -runTests -testPlatform PlayMode -testResults /tmp/sg.xml -logFile /tmp/sg.log
```

Count `test-case` elements, never the root attribute — see [[unity-test-xml-root-total-lies]].

**After the GUI editor closes, `Temp/UnityLockfile` is left behind** and the batchmode guard hook
refuses to run. It is safe to remove *only* once `pgrep -af "Editor/Unity -projectPath
/mnt/archive4/DEV/swordgal"` is empty — other Unity processes are usually holding *other* projects
and are not a reason to leave it.
