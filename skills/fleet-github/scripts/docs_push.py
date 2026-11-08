#!/usr/bin/env python3
"""Push docs-only commits on main: markdown on allowed paths, validated, privacy-checked, fast-forward only.

    docs_push.py --repo-dir <clone> --allow 'Docs/**' --allow '.project-state/**' --allow '.memory/**' \
        [--validate "python tools/git/validate_docs.py"] [--dry-run]

Checks every commit on HEAD that origin/main does not have. Raw `git push` is denied to the bots that use
this, so it is their only route to main. Programs started: git, and the --validate command.
"""
from __future__ import annotations

import argparse
import fnmatch
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # found when run isolated
import fleet_rules as rules  # noqa: E402


def push_problems(changed: list[str], allow: list[str], added_lines: list[str]) -> list[str]:
    if not changed:
        return ['nothing to push: no commit on HEAD that origin/main lacks']
    problems = [f'not markdown: {f}' for f in changed if not f.endswith('.md')]
    problems += [f'outside the allowed paths ({", ".join(allow)}): {f}' for f in changed
                 if not any(fnmatch.fnmatch(f, pattern) for pattern in allow)]
    problems += [f'local path in an added line: {line.strip()[:120]}' for line in added_lines
                 if rules.PRIVACY.search(line) and 'privacy-ok:' not in line]
    return problems


def git(repo: str, *args: str) -> str:
    result = subprocess.run(['git', '-C', repo, *args], capture_output=True, text=True, encoding='utf-8',
                            errors='replace')
    if result.returncode != 0:
        sys.exit(f'git {" ".join(args)}: {result.stderr.strip()}')
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('--repo-dir', required=True)
    parser.add_argument('--allow', action='append', required=True, help='glob of paths that may change')
    parser.add_argument('--validate', help='command that must exit 0 before the push')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    repo = args.repo_dir

    if git(repo, 'branch', '--show-current').strip() != 'main':
        print('refused: the clone is not on main (someone else may be using it); wait and retry', file=sys.stderr)
        return 1
    git(repo, 'fetch', 'origin', 'main')
    if subprocess.run(['git', '-C', repo, 'merge-base', '--is-ancestor', 'origin/main', 'HEAD']).returncode != 0:
        print('refused: origin/main moved; run `git pull --ff-only` and retry', file=sys.stderr)
        return 1
    changed = [f for f in git(repo, 'diff', '--name-only', 'origin/main..HEAD').splitlines() if f]
    added = [l[1:] for l in git(repo, 'diff', 'origin/main..HEAD').splitlines()
             if l.startswith('+') and not l.startswith('+++')]
    problems = push_problems(changed, args.allow, added)
    if args.validate and not problems:
        if subprocess.run(shlex.split(args.validate), cwd=repo).returncode != 0:
            problems.append(f'validator failed: {args.validate}')
    if problems:
        print('refused:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1
    print(f'{len(changed)} file(s) ok: {", ".join(changed)}')
    if args.dry_run:
        return 0
    result = subprocess.run(['git', '-C', repo, 'push', 'origin', 'HEAD:main'], capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    print((result.stdout + result.stderr).strip())
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
