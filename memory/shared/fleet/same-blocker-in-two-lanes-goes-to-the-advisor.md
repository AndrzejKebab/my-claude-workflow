# The same blocker in two lanes goes to the Advisor at once

Symptom: a second Worker reports a failure you have already seen in another lane (a toolchain upgrade, a cache, a process nobody can kill)
Domain: fleet
Verified: 2026-11-11 at 2c3c2faa

## What to do

One cause hitting two lanes is a fleet blocker, not lane work. Manager: DM the Advisor in the same turn with each lane's exact output and your analysis; the Advisor decides whether the owner is needed. Worker: a cause outside your diff (toolchain, upgrade, a process you cannot kill) goes to Manager by DM in the turn you find it, with the self-check. The final reply of a watchdog wake reaches nobody.

## Evidence

2026-11-10 after the Unity a16 upgrade: Worker-3's compile failed on duplicate PolySharp attributes, Worker-5's on stale Burst wrappers in Library/Bee, and Worker-5 could not kill its own a16 batchmode processes 'exactly as earlier tonight'. Manager handled each lane alone and compiled a worktree itself; the Advisor and the owner heard nothing.
