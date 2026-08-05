---
name: no-local-typecheck-gate
description: Nothing local runs typecheck — the post-edit hook and commit gate stop at format + lint
metadata: 
  node_type: memory
  type: project
  originSessionId: 480368ee-90b1-4c70-9853-5348f7654aa8
  modified: 2026-07-23T16:25:19.739Z
---

No hook in this repo runs `tsc`. The post-edit hook is biome-only, and the commit gate is
format + lint. A branch can be green on every hook and still fail CI's `pnpm typecheck`.

**Why:** cold across the 19 packages `pnpm typecheck` measures **26.2 s** (2026-07-23), against
the 30 s `PreToolUse` timeout that `.agents/scripts/hook-config.mjs` generates into
`.claude/settings.json` — it would flake as a commit gate. Warm with a turbo cache hit it is
1.4 s, so adding it means raising that generated timeout, not just adding a command.

**How to apply:** run `pnpm typecheck` yourself before calling work done, especially after a
multi-edit refactor where the type error is a dangling reference no linter can see. Green
hooks are not evidence the types hold. See [[verify-real-functionality]].
