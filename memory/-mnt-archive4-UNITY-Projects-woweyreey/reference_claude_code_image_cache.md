---
name: Claude Code image-cache path convention
description: Pasted images in Claude Code are auto-saved to ~/.claude/image-cache/<session-uuid>/<N>.png where N matches the "image N" index the orchestrator sees. Use this to resolve conversation-attached images to absolute paths sub-agents can Read.
type: reference
originSessionId: 42962e51-34e2-4a27-9eb4-f52e6dddfdb7
---
When the user pastes an image into Claude Code, the harness saves it to:

```
~/.claude/image-cache/<session-uuid>/<N>.png
```

- `<session-uuid>` is the active session's UUID. Find the current one with `ls -t ~/.claude/image-cache/ | head -1` (most recently modified directory).
- `<N>` is sequential per session and matches the "image N" identifier the orchestrator sees in its own view (e.g. "image 32" → `32.png`).
- Verify existence with `ls` before quoting the path — sessions can be wiped, and the index can wrap.

**How to apply:**
- In `/delegate` mode, use this to resolve conversation-attached images to absolute filesystem paths that sub-agents can Read. Sub-agents can render PNG/JPG visually via the Read tool.
- Also useful when handing off to fresh agents (handoff skill) — inline the absolute path so the next session can re-view the image.
- Don't write "image 32" or any conversation-relative reference in shared files; resolve to the absolute path first.
