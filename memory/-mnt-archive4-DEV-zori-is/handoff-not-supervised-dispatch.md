---
name: ""
metadata: 
  node_type: memory
  originSessionId: 86b27887-66d1-4fcd-9884-31d082163037
---

When the user says "kick off a new session", "handoff", or "do it in a new session", they want a FULL ownership handoff — a fresh agent that owns the work and that the user interacts with directly — NOT a supervised orchestration `dispatch --inject` where I stay coordinator and monitor `worker_done`/heartbeats.

**Why:** `dispatch --inject` injects a coordinator preamble that makes the worker send heartbeat/worker_done/post-completion polling back to my terminal, creating lifecycle obligations and a babysitting loop the user did not ask for. The user found this wrong and asked me to "abandon your role as orchestrator."

**How to apply:** For a handoff, launch the worker with a plain prompt and no lifecycle preamble — `orca terminal create --worktree <selector> --command "claude --dangerously-skip-permissions"` then `orca terminal send --terminal <h> --text "<brief>" --enter`, or `orca worktree create --prompt "<brief>"`. Do not `dispatch --inject`, do not `check --wait` on it, do not supervise. Reserve supervised orchestration (task DAG + `dispatch --inert` + `check --wait`) for when the user explicitly wants a coordinated multi-worker run. Relates to [[blackbox-test-harness]].
