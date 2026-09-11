# Game-development verification

## Test at the observed boundary

Test the real player-visible or player-affecting path. For a visual issue, keep
the final-frame capture alongside internal diagnostics; internal values help
find the cause but do not prove the rendered result is correct.

## Build useful gates

- Drive the production code path instead of a reimplementation.
- Use a deterministic analytical, brute-force, or golden reference when one is
  available.
- Assert both required behaviour and at least one forbidden behaviour.
- Record witness data: inputs, sample counts, relevant configuration, and the
  measured result.
- Prove a regression test can fail by running it against a known-bad version or
  a controlled fault before relying on it.

## Unity test layers

Use EditMode tests for deterministic algorithms, serialization, chunk data,
and meshing. Use PlayMode tests for world scheduling, entity lifecycles, and
rendering/presentation interactions. Run a player build for platform-specific,
Burst, native-plugin, and final-pipeline coverage.

For voxel systems, include chunk borders, LOD transitions, empty/solid
boundaries, non-aligned world origins, streaming/teleport cases, and rapid edit
sequences. Measure performance separately from correctness and keep target
hardware and scene complexity explicit in any performance claim.

## Verification scope

Verify the smallest relevant scope first, then expand when a change crosses
assemblies, runtime boundaries, platforms, or data ownership domains. Use the
project's own compile, test, Editor, and runtime tools when available.

Do not claim that work is functioning, fixed, tested, or complete without an
observable result. Report the state precisely:

- implemented but untested;
- implemented and verified in the named scope;
- partially implemented;
- blocked by a stated condition;
- known issue requiring investigation.

A successful narrow check proves only that scope. Name meaningful omitted tiers,
such as a player build, dedicated server, target GPU, or multiplayer session,
when their absence changes whether the result can be relied upon.
