# Locating a Unity editor SIGSEGV

Unity's `Native stacktrace:` block in a crash log is **mono's own signal-handler chain**
(`mono_sigsegv_signal_handler` → the crash-dump printer), not the fault site. Reading it as "the
crash is in the Mono GC" is wrong every time. `Thread … may have been prematurely finalized` and the
`mono_thread_info_current` assert are the telemetry dumper failing, and `Setting up scripting
invocation from unattached thread` is Unity's `SignalHandler` attempting `DoQuitEditorWithExitCode`
off the main thread — a *second* fault. That double fault is why a crashed `-runTests` run writes no
results XML.

A small `addr:` value (`addr:0x39`) is a null pointer plus a field offset — an allocation that
returned NULL. Check `VmRSS`/`VmSize` in `/proc/<pid>/status` before theorising about corruption; a
runaway allocation looks exactly like a GC bug from the log alone.

Getting a real backtrace on this machine:

- `kernel.yama.ptrace_scope = 1` and there is no passwordless sudo, so `gdb -p <pid>` fails with
  "Operation not permitted". **gdb must be the parent**: `gdb -batch --args <editor> -projectPath …`,
  then `kill -INT <gdb-pid>` from a watcher when RSS crosses a threshold, with `-ex 'bt 60'` after
  `-ex run`. Running under gdb also disables ASLR, which lets mono unwind further.
- `perf record -p <pid>` returns "no samples" regardless of event — do not spend time on it.
- Find the editor by `/proc/<pid>/exe`, never a cmdline pattern: gdb's own argv carries the whole
  Unity command line, so a `pgrep -f` match silently returns gdb (7 MB RSS) instead.
- Symbolise offsets with `gdb -batch -ex 'info symbol 0x<offset>'`; `readelf`/`nm` see only ~840
  exported FUNCs and will confidently name the wrong symbol. Base = `<logged addr> - <known offset>`;
  `burst_signal_handler` is a good anchor.
- `coredumpctl list` usually has the core; `coredumpctl dump <pid> --output=…` then gdb it.
