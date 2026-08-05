---
name: Never dispatch two unity-cli test commands in parallel within an agent
description: Sub-agents must serialize all unity-cli test invocations within their own work — never two simultaneous test runs.
type: feedback
originSessionId: 0c8013cd-69a6-4fef-b80c-ef328fedf212
---
When briefing a sub-agent, the brief must explicitly require: **all `unity-cli test` invocations the agent runs must be sequential, with the standard 5 s sleep between them, never concurrent.**

**Why:** Even within a single agent, running two test calls in parallel (e.g. EditMode + PlayMode in the same shell pipeline) collides on the Unity editor instance — one or both hang or fail with bridge-crash artefacts. This compounds the existing project rule (`feedback_unity_cli_tests.md`: "no concurrent unity-cli tests"), which already applies project-wide; the agent brief must restate it because agents otherwise default to "run tests in parallel for speed".

**How to apply:** In every agent prompt that involves running tests, include the explicit sequence:

```
unity-cli test --mode PlayMode --filter "...A"
sleep 5
unity-cli test --mode PlayMode --filter "...B"
sleep 5
unity-cli test --mode EditMode --filter "..."
```

Never give the agent a Bash block with `&` or piped concurrent test calls. Never tell the agent "run all the basemap test suites" without specifying serialization.
