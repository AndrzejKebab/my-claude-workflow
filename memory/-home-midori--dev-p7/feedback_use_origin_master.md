---
name: use_origin_master
description: Always compare branches against origin/master, not local master which may be stale
type: feedback
---

Always fetch and compare against `origin/master` (not local `master`) when analyzing branches and diffs.

**Why:** Local master can be stale. The user doesn't care about local master — origin/master is the source of truth.

**How to apply:** Run `git fetch origin` first, then use `origin/master` in all diff/log/merge-base comparisons.
