# Codebase Navigation

Use the best available repository index before broad manual search.

## Search Order

1. Query an existing Graphify graph when `graphify-out/graph.json` is present.
2. Read the source files identified by Graphify.
3. Use FFF for filename and content search when the graph lacks the required detail.
4. Fall back to `rg`, file listing, and direct reads.

Do not build a Graphify graph for an ordinary lookup. Creating a graph requires an explicit `/graphify` request. Treat graph results and memory as navigation leads, then verify important claims against current source and configuration.

## Graphify Integration

Install or refresh Graphify's agent integration for each provider:

```powershell
graphify install --platform claude
graphify install --platform codex
```

Run these commands again after upgrading Graphify when the CLI reports that an installed skill is older than the package.

Inside a project that already maintains `graphify-out/`, install the repository hook:

```powershell
graphify hook install
```

The hook refreshes the graph after commits. Keep project-specific Graphify requirements in that project's `AGENTS.md`; do not duplicate installation instructions in every project.

## Query Operations

```powershell
graphify query "How does the save pipeline work?"
graphify explain "WorldSaveContext"
graphify path "BlockEditInputSystem" "ChunkMeshingSystem"
```

- Use `query` for a natural-language codebase question.
- Use `explain` for one symbol or concept.
- Use `path` for the relationship between two symbols or systems.

Read the returned source locations before editing code. If Graphify is missing, stale, or unable to answer, continue with FFF and normal repository tools and report that limitation accurately.

## FFF Integration

Register FFF as a global MCP server with an absolute executable path so desktop sessions do not depend on inherited shell `PATH` state. FFF indexes the active task's project root; open the task in the intended repository before testing searches.

Use FFF content search for known identifiers and filename search when locating a file or module. Keep queries short and use multi-pattern search for naming variants.

## Related Documentation

- [Durable memory](durable-memory.md)
- [Evidence-based review](evidence-based-review.md)
- [Game-development reference](README.md)
