---
name: unity-recompile is the only sanctioned recompile path
description: Always invoke `unity-recompile`; never decompose into raw `unity-cli editor refresh ... && sleep ... && unity-cli console ...`. If it backgrounds, wait for the auto-notification — never poll.
type: feedback
originSessionId: 7aff3624-728d-45ef-9423-5b730f7c247b
---
After ANY C#/shader/asmdef edit, recompile via the canonical wrapper `unity-recompile` (lives in `/home/midori/_dev/my-claude-workflow/bin/`, on PATH — invoke by bare name). It does, in order: `hyprctl dispatch focuswindow "class:Unity"` → `unity-cli editor refresh --compile --force --timeout 3600000` → `sleep 30` → `unity-cli console --filter error --lines 5`.

**Never decompose** into raw `unity-cli editor refresh ...`, never skip the focus step, never skip the sleep, never substitute a different post-check. If you need an additional check, run `unity-recompile` first and append your check after.

**Why:**
- Without the Hyprland focus call, the asset-refresh IPC signal stalls and `unity-cli` returns immediately (or backgrounds) without a compile actually happening — every "recompile didn't take" debugging session traces back to this.
- The 30 s sleep covers the post-recompile editor freeze (domain reload + assembly reload + deferred init). Anything shorter races the editor and the next `unity-cli` call sees stale state.
- Centralising the sequence prevents drift: agents mutating any one step (focus / timeout / sleep / post-check) silently break the others.

**How to apply:**
- ANY recompile trigger goes through `unity-recompile` — in scripts, in skill workflows, in handoff briefs you write for sub-agents, in delegated work.
- Long compiles can push the Bash invocation into background mode. When that happens, **wait for the harness's completion notification and resume work then**. Do NOT spawn a monitor, do NOT run a `while sleep ; check` loop, do NOT dispatch a polling sub-agent — the harness already auto-resumes on background completion.
- Project rule lives in `/mnt/archive4/UNITY/Projects/woweyreey/CLAUDE.md` § "Recompile Protocol (unity-recompile)" — that section is the binding contract; this memory enforces the same rule across sessions.
