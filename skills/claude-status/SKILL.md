---
name: claude-status
description: Inspect local Claude Code session activity and associated Git worktrees without modifying sessions or repositories.
---

# Claude session status

Run `claude-status.sh` to summarize the JSONL sessions under `~/.claude/projects`.

```bash
claude-status.sh
claude-status.sh --here
claude-status.sh --attention
```

- The default view shows every discoverable project and its sessions.
- `--here` limits output to the current repository or worktree.
- `--attention` shows sessions older than 24 hours whose associated Git working tree currently has changes.

The script reads each session's recorded `cwd`; it does not reconstruct paths from Claude's encoded directory names. It supports Windows paths when run through Git Bash and includes staged, unstaged, and untracked files in the Git summary.

This is a read-only diagnostic. An `ATTENTION` result is only a heuristic: it does not prove that the old session created or owns the current working-tree changes. Inspect the session and `git status` before deciding what to resume, archive, commit, or remove.

This skill reports Claude Code sessions only. Use Codex's task interface for Codex task status.
