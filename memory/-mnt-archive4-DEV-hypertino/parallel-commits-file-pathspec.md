---
name: parallel-commits-file-pathspec
description: "Parallel agents in one worktree must commit with per-FILE pathspecs — directory pathspecs sweep siblings' uncommitted edits"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 069108a5-de18-445a-9999-df2891ddd754
---

Observed 2026-07-06 (spec-book orchestration): two parallel agents briefed with `git commit -- docs/spec docs/orchestrate/spec-book` swept each other's mid-edit files into their commits — a directory pathspec commits the working-tree state of everything under the directory, not just the agent's own staged files.

**Why:** content survives but attribution mixes, and a sibling's PARTIAL edit state can be committed mid-write; unwinding needs history rewrite on a shared branch (risky while sessions are live).

**How to apply:** when briefing agents that may run concurrently in the same worktree, the commit instruction lists explicit FILES (`git commit -- <file1> <file2> ...`), never directories, whenever another agent could be editing under the same tree. Directory pathspecs are safe only for a solo agent or disjoint directory ownership. Related: [[orca-orchestration-mail-pull]].
