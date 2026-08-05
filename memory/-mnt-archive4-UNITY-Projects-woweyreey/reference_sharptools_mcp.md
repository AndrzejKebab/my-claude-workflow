---
name: SharpToolsMCP install location
description: Where the SharpTools MCP server lives, how it's registered with Claude Code, and how to update it
type: reference
originSessionId: 41ada086-5faa-4bed-be8f-5350b5f879af
---
- Repo: `/home/midori/_dev/SharpToolsMCP` (cloned from https://github.com/kooshi/SharpToolsMCP)
- Stdio binary: `SharpTools.StdioServer/bin/Release/net8.0/SharpTools.StdioServer` (net8.0 — needs .NET 8 SDK + runtime)
- Registered with Claude Code as `sharptools` at **user scope** in `~/.claude.json` — survives restarts because Claude Code launches the binary on demand per session (no daemon to supervise)
- Logs: `/home/midori/_dev/SharpToolsMCP/logs`
- Update: `/home/midori/_dev/SharpToolsMCP/update.sh` (git pull + `dotnet build -c Release` + smoke test); next Claude Code session picks up the new binary automatically
- Verify: `claude mcp list` (should show `sharptools - ✓ Connected`)
- Remove: `claude mcp remove sharptools -s user`
