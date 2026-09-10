# Unity Editor crash forensics

A native Unity crash log often contains failures from the crash reporter,
signal handler, or managed-runtime unwinder after the original fault. Do not
assume the last visible stack is the fault site. Correlate the Editor log,
native crash dump, process memory, and the last operation performed.

## Preserve evidence first

Before reopening the project repeatedly, copy the relevant artifacts to a
task-local directory:

- `Editor.log` and any batch-mode log specified with `-logFile`.
- Crash dump (`.dmp` on Windows, core dump on Linux).
- `error.log`, crash-report metadata, and native stack trace when present.
- The exact Unity Editor version, command line, project revision, and active
  native plugins.
- The last successful and failed test/build command.

On Windows, Unity's Editor log is normally under:

```text
%LOCALAPPDATA%\Unity\Editor\Editor.log
```

Use a dedicated `-logFile` for automated runs so concurrent attempts do not
overwrite or interleave the same log.

## Read the crash chain carefully

- An access violation near a small address such as `0x39` often means a null
  pointer plus a field offset, but it does not identify why the pointer was null.
- Managed-runtime or crash-handler frames may be secondary failures while Unity
  is trying to print diagnostics or shut down.
- Missing test-result XML can mean the process died before the test runner
  flushed results; the Editor log and exit code become the primary evidence.
- Burst, graphics drivers, native plugins, unsafe collections, and engine bugs
  can all fail outside managed exception handling.

## Windows workflow

1. Reproduce with one Editor instance and a dedicated log.
2. Check system and GPU memory pressure during the run.
3. Open the `.dmp` in Visual Studio or WinDbg.
4. Load Microsoft, Unity, plugin, and game-native symbols when available.
5. Inspect the exception code, faulting thread, module, instruction address,
   registers, and native call stack.
6. Compare the module offset against the exact binary from the crashing Editor
   or player build.

Useful PowerShell checks:

```powershell
Get-Process Unity -ErrorAction SilentlyContinue |
    Select-Object Id, Path, WorkingSet64, PrivateMemorySize64, StartTime

Get-Item "$env:LOCALAPPDATA\Unity\Editor\Editor.log" |
    Select-Object FullName, Length, LastWriteTime
```

For automated reproduction, launch the Editor executable from the version used
by the project:

```text
F:\Unity Editors\<version>\Editor\Unity.exe
```

## Narrow the cause

Change one variable per reproduction:

- Disable one native plugin or renderer feature.
- Run without Burst, then with synchronous Burst compilation.
- Reduce the data size while retaining the failing regime.
- Switch graphics API only when the crash implicates rendering or a driver.
- Disable jobs or worker-thread parallelism only as a diagnostic control.
- Reproduce in a development player if the crash may be Editor-specific.

Predict how the crash should move before applying each control. A change that
merely makes the crash disappear once is not yet a confirmed cause.

## Memory-related failures

Track working set, private bytes, native allocations, and GPU allocations over
time. A runaway allocation can surface as an unrelated null dereference after
an allocation failure. Preserve the growth curve and the last successful
allocation or frame rather than diagnosing from the final stack alone.

## Linux note

On Linux, use a core dump or launch Unity as a debugger child when attach
permissions prevent `gdb -p`. Match the actual Unity executable rather than a
broad command-line pattern, because the debugger or search command can contain
the same project path. Symbolize addresses against the exact Editor and plugin
binaries used by the run.
