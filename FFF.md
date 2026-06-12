# FFF — fast file search (MCP)

Rust file-search toolkit exposed as a user-scoped MCP server (`fff-mcp`, registered in `~/.claude.json`). Frecency-ranked fuzzy matching, git-aware filtering, sub-10ms on large repos.

## Tools

- `fffind` — find files by fuzzy name.
- `ffgrep` — search file contents (plain literal / regex / fuzzy modes).
- `fff-multi-grep` — batch multiple content searches in one call.

## When to reach for it

Prefer the `fff` MCP tools over built-in `Glob`/`Grep` — faster on large trees, frecency-ranks recently-touched files first. Built-ins remain fine for one-off greps where fff isn't loaded yet. Unlike `rtk` (hook-installed, automatic), `fff` is opt-in — it only helps when its tools are actually called.

Update the binary: `curl -fsSL https://dmtrkovalenko.dev/install-fff-mcp.sh | bash`.
