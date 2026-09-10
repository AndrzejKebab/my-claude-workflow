# Decompilation workflow — finding the truth

Use this workflow when a Unity API signature, overload, attribute, or internal
behavior is unclear. Prefer shipped source over decompiled assemblies.

This machine uses:

- Unity Hub application: `F:\Unity Hub\Unity Hub.exe`
- Unity Editors: `F:\Unity Editors\<version>\`

The examples below use PowerShell and keep `<version>` as a placeholder so they
survive Editor upgrades.

## Tier checklist

1. Search the project's `Library/PackageCache`.
2. Search the selected Editor's built-in package sources.
3. Use Rider's declaration/decompiler view or another IDE decompiler.
4. Use `ilspycmd` when a searchable local source dump is useful.

## Tier 0 — project `Library/PackageCache`

Many Unity packages ship their C# source directly with the project:

```powershell
Get-ChildItem -Directory .\Library\PackageCache |
    Where-Object Name -Like 'com.unity.*'

rg -n "ScheduleParallel" .\Library\PackageCache\com.unity.collections@* .\Library\PackageCache\com.unity.entities@*
```

This is the best source for Entities, Collections, Burst, Mathematics, and
other package APIs because it matches the versions resolved by the project.
Treat `Library/PackageCache` as read-only; edit a package only after embedding
it through Unity Package Manager.

## Tier 1 — Editor built-in packages

Some packages and package metadata ship with the Editor:

```powershell
$unityEditorRoot = 'F:\Unity Editors\<version>\Editor'
$builtInPackages = Join-Path $unityEditorRoot 'Data\Resources\PackageManager\BuiltInPackages'

Get-ChildItem -Directory -LiteralPath $builtInPackages
rg -n "symbolName" $builtInPackages
```

Replace `<version>` with the Editor version used by the project, such as
`6000.7.0a6` on this machine.

## Tier 2 — Unity engine DLLs

Core `UnityEngine` APIs, including much of `Unity.Jobs`, live in managed engine
assemblies rather than PackageCache:

```powershell
$unityEditorRoot = 'F:\Unity Editors\<version>\Editor'
$managedRoot = Join-Path $unityEditorRoot 'Data\Managed\UnityEngine'

Get-ChildItem -LiteralPath $managedRoot -Filter '*.dll'
```

For job-system types, start with:

```text
UnityEngine.CoreModule.dll
```

### Rider or another IDE decompiler

Use “Go to Declaration” on the symbol. If source is unavailable, Rider can
show a decompiled declaration from the referenced assembly. This is usually
the fastest way to confirm one overload or member without depending on the
IDE's private cache layout.

### `ilspycmd` for searchable output

Install once:

```powershell
dotnet tool install --global ilspycmd
```

Choose a task-local output directory, then decompile the module:

```powershell
$unityEditorRoot = 'F:\Unity Editors\<version>\Editor'
$assemblyPath = Join-Path $unityEditorRoot 'Data\Managed\UnityEngine\UnityEngine.CoreModule.dll'
$outputPath = Join-Path $env:TEMP 'unity-coremodule-decompiled'

ilspycmd --project --outputdir $outputPath $assemblyPath
rg -n "IJobParallelForExtensions|innerloopBatchCount" $outputPath
```

If `ilspycmd --project` produces many files, that is useful for symbol search
and stable file-level citations. Recreate the output after changing Unity
versions; decompiled line numbers are not stable across versions.

## Example: verify a scheduling overload

To check the public parameter name for `IJobParallelFor.Schedule`:

1. Search `Library/PackageCache` in case the relevant interface ships as
   package source.
2. Navigate to `IJobParallelForExtensions.Schedule` in Rider, or decompile
   `UnityEngine.CoreModule.dll`.
3. Confirm the public signature rather than copying an internal field name.
4. Record the result in [`scheduling-overloads.md`](scheduling-overloads.md)
   with the Unity or package version used for verification.

This distinguishes public names such as `innerloopBatchCount` from internal
implementation names such as `BatchSize`.

## Online documentation

Unity's online documentation is useful for concepts and supported behavior,
but it may show a different package or Editor version. For exact overloads and
source-generator behavior, prefer the source or assemblies installed for the
current project.

## See also

- [`scheduling-overloads.md`](scheduling-overloads.md) — verified scheduling signatures.
- [`job-types.md`](job-types.md) — choosing the appropriate job interface.
- [`../burst/verification.md`](../burst/verification.md) — verifying Burst compilation.
