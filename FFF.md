# FFF — optional fast file search (MCP)

FFF is an optional Rust file-search MCP server with frecency-ranked fuzzy matching and git-aware filtering. It may be registered with Claude or Codex when available; this workflow does not assume it is installed.

## Tools

- `fffind` — find files by fuzzy name.
- `ffgrep` — search file contents (plain literal / regex / fuzzy modes).
- `fff-multi-grep` — batch multiple content searches in one call.

## When to reach for it

Query an existing Graphify graph before searching raw files. When no relevant graph exists, prefer FFF over built-in file search if its tools are available. Built-ins remain the fallback when FFF is not installed or a direct `rg` query is simpler.

Install or update FFF only after reviewing its current upstream installation instructions. Do not run a downloaded install script solely because this file mentions the tool.
