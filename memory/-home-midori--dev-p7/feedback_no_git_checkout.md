---
name: no-git-checkout
description: Never use git checkout to restore files — manually edit them instead
type: feedback
---

Do not use `git checkout origin/master -- <file>` to restore files.
**Why:** User considers it a destructive operation that can silently overwrite work.
**How to apply:** When reverting changes to specific files, manually edit them back to the correct state using the Edit tool.
