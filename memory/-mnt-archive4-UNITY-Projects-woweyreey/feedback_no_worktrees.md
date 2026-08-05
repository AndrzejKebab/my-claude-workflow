---
name: Never use isolated worktrees for sub-agents on this project
description: This Unity project's sub-agents must always work in the main working tree, never in `isolation: "worktree"` mode.
type: feedback
originSessionId: 0c8013cd-69a6-4fef-b80c-ef328fedf212
---
When dispatching sub-agents on this project, **never** pass `isolation: "worktree"` to the Agent tool. Agents always operate directly on the main working tree.

**Why:** This project's sub-agent verification path requires the live Unity editor, which is bound to the main checkout. A worktree-isolated agent cannot run `unity-cli editor refresh`, `unity-cli console`, or `unity-cli test` against its isolated copy — those commands target the editor instance attached to the primary checkout. Working in isolation defeats the entire verification loop.

**How to apply:**
- Default to omitting the `isolation` parameter entirely (the default is "no isolation" — main tree).
- If a killed/stopped agent leaves partial edits in the working tree, those edits **are** the current state of the project. Do not "recover" them; just dispatch the next agent to continue from where the prior one stopped. Use `git status` / `git diff` to review state if needed, then brief the next agent on what's already in the tree.
