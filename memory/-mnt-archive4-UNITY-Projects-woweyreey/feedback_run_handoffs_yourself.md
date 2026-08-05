---
name: Run handoff documents yourself, don't delegate
description: When user says "execute @docs/.../handoff.md", run the work directly — don't dispatch a sub-agent
type: feedback
originSessionId: 25c59982-1935-4daf-b597-f97cfef65ffd
---
When the user invokes `execute @docs/<path>/<handoff>.md` (or similar "run this handoff" phrasings), execute it yourself in the main session. Do NOT spawn a sub-agent for it.

**Why:** The user explicitly corrected this on 2026-05-01 after I dispatched a sub-agent for `04-handoff-ring-positioning.md`. The handoff itself said "single sequential agent" but the user wanted ME to be that agent — not a sub-agent. The "delegating-operator" memory applies to broad/exploratory work; explicit handoff documents the user hands off to the current session are meant for the current session to run.

**How to apply:** When the user pastes/references a handoff file and says "execute it" / "run it" / "do this", read the handoff and execute it step-by-step in this session, using direct tool calls (Read/Edit/Write/Bash). Reserve sub-agent dispatch for: parallel research, broad codebase searches, explicitly-requested delegation, or work that the user frames as "have an agent do X".
