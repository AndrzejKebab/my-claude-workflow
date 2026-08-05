---
name: research-background-jobs-need-setsid
description: "/research GPU scripts take ~90s to appear in ps; a zero-byte log is not evidence they died, but a sub-agent that returns does kill its own background job"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d7305028-ac23-4b11-b76e-fc76b0ca7118
  modified: 2026-07-21T16:39:21.678Z
---

Two distinct failure modes look identical when a `/research` pass seems stalled — a **zero-byte log
and no process in `ps`**. They need opposite responses, so separate them before acting.

**Not a failure: the CUDA bootstrap window.** `transcribe_to_srt.py` preloads the CUDA-12 cublas
stack and builds the faster-whisper model before it writes anything or shows up under its own name
in `ps`. That is roughly **90 seconds of looking completely dead**. A Bash `run_in_background` job
launched from the orchestrator *does* survive — I once concluded it had been killed, relaunched it
detached, and ended up with two concurrent whisper runs on the same file competing for VRAM
(~4.5 GiB each) and racing on the same output SRT. Check `nvidia-smi --query-compute-apps` before
concluding anything: it shows the python PID while `ps | grep python` still shows nothing.

**A real failure: a sub-agent that returns.** A `research-extractor` sub-agent which launches a long
job in *its* background and then returns takes the job down with it — the download finished, the
job's `.output` stayed 0 bytes, and nothing ever progressed. Either run the long script from the
orchestrator, or require the sub-agent to block in the foreground until the artifact exists.

**How to apply.** Diagnose in this order — `nvidia-smi --query-compute-apps=pid,used_memory` first
(authoritative for GPU work), then `cat /proc/<pid>/cmdline`, then the job's `.output` size, then
temp-dir mtimes. Beware `pgrep -f`/`ps | grep` self-matching your own command line — it manufactures
phantom "processes" that are really your shell. Wait out at least two minutes before calling a GPU
job dead. If you do relaunch, kill the original first.

`setsid nohup … & disown` is the belt-and-braces launch when you want a job that provably cannot be
reaped, but it is not required for ordinary orchestrator background jobs. Pair any launch with a
`Monitor` `until`-loop over the expected artifact that also prints the log tail when no process
remains, so a dead job announces itself instead of hiding as a slow one.

See [[deck-benchmark-launcher-and-staleness]] for the sibling habit: check the artifact, not the
launcher.
