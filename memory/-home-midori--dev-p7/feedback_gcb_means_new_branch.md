---
name: gcb means git checkout -b
description: When user says "gcb, commit, preflight" — gcb means create a new branch with git checkout -b before committing
type: feedback
originSessionId: 306ab5d2-5e1b-4595-a071-702ca9bbb48a
---
"gcb" = `git checkout -b <branch>` — create a new feature branch before committing.

**Why:** User expects work to land on a feature branch, not master/main. Committing directly to master is wrong.

**How to apply:** When the user says "gcb, commit, preflight", the sequence is:
1. `git checkout -b <branch>` (conventional branch name from the changes)
2. Run preflight (`pnpm lint:fix && pnpm test` or equivalent)
3. Commit all changes
