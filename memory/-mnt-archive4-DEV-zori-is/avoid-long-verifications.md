---
name: avoid-long-verifications
description: "For zori.is, don't block on dev-server spin-ups or full e2e waits — verify fast, user checks visually"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: eaac5e27-13eb-491d-af70-b013457a4a05
---

On zori.is the user runs the app live in their own browser and verifies UI changes visually. They twice interrupted me polling for the Vite dev server to come up, and said "please avoid these long running verifications."

**Why:** the Vite dev server does a cold debug cargo build on first start (minutes), and the dev server bound the port but didn't respond for ~10 min once. Blocking on it (or on a full Playwright run that waits on that server) wastes the user's time when they can already see the change.

**How to apply:** for JS/CSS HUD/UI edits (e.g. [[project-lighthouse-falling-sand]]), rely on fast checks — `node --check` for syntax, and at most `npm run build` (release cargo is cached → fast, ~0.5s vite). Don't start `npm run dev` or run Playwright unless the user explicitly asks. JS edits hot-reload in the user's own session, so they confirm visuals themselves. The black-box e2e (`tests/events-hud.spec.js`) still exists for when a full verify is wanted — just don't force it.
