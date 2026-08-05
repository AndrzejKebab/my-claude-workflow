# Durable memory

Claude Code writes per-project memories to `~/.claude/projects/<slug>/memory/`. **Nothing tracks
`~/.claude`** — it is not a git repo, and before this the installer only symlinked `skills`, `agents`
and the `CLAUDE.md` @imports into it. Everything else there was one machine rebuild from gone.

At migration time that was **33 project directories and 402 files**, some of them years of accumulated
project knowledge — `woweyreey` alone held 163.

The fix is the shape the installer already used for `skills` and `agents`: the real files live in this
repo, a symlink points at them from `~/.claude`.

    ~/.claude/projects/<slug>/memory  ->  <repo>/memory/<slug>/

`bin/cc-memory-link` performs the migration and `install.sh` runs it, so a fresh machine gets every
memory back with the same command that installs everything else.

    cc-memory-link -n              # dry run — say what would happen, touch nothing
    cc-memory-link                 # do it
    cc-memory-link -n <substring>  # limit to slugs matching a substring

## How it avoids losing anything

The order is **copy → verify → replace**, never move:

1. `cp -an` into the store (`-n` so an existing file is never clobbered).
2. `cmp` every source file against its copy. Any mismatch aborts *that slug* and leaves the originals
   untouched.
3. Only then remove the original directory and put a symlink in its place.

An interrupted run therefore leaves originals intact and can simply be re-run. A file present on both
sides with **differing content** is never overwritten — the slug is reported as `CONFLICT`, skipped,
and left unlinked to resolve by hand. Re-running when everything is already linked is a no-op.

## Privacy

The store holds memories about **every** project, including client work. This repo is private, and it
must stay that way — check with `gh repo view <owner>/my-claude-workflow --json isPrivate` before ever
changing its visibility, and treat `memory/` as the reason not to.

If a project's memories should not live here at all, the honest options are to keep that slug
unlinked (delete the symlink and restore a real directory from the store), or to add the slug to
`.gitignore` — not to quietly hope nobody looks.

## The general lesson

`~/.claude` is a **cache with some config in it**, not storage. Anything written there that would hurt
to lose needs a symlink into a tracked repo and a line in `install.sh`. That already covers `skills`,
`agents`, the `CLAUDE.md` @imports, hooks (see [no-op-spin.md](no-op-spin.md)) and now `memory`.

`settings.json` is the deliberate exception: Claude Code writes to it during a session, so it is
merged into rather than symlinked — a link would make this repo churn on every run.
