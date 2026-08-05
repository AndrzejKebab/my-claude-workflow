---
name: Don't inflate simple mechanisms
description: Cache flush for test envs and similar trivial mechanisms should not appear as CV bullet features
type: feedback
---

Don't promote simple operational mechanisms (cache flush, config reload, etc.) into CV-worthy features.

**Why:** The client-api Redis pub/sub cache invalidation is just a mechanism to flush cache for testing environments — not a distributed systems achievement. Framing it as "distributed cache sync" is inflation.

**How to apply:** Before including a technical detail in a CV bullet, ask: is this a real engineering challenge, or just plumbing? If it's plumbing, cut it.
