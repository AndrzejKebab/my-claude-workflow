# Cold-compiling a worktree after an editor upgrade

When the main clone compiles and a worktree does not, the difference is environment, not code: every claim below
was measured by compiling the same head in a worktree, with the counts quoted beside the log mtime.

## The conditions are a set, not one cause

Compiling green needs **all** of these. Finding one and stopping names the wrong cause — and a lane that never had
the first condition still goes red.

1. **No stale gitignored package folder.** `Assets/Packages/<Pkg>.<version>/` (a resolved NuGet/analyzer package
   copied in by an older setup) survives merges because `/Assets/*` is gitignored. A source generator left there
   keeps emitting polyfill types the new editor or packages now define themselves, and the build fails with
   `CS0101`/`CS0579` duplicate definitions inside a *generated* file plus `CS0104` ambiguous attributes.
   Check with `git check-ignore -v Assets/Packages/<dir>`; if it hits an ignore rule, it is a leftover and the
   main clone is the reference for whether it should exist.
2. **Submodules at `main`'s commits.** `git submodule update --init --recursive` in the worktree. A submodule
   pointer that looks "dirty" but was never synced carries old source that reintroduces the same polyfills.
3. **No previous editor's artefacts.** `clear_caches.py` (or delete `Library/Bee`, `Library/ScriptAssemblies`,
   `Library/BuildPlayerData`) after an editor upgrade. Never delete `Library` wholesale unless the owner says so.
4. **Package-cache patch applied to the resolved copy.** `python tools/patch_mrunbelievable_packages.py --root
   <worktree>/Library/PackageCache`. The `--root` is the **PackageCache** directory, not the project root: give it
   the project root and it prints `no com.mrunbelievable.* packages` and patches nothing, which reads as "nothing
   to patch" rather than "wrong path". `patched 0 sites` from the correct root is different and can be legitimate —
   an editor whose built-in packages supply these assemblies resolves no `com.mrunbelievable.*` copy at all, and
   that lane still compiles `error CS` 0. Quote which of the two zeroes you got, with the root you passed.

## Order

1. remove the gitignored leftovers;
2. `git submodule update --init --recursive`;
3. clear `Library/Bee` (+ `ScriptAssemblies`, `BuildPlayerData`);
4. **import once** — a compile attempt does it, and it is what repopulates `Library/PackageCache` after a clear;
5. run the package patch against `Library/PackageCache`;
6. compile, and quote the head, the editor version, `error CS` count and the log mtime together.

Step 4 before step 5 matters: patching a cleared `Library` finds no packages and silently does nothing.

## Copying the main clone's cache does not make a worktree warm

Copying `Library`, `Library/Bee`, `ScriptAssemblies`, `ArtifactDB` or the whole `PackageCache` from the main clone
into a worktree does **not** reproduce its green build: Bee's cache keys include the project path, so every package
assembly is a `CacheMiss` and gets rebuilt in the worktree anyway. If the rebuild then fails, the failure is in the
build, not in the copy — say so instead of spending another copy.

## A held `Temp/UnityLockfile`

A batchmode Editor that exits in a second with `exit code 1` and a ~1 KB log is usually refusing a project whose
`Temp/UnityLockfile` is held by a zombie Editor from an earlier run. Kill only Editors whose `-projectPath` is that
worktree (`unity_procs.py kill --worktree … --batch-only --yes`, then again without `--batch-only` if one survives),
then delete the lock and start the compile again. Never delete a lock whose holder is alive.
