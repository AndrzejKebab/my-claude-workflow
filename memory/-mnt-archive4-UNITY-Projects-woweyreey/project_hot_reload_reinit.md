---
name: Hot reload re-initialization design question
description: Should hot reload re-run start() when component code changes? Requires script diffing.
type: project
---

Hot reload currently rewires prototypes (`Object.setPrototypeOf`) so `update()` uses new code, but does NOT re-run `start()`. This means:
- New method implementations execute immediately
- But entity state from old `start()` persists (possibly stale)

**Open question:** Should hot reload detect if `start()` changed and re-initialize affected entities?

**Why:** Modders editing components during play expect new `start()` logic to take effect. But implicit re-initialization might not be their intent (e.g., they only changed `update()` and want to keep accumulated state).

**How to apply:** Future work — diff pre/post reload scripts to detect `start()` changes. If changed, offer re-initialization. This is a design decision, not a bug.
