## Never edit files with bash

**Edit and Write are the only ways to change a file.** Not `sed -i`, not `python3 - <<PY`, not
`node -e`, not `printf > file`, not a heredoc writing source, not `>>` appending to a tracked file.

Post-edit hooks fire on `Edit|Write|MultiEdit|NotebookEdit` and **cannot** fire on Bash — a shell
command does not say which files it touched, so nothing formats, lints or verifies what it wrote.
The write succeeds, the hook stays silent, and the file is the one thing in the tree nobody checked.

Measured 2026-07-23, identical content written both ways into a repo with a biome post-edit hook:
the Write-tool file came back formatted *and* linted (an unused binding renamed); the `printf` file
was untouched. In that same session a dead import survived every gate — `tsc` does not flag one and
the formatter does not lint — and it survived precisely in the files patched through the shell,
because those were the only files the hook never saw. Lint debt accumulates exactly where bash was
used and nowhere else, which is why it reads as a mystery rather than as a cause.

The pull toward bash is real and it is a trap: a tricky escape, nested backticks inside a template
literal, a repetitive rename across several files. Do it with Edit anyway — Read the file first
when the string is awkward. Scripted editing is for **generated artefacts and throwaway scratch
files**, never for source.

If a shell write is genuinely unavoidable, it is not finished until the repo's own formatter and
linter have been run over exactly the files it touched, in the same turn, and the result reported.
"The hook did not run" is not an excuse available afterwards; it is a thing to have prevented.