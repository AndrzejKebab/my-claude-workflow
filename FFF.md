# FFF — fast file search (MCP)

Rust file-search toolkit exposed as a user-scoped MCP server (`fff-mcp`, registered in `~/.claude.json`). Frecency-ranked fuzzy matching, git-aware filtering, sub-10ms on large repos.

## Tools

- `fffind` — find files by fuzzy name.
- `ffgrep` — search file contents (plain literal / regex / fuzzy modes).
- `fff-multi-grep` — batch multiple content searches in one call.

## When to reach for it

Prefer the `fff` MCP tools over the built-in `Glob`/`Grep` for file-name and content search — they are faster on large trees and frecency-rank recently-touched files first. Built-in tools remain fine for one-off greps where fff isn't loaded yet.

Unlike `rtk` (a transparent CLI proxy installed via hook — zero-token, auto-rewrites commands), `fff` is opt-in: it only helps when I actually call its tools instead of the defaults.

Update the binary by re-running the installer: `curl -fsSL https://dmtrkovalenko.dev/install-fff-mcp.sh | bash`.
