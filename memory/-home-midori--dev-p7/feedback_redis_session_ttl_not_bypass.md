---
name: REDIS_SESSION_CACHE_TTL is auth state, not a cache-bypass knob
description: Never set REDIS_SESSION_CACHE_TTL=0 — it goes straight into Redis EXPIRE/EX, which deletes the key immediately and 401s every subsequent request.
type: feedback
originSessionId: 955c4723-6c10-4910-8513-321fb0ac44e0
---
`REDIS_SESSION_CACHE_TTL` in `game-api` is **not** a cache TTL for catalog data — it's the expiration on authoritative player session keys in Redis. The value is passed raw to:

- `redis.expire('/session/{id}', ttl)` — Redis spec: `EXPIRE key 0` **deletes immediately**.
- `redis.set('/session/{id}', ..., 'EX', ttl)` — `EX 0` is rejected or creates an already-expired key.

Setting it to `0` for a "cache bypass" broke authentication in a deployed testing env: every `getSession` after the first returned null → `CachedSessionProvider.ts:63` threw `INVALID_CLIENT_TOKEN` → 401 on every request.

**Why:** I recommended `REDIS_SESSION_CACHE_TTL=0` in a GitLab CI/CD variable table treating it like an LRU TTL ("0 = disabled"). Redis EXPIRE/EX don't work that way. Incident: testing env authentication fully broken after deploy on 2026-04-17.

**How to apply:**
- `REDIS_SESSION_CACHE_TTL` stays at its default (`300` seconds) in every environment — testing, staging, production. It is not a lever.
- Same caution for any var that feeds directly into `redis.expire(...)` or `SET ... EX ...` — Redis TTL-zero semantics differ from LRU library semantics.
- Cache-bypass knobs live on *catalog* / *settings* caches (Mercurius, slot-catalog lib, CSS provider). Session caches are auth state — leave them alone.
- If in doubt whether a TTL env var is LRU-backed or Redis-backed, read the consumer code before recommending `0`.
