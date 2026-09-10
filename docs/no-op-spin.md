# Avoiding no-op polling loops

An agent waiting for a Unity run, build, test suite, delegated task, or remote
job should wait on the subject itself. Repeated `echo`, `true`, empty polling,
or rapid status checks add cost and noise without making completion happen
sooner.

## Rules

- Use the client's task-wait primitive when one exists.
- For a running terminal process, wait on that process or session rather than
  launching new commands.
- For a background service, poll at a bounded interval and stop when a concrete
  state changes.
- Do not use foreground sleeps merely to keep an agent active.
- Report unchanged state only when the user asked for periodic status.
- Time out with a clear diagnostic rather than polling forever.

## Claude Code hook

`bin/cc-nospin` is a Claude Code `PreToolUse` hook. It rejects commands that are
entirely no-ops and detects excessive repetition. It is a provider-specific
backstop; the general waiting rules above apply equally to Codex.

The hook must fail open on malformed input or unavailable dependencies. A broken
pre-tool hook must not block every shell command.

## Unity process checks

On Windows, prefer checking the actual Unity process plus the project lock and
log state. A broad command-line substring search can match the checking command
itself or an unrelated Editor.

Useful evidence includes:

- The process executable is `Unity.exe`.
- The expected project has a `Temp\UnityLockfile` while open.
- The batch-mode log continues to advance.
- The process exit code or terminal session reports completion.

`bin/unity-ps` is a Unix helper retained for compatible environments. Do not use
it as the Windows implementation; use PowerShell process inspection or the Unity
CLI integration available in the current environment.

## Prompt guidance

When delegating long-running work, say:

> Wait on the running task or process. Do not issue no-op commands to remain
> active. Poll only when no event-based wait exists, use a bounded interval,
> and report only completion, failure, or required user action.
