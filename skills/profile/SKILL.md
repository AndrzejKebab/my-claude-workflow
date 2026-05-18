---
name: profile
description: Build, run, and analyze Unity profiler data with perf-report-style call-stack attribution
---

Profile the game with call-stack-level GC allocation and CPU time attribution.

This global skill entry covers **methodology cross-references only**. The full per-project
implementation lives in each project's own `.claude/skills/profile/`. Read the project-local
SKILL.md for script inventory, argument grammar, benchmark sections, and pitfall catalogue.

- **woweyreey** (production project): `/mnt/archive4/UNITY/Projects/woweyreey/.claude/skills/profile/SKILL.md`
  Uses `unity-cli exec` (IPC into live editor) for build. `deploy-deck.sh` is pure bash.
- **zori_test_bed** (testbed): `/mnt/archive4/UNITY/Projects/zori_test_bed/.claude/skills/profile/SKILL.md`
  Uses batchmode exclusively — no live editor, no unity-cli. Build step is `build.sh <project>`.

## zori_test_bed build path (canonical, batchmode-only)

For any profile dispatch targeting `zority_6_0 | zority_6_3 | zority_6_4`, the build step is:

```bash
${CLAUDE_SKILL_DIR}/build-zority.sh zority_6_4
# or absolute path:
${CLAUDE_SKILL_DIR}/build-zority.sh /mnt/archive4/UNITY/Projects/zori_test_bed/zority_6_4
```

`build-zority.sh` is the **permanent canonical form** of the ad-hoc script that was written to
`/tmp/build-zority-6-4.sh` during the fog-detail-perf Step 9 dispatch (2026-05-18). It is
parameterised: accepts any `zority_6_*` shorthand or an absolute path.

**Do NOT write ad-hoc build scripts to `/tmp/` for this testbed.** The entry point exists here.

### Why batchmode, not unity-cli

The zori_test_bed CLAUDE.md explicitly removed `unity-cli` from its skillset:
> "The unity-cli (IPC-into-running-editor) tooling is gone from this project's skillset. It was
> unaffordable: it required keeping an editor process open and focused, and a single domain reload
> during agent work killed the assumption it relied on."

Every Unity invocation in the testbed goes through:
```bash
unity <project> -batchmode -quit [-executeMethod ...] -logFile -
```

### The -nographics prohibition

**Never pass `-nographics`** to any batchmode invocation in this testbed. From CLAUDE.md:
> "Never pass -nographics. Caps RenderTexture at 4096 and breaks anything that allocates GPU
> resources during import / EditMode fixtures (RenderTexture.Create failed). Applies to compile
> checks, tests, and -executeMethod runs alike."

The ad-hoc script `/tmp/build-zority-6-4.sh` correctly omitted `-nographics`. The testbed
skill's `build.sh` had this flag present as a latent bug — that's why the profile agent wrote
the ad-hoc script instead of using the existing file. `build-zority.sh` (this skill) is the
corrected, permanent version.

### FD limit workaround

`build-zority.sh` applies `ulimit -n 8192` before spawning Unity. This works around a Mono
`NamedPipeServerStream` FD-assertion in Unity 6000.4.x (corefx bugfix), which asserts when an
accepted-socket FD exceeds the cached `_SC_OPEN_MAX`. 8192 is sufficient for asset import and
IL post-process; it does not restrict the build output.

## Relationship to /build-run

`/build-run` (at `/mnt/archive4/UNITY/Projects/zori_test_bed/.claude/skills/build-run/SKILL.md`)
covers **release** builds via `Zori.TestBed.Editor.BuildScript.BuildLinuxRelease`.
`build-zority.sh` here covers **development** builds (profiler-enabled) via
`Zori.TestBed.Editor.ProfileBuild.BuildDevelopmentLinux`. Use `/build-run` when you want a
production binary; use `build-zority.sh` (via `/profile`) when you need a profiler capture.

Both share the same `-nographics` prohibition and `ulimit -n 8192` workaround.
