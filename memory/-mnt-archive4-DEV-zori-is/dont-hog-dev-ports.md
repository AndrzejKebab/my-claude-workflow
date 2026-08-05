---
name: dont-hog-dev-ports
description: "zori.is — don't start/restart preview/dev servers; the user runs their own, ports are shared across worktrees"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 78912f78-e52f-4134-a980-8e50b02dcd3c
---

Do NOT spin up `npm run preview` / `just preview-mobile` / `vite dev` servers to verify zori.is changes. The user runs their own preview and verifies visually.

**Why:** zori.is lives in several git worktrees (e.g. `localization`, `haptics`, `optimize-pass`, `particle-fix`) that ALL default to port 5173. Starting a server there collides with whatever the user (or another worktree) already has bound — and repeated background restarts leave orphaned detached `vite preview`/`workerd` processes that keep grabbing the port. In one session this led to testing the wrong worktree's stale build for several rounds.

**How to apply:** verify changes at the source/build level only — `node --check`, `npm run build` (the i18n coverage gate), grep the emitted `dist/`. If a running server is truly needed, ask the user to run it (`! just preview-mobile`) rather than starting one yourself, and never leave background servers running. Complements [[avoid-long-verifications]].
