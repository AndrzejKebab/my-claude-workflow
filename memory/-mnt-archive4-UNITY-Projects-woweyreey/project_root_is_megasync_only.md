---
name: woweyreey root repo is MEGASync-only, never pushed, never branched
description: Root repo is too large for GitHub LFS budget and syncs to MEGASync instead of being pushed. Never push the root, never branch the root. Submodules are the only thing that gets branched and pushed.
type: project
originSessionId: 42962e51-34e2-4a27-9eb4-f52e6dddfdb7
---
The woweyreey root repo is **synced to MEGASync, never pushed to GitHub** — it's too large for GitHub LFS without overpaying. Submodules under `Packages/` are the only repos that get pushed to GitHub.

**Why:** GitHub LFS pricing tiers don't match the root repo's size (Unity project with art assets, scenes, large binaries). MEGASync handles the bulk-asset replication; GitHub handles the code in the submodules.

**How to apply:**
- Never run `git push` from the root repo. The user pushes submodules manually; root never pushes.
- Never create a branch in the root repo. Even when the user says "branch this", they mean **inside the relevant submodule** — never a matching branch in the root.
- This matches and explains the existing project rule in `CLAUDE.md`: "Never create a branch in the root repo unless explicitly asked. When asked to branch on a submodule, branch ONLY inside the submodule — never create a matching branch in the root repo."
- For checkpoint commits in the root, commit-only-don't-push is the universal pattern. Sub-agents instructed to commit must not push.
