---
name: unity-native-crash-forensics
description: "How to actually locate a Unity editor SIGSEGV on this machine — the log's stacktrace is the signal handler, ptrace is descendant-only, perf yields nothing"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 473fac03-6fd5-444d-a174-fe2bfbfd7695
  modified: 2026-07-21T17:33:59.754Z
---

Unity's `Native stacktrace:` block in a crash log is **mono's own signal-handler chain**
(`mono_sigsegv_signal_handler` → the crash-dump printer), not the fault site. Reading it as "the
crash is in the Mono GC" is wrong every time. Likewise `Thread … may have been prematurely
finalized` and the `mono_thread_info_current` assert are the telemetry dumper failing, and
`Setting up scripting invocation from unattached thread` is Unity's `SignalHandler` attempting
`DoQuitEditorWithExitCode` off the main thread — a *second* fault. That double fault is why a
crashed `-runTests` run writes no results XML.

A small `addr:` value (`addr:0x39`) is a null pointer plus a field offset: an allocation that
returned NULL. Check `VmRSS`/`VmSize` in `/proc/<pid>/status` before theorising about corruption —
a runaway allocation looks exactly like a GC bug from the log alone.

Getting a real backtrace here:

- `kernel.yama.ptrace_scope = 1` and there is no passwordless sudo, so `gdb -p <pid>` fails with
  "Operation not permitted". **gdb must be the parent**: `gdb -batch --args <editor> -projectPath …`,
  then `kill -INT <gdb-pid>` from a watcher when RSS crosses a threshold, with `-ex 'bt 60'` after
  `-ex run`. Running under gdb also disables ASLR, which lets mono unwind further and print frames
  the ASLR'd run could not.
- `perf record -p <pid>` returns "no samples" regardless of event — don't spend time on it.
- Find the editor process by `/proc/<pid>/exe`, never by a cmdline pattern: gdb's own argv carries
  the whole Unity command line and a `pgrep -f` match silently returns gdb (7 MB RSS) instead.
- Symbolise offsets against the editor binary with `gdb -batch -ex 'info symbol 0x<offset>'`;
  `readelf`/`nm` only see ~840 exported FUNCs and will confidently name the wrong symbol.
  Base = `<logged addr> - <known offset>`; `burst_signal_handler` is a good anchor.
- `coredumpctl list` usually has the core; `coredumpctl dump <pid> --output=…` then gdb it.

Related: [[single-editor-test-runs]], [[durable-e2e-not-editor-qa]].
