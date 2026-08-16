---
name: rtk-compacts-agent-shell-output
description: "a PreToolUse hook proxies every bare command in an agent Bash call through rtk, which compacts output — counts and lists come back short"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f34b3ade-1c50-43d6-b6a8-427dc6799447
  modified: 2026-08-15T03:22:00.556Z
---

`~/.claude/settings.json` wires `rtk hook claude` as a **PreToolUse hook on `Bash`**, so every bare
command name in an agent shell call is proxied through rtk whether or not the agent typed `rtk`.
rtk's job is to "filter and summarize system outputs before they reach your LLM context", so a long
list comes back truncated and `grep -c` can answer with a summary instead of a number.

Measured 2026-08-15 in `gaming-platform-service`:

- `git log --oneline master..HEAD | wc -l` → **50**; `/usr/bin/git log … | wc -l` → **59**
- `git log --oneline master..HEAD | grep -c .` → **59** (inconsistent between pipes, same command)
- `git log --format='%h %s' master..HEAD | grep SLOTS-208` → no match, though the commit is there
- node child processes are never proxied, so `pnpm docs:writing` and `pnpm test:precommit` are true

**Why:** a branch was read at nine commits short for five sessions, and those nine turned out to be
another team's work sitting in the pull request's diff with nothing explaining it. A compacted list
reads exactly like a complete one.

**How to apply:** for anything a document will quote, call the binary by absolute path —
`/usr/bin/git`, `/usr/bin/grep`, `/usr/bin/wc`. Bare names are fine for browsing. Resolving refs to
SHAs first does **not** help; the path is what matters. The repo carries this rule in
`.agents/skills/rtk/SKILL.md`, "Never take a measurement through rtk". Supersedes the older claim
that `/usr/bin/git` does not bypass the wrapper — it does.
