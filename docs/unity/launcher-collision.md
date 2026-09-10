# Distinguishing the Unity Editor launcher from Unity CLI

Unity CLI commands and this repository's Editor wrapper solve different
problems, but both may be invoked with names containing `unity`. Do not rely on
PATH order when automation needs one specific tool.

## The two tools

- **Unity CLI** communicates with or controls a supported Unity Editor workflow.
  Commands in this repository include `unity-cli console` and the
  `unity-cli-recompile` helper.
- **`bin/unity-editor`** is this repository's Editor launcher. It reads the
  project's Unity version and starts the matching Editor, including synchronous
  batch-mode execution when requested.

`bin/unity` remains a compatibility alias for `unity-editor`. An official or
separately installed CLI may also claim the bare `unity` command, so scripts
should use the unambiguous command they actually require.

## Check resolution on Windows

In PowerShell:

```powershell
Get-Command unity -All | Select-Object CommandType, Source, Definition
Get-Command unity-editor -ErrorAction SilentlyContinue
Get-Command unity-cli -ErrorAction SilentlyContinue
```

In Git Bash:

```bash
type -a unity
type -a unity-editor
type -a unity-cli
```

The first PATH match wins. A successful command is not proof that the intended
binary ran.

## Which command to use

- Launch the Editor or run batch mode with `unity-editor`.
- Inspect or control a supported live Editor with `unity-cli`.
- Recompile through the repository helper with `unity-cli-recompile`.
- Use bare `unity` only for interactive compatibility when its resolution has
  been checked.

For scripts outside this repository, invoke an absolute path or configure a
clearly named project variable rather than depending on global PATH ordering.

## Installation check

`install.sh` reports what the bare `unity` command resolves to. A warning is
informational: it does not mean Unity CLI is invalid. It means automation should
choose `unity-editor` or `unity-cli` explicitly instead of assuming what
`unity` means.

## Live Editor versus batch mode

Unity normally locks a project to one Editor instance. If that project is open,
do not start a second batch-mode Editor against the same path. Use the live-
Editor CLI workflow where supported, or close the Editor before running the
batch-mode wrapper. Validate liveness with the actual process, project lock,
and recent Editor log rather than a stale heartbeat alone.
