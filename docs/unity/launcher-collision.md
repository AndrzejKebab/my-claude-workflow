# `unity` collides with Unity's own CLI

Unity Technologies now ship a `unity-cli` and their installer drops it at **`~/.local/bin/unity`** —
a 134 MB binary (`1.0.0-beta.3` as of 2026-07-31). This repo's launcher is also called `unity`: a
~110-line bash wrapper that reads `ProjectSettings/ProjectVersion.txt`, dispatches GUI launches
through `unity-launch` with an already-open guard, and `exec`s batchmode synchronously so the caller
gets Unity's exit code.

They are completely different tools that answer to the same name. **Whichever `bin` dir comes first on
PATH wins**, and the loser leaves no trace — same invocation, no error, different semantics. On the
machine this was found, `_dev/my-claude-workflow/bin` sat at PATH position 3 and `~/.local/bin` at 10,
so the wrapper won *by accident*. A machine that orders them the other way sends every Unity gate
through the wrong binary silently.

## What was done about it

**`unity-editor` is the canonical name.** `bin/unity` is kept as a symlink to it, so existing call
sites and the SKILL.md prose keep working wherever PATH order still favours this repo.

**`install.sh` checks and says so.** It resolves `unity`, compares it against `bin/unity-editor`, and
prints either `OK` or a warning naming the wrong binary and both fixes.

## The immune option

The zori_skills unity plugin reads **`ZORI_UNITY_BIN`** (`plugins/unity/lib/unity.sh`), defaulting to
bare `unity` on PATH. Binding it removes the PATH dependency completely:

    export ZORI_UNITY_BIN=unity-editor

That is one env var against one real call site — `lib/unity.sh` is the *only* place that actually
invokes the launcher; every other mention across the plugin is documentation. Set it per repo in
`.agents/project.sh`, or globally in the shell rc.

## Why not just rename and be done

Because `unity` is what the skills' documentation, the muscle memory and any shell history all say.
Keeping the short name working while making an unambiguous one available costs a symlink; forcing the
rename costs a sweep through prose in five SKILL.md files for no functional gain. The name that
matters is the one a *script* resolves, and scripts should be using `ZORI_UNITY_BIN`.
