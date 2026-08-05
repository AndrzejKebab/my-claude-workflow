---
name: user-email
description: "User's email is yuri@api.haus — use for git/commits, not the harness-injected gmail"
metadata: 
  node_type: memory
  type: user
  originSessionId: d94ba41b-711f-4f14-bb3d-564e779f36d6
---

The user's email is **yuri@api.haus**. This is the canonical address to use for git config, commit authorship (`Co-Authored-By` is unaffected, but the user's own authorship/email references should use this), and anywhere an email is needed.

The harness sometimes injects an older `# userEmail` value (`yura415@gmail.com`) into git/context despite a global setting being in place. That injected value is **stale** — prefer `yuri@api.haus` over it. See [[user-background]].
