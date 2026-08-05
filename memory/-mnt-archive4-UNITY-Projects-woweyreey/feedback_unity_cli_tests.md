---
name: unity-cli test discipline
description: Never run concurrent unity-cli test commands; only run full UnityJS suite on big refactors or when requested
type: feedback
---

Never run more than one `unity-cli test` command at a time — especially not when another is running in background.

**Why:** Unity test runner can only handle one session at a time. Running a second command while one is backgrounded causes connection errors (EOF) and wastes time.

**How to apply:**
- Wait for any running test to finish before starting another.
- Full suite (`--filter "UnityJS"`) takes ~10 minutes — only run it on big refactors, architectural changes, or when explicitly requested.
- For targeted changes, run only the specific relevant test filter.
