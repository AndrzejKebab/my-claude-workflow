#!/usr/bin/env python3
"""Move an item's status label and post the one-line reason, after the gate for that move.

    label.py 261 --to waits-for-final-review --signer Reviewer --reason "review clean at ecf73eac"
    label.py 300 --to blocked --signer Worker-2 --reason "..." --self-check-file .scratch/check.md
    label.py 310 --to in-progress --signer Worker-1 --reason "plan approved" --pr 312

    label.py 433 --to blocked --add on-hold --signer Worker-4 --reason "Blocked by #164"

Gates: bare `blocked` needs the four-line self-check; `blocked --add on-hold` needs an open `Blocked by #N` in the
reason, and `blocked --add question` the question in the reason; the first `in-progress` needs a work plan and Reviewer's
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
    raw = gh('pr', 'view', str(number), '--json', 'body,comments,closingIssuesReferences,createdAt', *repo,
             check=False)
    return json.loads(raw) if raw else None


SIDE = ('question', 'on-hold')
BLOCKED_BY = re.compile(r'blocked by\s+((?:#\d{1,5}(?:\s*(?:,|and|&)\s*)?)+)', re.I)


def needs_self_check(args) -> bool:
    """Bare `blocked` is a failure and owes the self-check; `+ on-hold` (another item) and `+ question` are waits."""
    return args.to == 'blocked' and not set(args.add) & set(SIDE)


def side_problems(args, state) -> list[str]:
    wrong = [name for name in args.add + args.remove if name not in SIDE]
    if wrong:
        return [f'--add/--remove take only the side labels question and on-hold, not {", ".join(wrong)}; '
                'a status moves with --to']
    if 'on-hold' in args.add:
        if args.to != 'blocked':
            return ['on-hold goes with --to blocked: blocked + on-hold means waiting on another item']
        numbers = [int(n) for match in BLOCKED_BY.finditer(args.reason) for n in re.findall(r'#(\d+)', match.group(1))]
        if not numbers:
            return ['blocked + on-hold needs the item it waits on in --reason: "Blocked by #N"']
        if not any(state(n) == 'OPEN' for n in numbers):
            return [f'{", ".join(f"#{n}" for n in numbers)} is already closed: nothing holds this item']
    return []


def side_edits(args, labels: list[str]) -> list[str]:
    edit = []
    for name in args.add:
        edit += ['--add-label', name]
    removed = set(args.remove) | ({'on-hold'} & set(labels) if args.to != 'blocked' else set())
    for name in sorted(removed):
        edit += ['--remove-label', name]
    return edit


def issue_state(number: int, repo: list[str]) -> str:
    return gh('issue', 'view', str(number), '--json', 'state', '-q', '.state', *repo, check=False)


def gate(args, current: list[str], repo: list[str]) -> list[str]:
    if problems := side_problems(args, lambda n: issue_state(n, repo)):
        return problems
    if args.to == 'blocked':
        if not needs_self_check(args):
            return []
        if not args.self_check_file:
            return ['`blocked` needs --self-check-file with the four-line self-check:\n' + rules.SELF_CHECK_FORMAT]
        return rules.self_check_problems(Path(args.self_check_file).read_text(encoding='utf-8'))
    if args.to == 'in-progress' and set(current) <= {'ready'}:
        pr = pr_facts(args.pr or args.number, repo)
        if pr is None:
            return ['starting work needs the draft PR first: open it with a `## Work plan` body, get "Plan '
                    'approved" from Reviewer, then pass --pr <draft PR number> when labelling the issue']
        return rules.start_problems(pr['body'], [c['body'] for c in pr['comments']], pr.get('createdAt'))
    if args.to == 'waits-for-review':
        pr = pr_facts(args.number, repo)
        if pr is None:  # an issue: gate on the PR that closes it
            raw = gh('issue', 'view', str(args.number), '--json', 'closedByPullRequestsReferences', *repo)
            linked = [p['number'] for p in json.loads(raw).get('closedByPullRequestsReferences') or []]
            if problems := rules.linked_pr_problems(linked):
                return problems
            pr = pr_facts(linked[-1], repo)
        linked = pr.get('closingIssuesReferences') or []
        issue = json.loads(gh('issue', 'view', str(linked[0]['number']), '--json', 'body,labels', *repo)) \
            if linked else {'body': '', 'labels': []}
        if not linked and not re.search(r'#\d+', pr['body']):
            return ['the PR body must close its issue (`closes #N`) so its acceptance criteria can be checked']
        is_bug = any(label['name'] == 'bug' for label in issue['labels'])
        return rules.ready_problems(pr['body'], issue['body'], is_bug, [c['body'] for c in pr['comments']])
    return []


def main() -> int:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # the comment's arrow breaks a cp1250 console
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('number', type=int)
    parser.add_argument('--to', required=True, choices=STATUS)
    parser.add_argument('--reason', required=True, help='one line: why the label moves')
    parser.add_argument('--signer', required=True, choices=rules.SIGNERS)
    parser.add_argument('--self-check-file', help='required for --to blocked')
    parser.add_argument('--pr', type=int, help='the draft PR, when starting work on an issue')
    parser.add_argument('--add', action='append', default=[], metavar='LABEL',
                        help='side label with the status: on-hold (with --to blocked and "Blocked by #N" in '
                             '--reason) or question; repeatable')
    parser.add_argument('--remove', action='append', default=[], metavar='LABEL',
                        help='side label to take off (question, on-hold); leaving blocked drops on-hold itself')
    parser.add_argument('--repo')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    repo = ['--repo', args.repo] if args.repo else []

    listed = gh('issue', 'view', str(args.number), '--json', 'labels', '-q', '.labels[].name', *repo).split()
    current = [name for name in listed if name in STATUS and name != args.to]
    problems = gate(args, current, repo)
    if problems:
        print('refused:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1

    before = ', '.join(current) if current else '(none)'
    edit = ['issue', 'edit', str(args.number), '--add-label', args.to]
    for name in current:
        edit += ['--remove-label', name]
    edit += side_edits(args, listed)
    after = ' + '.join([args.to, *args.add])
    comment = f'# {args.signer}\n\nLabel: {before} → {after} — {args.reason}\n'
    if needs_self_check(args):
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
