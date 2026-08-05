---
name: No git push
description: cc-filter blocks git push — never attempt it, only the user pushes
type: feedback
---

Never run `git push` — the cc-filter hook physically blocks it.

**Why:** User's security policy enforced via pre-tool hook.
**How to apply:** After committing in submodules or the main repo, tell the user the commit is ready and let them push manually.
