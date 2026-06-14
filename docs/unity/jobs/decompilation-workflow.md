# Decompilation workflow — finding the truth

How to verify a Unity API signature without trusting an LLM's recollection. Tiered by ergonomics: pick the lowest-friction tier that actually has the file you need.

## Tier 0 — `Library/PackageCache/com.unity.<pkg>@<hash>/`

If the type lives in a Unity package shipped as source (`Unity.Collections`, `Unity.Mathematics`, `Unity.Burst`, `Unity.Entities`, `Unity.Jobs.LowLevel.Unsafe` extensions, etc.), it is **already on disk**:

```bash
ls /mnt/archive4/UNITY/Projects/woweyreey/Library/PackageCache/ | grep com.unity.
```

Read the source directly. Cite `file:line` exactly. No tooling needed.

Examples:
- `IJobParallelForBatch` → `Library/PackageCache/com.unity.collections@12999e356c23/Unity.Collections/Jobs/IJobParallelForBatch.cs:18`
- `[BurstCompile]` → `Library/PackageCache/com.unity.burst@6bb9aca3ef38/Runtime/BurstCompileAttribute.cs`
- `IJobEntity` → `Library/PackageCache/com.unity.entities@8b72e8a7d7d1/Unity.Entities/IJobEntity.cs`

## Tier 1 — Editor `BuiltInPackages/`

URP, HDRP, Core RP, Shader Graph, and a few engine-adjacent packages live under the Editor install:

```
/home/midori/Unity/Hub/Editor/6000.3.14f1/Editor/Data/Resources/PackageManager/BuiltInPackages/
  com.unity.render-pipelines.core/
  com.unity.render-pipelines.universal/
  com.unity.shadergraph/
  ...
```

These are the canonical RenderGraph / URP / HDRP sources cited throughout `docs/unity/rendergraph/`. Source-shipped, no decompilation needed.

## Tier 2 — DLL types (engine modules)

Many core types — `IJob`, `IJobFor`, `IJobParallelFor`, `JobHandle`, `JobsUtility`, `Transform`, `GameObject`, etc. — live in **engine module DLLs** (`UnityEngine.CoreModule.dll`, `UnityEngine.PhysicsModule.dll`, …) under:

```
/home/midori/Unity/Hub/Editor/6000.3.14f1/Editor/Data/Managed/UnityEngine/
```

There is **no source on disk** for these. Three options:

### 2a. Rider DecompilerCache (free if Rider has already shown the file)

Rider's resharper-host caches every type it decompiles for goto-definition / IL viewer:

```
~/.config/JetBrains/Rider2025.3/resharper-host/DecompilerCache/decompiler/
  <assembly-mvid>/<bucket>/<hash>/<TypeName>.cs
```

