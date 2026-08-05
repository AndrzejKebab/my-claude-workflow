---
name: tokf filter usage
description: How to use tokf for filtering command output — never read raw persisted output files
type: reference
---

`tokf` is installed as a Claude Code PreToolUse hook that rewrites Bash commands to filter output.

**How it works:**
- Hook rewrites `scripts/run-tests.sh ...` → `tokf run scripts/run-tests.sh ...`
- Filter extracts only test summary lines (`total=N passed=N failed=N`)
- Filtered output is what Claude sees — no Vulkan noise, no Unity boot spam

**Rules:**
- Test runner output is already clean (logs go to `/tmp/unity-test.log`, not stdout)
- tokf further filters to just summary + failure lines
- Never pipe test commands (`| tail`, `| grep`) — output is already minimal
- Never read raw persisted output files — trust the Bash tool result
- For debugging failures: read `/tmp/unity-test-results.xml` or `/tmp/unity-test.log`

**To customize filters:**
```bash
tokf ls                          # list available filters
tokf show scripts/run-tests      # show current filter
tokf eject scripts/run-tests     # copy to local config for editing
```
