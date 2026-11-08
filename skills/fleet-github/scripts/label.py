#!/usr/bin/env python3
"""Move an item's status label and post the one-line reason, after the gate for that move.

    label.py 261 --to waits-for-final-review --signer Reviewer --reason "review clean at ecf73eac"
    label.py 300 --to blocked --signer Worker-2 --reason "..." --self-check-file .scratch/check.md
    label.py 310 --to in-progress --signer Worker-1 --reason "plan approved" --pr 312

Gates: `blocked` needs the four-line self-check; the first `in-progress` needs a work plan and Reviewer's
plan approval on the draft PR; `waits-for-review` on a PR needs one evidence line per acceptance criterion,
and on a bug also Cause, Reproduction and the approach approval. Programs started: gh.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # found when run isolated or through a shim
import fleet_rules as rules  # noqa: E402

STATUS = ('ready', 'in-progress', 'waits-for-review', 'in-review', 'waits-for-final-review', 'waits-for-eye-review',
          'ready-to-merge', 'blocked', 'needs-owner', 'needs-human')


def gh(*args: str, stdin: str | None = None, check: bool = True) -> str:
    result = subprocess.run(['gh', *args], input=stdin, capture_output=True, text=True, encoding='utf-8',
                            errors='replace')
    if check and result.returncode != 0:
        sys.exit(result.stderr.strip() or f'gh {" ".join(args)} failed')
    return result.stdout.strip() if result.returncode == 0 else ''


def pr_facts(number: int, repo: list[str]) -> dict | None:
    raw = gh('pr', 'view', str(number), '--json', 'body,comments,closingIssuesReferences', *repo, check=False)
    return json.loads(raw) if raw else None


def gate(args, current: list[str], repo: list[str]) -> list[str]:
    if args.to == 'blocked':
        if not args.self_check_file:
            return ['`blocked` needs --self-check-file with the four-line self-check:\n' + rules.SELF_CHECK_FORMAT]
        return rules.self_check_problems(Path(args.self_check_file).read_text(encoding='utf-8'))
    if args.to == 'in-progress' and set(current) <= {'ready'}:
        pr = pr_facts(args.pr or args.number, repo)
        if pr is None:
            return ['starting work needs the draft PR first: open it with a `## Work plan` body, get "Plan '
                    'approved" from Reviewer, then pass --pr <draft PR number> when labelling the issue']
        return rules.start_problems(pr['body'], [c['body'] for c in pr['comments']])
    if args.to == 'waits-for-review':
        pr = pr_facts(args.number, repo)
        if pr is None:
            return []  # the issue side follows its PR, which carries the gate
        linked = pr.get('closingIssuesReferences') or []
        issue = json.loads(gh('issue', 'view', str(linked[0]['number']), '--json', 'body,labels', *repo)) \
            if linked else {'body': '', 'labels': []}
        if not linked and not re.search(r'#\d+', pr['body']):
            return ['the PR body must close its issue (`closes #N`) so its acceptance criteria can be checked']
        is_bug = any(label['name'] == 'bug' for label in issue['labels'])
        return rules.ready_problems(pr['body'], issue['body'], is_bug, [c['body'] for c in pr['comments']])
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('number', type=int)
    parser.add_argument('--to', required=True, choices=STATUS)
    parser.add_argument('--reason', required=True, help='one line: why the label moves')
    parser.add_argument('--signer', required=True, choices=rules.SIGNERS)
    parser.add_argument('--self-check-file', help='required for --to blocked')
    parser.add_argument('--pr', type=int, help='the draft PR, when starting work on an issue')
    parser.add_argument('--repo')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    repo = ['--repo', args.repo] if args.repo else []

    listed = gh('issue', 'view', str(args.number), '--json', 'labels', '-q', '.labels[].name', *repo)
    current = [name for name in listed.split() if name in STATUS and name != args.to]
    problems = gate(args, current, repo)
    if problems:
        print('refused:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1

    before = ', '.join(current) if current else '(none)'
    edit = ['issue', 'edit', str(args.number), '--add-label', args.to]
    for name in current:
        edit += ['--remove-label', name]
    comment = f'# {args.signer}\n\nLabel: {before} → {args.to} — {args.reason}\n'
    if args.to == 'blocked':
        comment += '\n' + Path(args.self_check_file).read_text(encoding='utf-8').strip() + '\n'
    print(f'{before} -> {args.to}')
    if args.dry_run:
        print('gh', ' '.join(edit), *repo)
        print(comment)
        return 0
    gh(*edit, *repo)
    gh('issue', 'comment', str(args.number), '-F', '-', *repo, stdin=comment)
    now = gh('issue', 'view', str(args.number), '--json', 'labels', '-q', '[.labels[].name]', *repo)
    print('labels now:', now)
    return 0 if args.to in now else 1


if __name__ == '__main__':
    sys.exit(main())