The MVID is `<hex>200` (the trailing `200` comes from Rider's bucketing scheme — note it in the path). To find a type:

```bash
find ~/.config/JetBrains/Rider*/resharper-host/DecompilerCache/decompiler -name 'JobHandle.cs'
# /home/midori/.config/JetBrains/Rider2025.3/.../JobHandle.cs
```

**Requires Rider to have already opened that type** (goto-definition, ⌘B, or just navigation). If the file isn't in cache, this tier is empty for that type.

### 2b. SharpTools MCP (Roslyn workspace + ILSpy decompile fallback)

`mcp__sharptools__*` (registered as `sharptools` in `~/.claude.json`; install at `~/_dev/SharpToolsMCP`) loads the project's `.sln` / `.csproj` into a real Roslyn workspace, then exposes LSP-grade tools:

- `SharpTool_LoadSolution` / `SharpTool_LoadProject` — initialise the workspace.
- `SharpTool_SearchDefinitions` — fuzzy-search any symbol across the solution **and its referenced assemblies** (engine DLLs included).
- `SharpTool_ViewDefinition` — return the source for a symbol. Resolution order: SourceLink → embedded PDB → **ILSpy-based decompilation**. Same fallback chain Rider uses.
- `SharpTool_GetMembers` / `SharpTool_FindReferences` / `SharpTool_ListImplementations` — navigate.

This is the closest equivalent to "Rider but headless" available from the agent. Use it when:
- You need a type that isn't in Rider's DecompilerCache yet.
- You want to sanity-check a Schedule overload before writing a call site.
- You need to enumerate all implementations of an interface (e.g. every `: IJobChunk` in the project + packages).

For the woweyreey project the solution path is `Assembly-CSharp.sln` at the project root.

### 2c. `ilspycmd` (bulk decompile any DLL)

Last-resort tier when SharpTools' workspace doesn't reach the assembly you want, or when you want a single big text dump for grep:

```bash
# One-time install (the cwd flag avoids the multi-csproj conflict):
cd /tmp && dotnet tool install -g ilspycmd

# Decompile UnityEngine.CoreModule into one file:
mkdir -p /tmp/unity-decompile/CoreModule
ilspycmd /home/midori/Unity/Hub/Editor/6000.3.14f1/Editor/Data/Managed/UnityEngine/UnityEngine.CoreModule.dll \
  -o /tmp/unity-decompile/CoreModule
```

Output: a single `UnityEngine.CoreModule.decompiled.cs` (~175k lines for CoreModule). Find a type with grep:

```bash
grep -nE 'public (interface|static class|struct) (IJobFor|IJobParallelFor|JobHandle)' \
  /tmp/unity-decompile/CoreModule/UnityEngine.CoreModule.decompiled.cs
```

Cite as `UnityEngine.CoreModule.decompiled.cs:<line>` — line numbers are stable for a given decompile output, so the citation survives until you re-run `ilspycmd`.

`ilspycmd` is on PATH at `~/.dotnet/tools/ilspycmd` after install. If `which ilspycmd` returns "not found", the install might have skipped PATH wiring; run via `~/.dotnet/tools/ilspycmd` directly.

## Tier comparison

| Tier | Tool                      | Setup            | When to use                                                  |
|------|---------------------------|------------------|--------------------------------------------------------------|
| 0    | `Library/PackageCache/`   | none             | Source-shipped Unity packages. Fastest.                      |
| 1    | `Editor/.../BuiltInPackages/` | none         | URP/HDRP/Core RP/Shader Graph.                               |
| 2a   | Rider `DecompilerCache/`  | open file in Rider once | Type already navigated to in Rider. Free.            |
| 2b   | SharpTools MCP            | `LoadSolution`   | Programmatic browse of any referenced DLL.                   |
| 2c   | `ilspycmd`                | one-time install | Bulk grep / line-number citations / mass extraction.         |

## Concrete recipe — "is `batchSize:` valid here?"

Given an LLM-suggested `job.Schedule(N, batchSize: 64)`, in increasing rigour:

1. **Determine the job interface.** Read the struct's declaration (e.g. `: IJobParallelFor`).
2. **Tier 0 lookup**: if the interface lives in `com.unity.collections`, grep its file for `Schedule<T>(`:
   ```bash
   grep -nE 'Schedule.*\(' /mnt/archive4/UNITY/Projects/woweyreey/Library/PackageCache/com.unity.collections@*/Unity.Collections/Jobs/IJobParallelForBatch.cs
   ```
3. **Tier 2** (engine interfaces): use SharpTools `SharpTool_ViewDefinition` on `Unity.Jobs.IJobParallelForExtensions.Schedule`, or `ilspycmd` and grep on the line emitted at `:2498`.
4. Inspect the parameter names; named-arg cheat sheet in [`scheduling-overloads.md`](scheduling-overloads.md) §"Named arguments cheat sheet".

The first tier that resolves wins. There is no need to escalate to ilspy if the source is in `Library/PackageCache/`.

## What about Unity's online docs?

`docs.unity3d.com/6000.3` is **not authoritative** for engine-module types — many ScriptReference URLs return 404 against the 6.3 doc tree, and the prose often differs from the actual signatures. The **package** ScriptReference (e.g. `docs.unity3d.com/Packages/com.unity.collections@2.x/api/...`) is more reliable for source-shipped packages.

Engine types decompiled from `UnityEngine.CoreModule.dll` carry inline XML doc comments — those came from `UnityEngine.CoreModule.xml` shipped alongside the DLL and are the canonical doc strings. Read the comment in the decompile, not the website.

## See also

- [`scheduling-overloads.md`](scheduling-overloads.md) for the named-argument cheat sheet that motivated this workflow.
- `docs/unity/rendergraph/index.md` for the equivalent setup applied to RenderGraph.
- `~/.claude/CLAUDE.md` references `~/_dev/SharpToolsMCP` install + `update.sh`.
