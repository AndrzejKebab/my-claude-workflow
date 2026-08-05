---
name: Avoid delayCall for blocking operations
description: Use long unity-cli --timeout instead of delayCall + polling — delayCall requires editor focus to fire
type: feedback
---

Don't use `EditorApplication.delayCall` to work around blocking calls like `BuildPlayer`. Instead, call the method directly with a long `--timeout` on unity-cli.

**Why:** delayCall only fires when the editor is focused/ticking. If Unity is in the background, the callback never executes and the script hangs indefinitely.

**How to apply:** For any unity-cli exec call that triggers a long-running blocking operation, use `--timeout 600000` (10 min) and call the method directly.
