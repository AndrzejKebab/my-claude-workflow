#!/usr/bin/env python3
"""Post a review whose flag follows from the body, or approve a work plan.

    review.py 261 -f .scratch/review-261.md [--repo owner/name]   # Issues to Fix -> request-changes
    review.py 261 -f body.md --approve                            # refused while an item is open
    review.py 261 --approve-plan "Phase_10_Part_2_Plan §5.3"      # posts `Plan approved: <step>`

Every item under `### Issues to Fix` ends with its grounds: (criterion: "…"), (rule: …) or (breakage: …).
Programs started: gh.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # found when run isolated or through a shim
import fleet_rules as rules  # noqa: E402


def gh(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(['gh', *args], input=stdin, capture_output=True, text=True, encoding='utf-8',
                          errors='replace')


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('number', type=int, help='pull request number')
    parser.add_argument('-f', '--file', help='markdown body; first line is `# <Signer>`')
    parser.add_argument('--repo')
    parser.add_argument('--approve', action='store_true', help='approve the PR (final pass only)')
    parser.add_argument('--approve-plan', metavar='STEP', help='approve the draft PR\'s work plan for this step')
    parser.add_argument('--signer', default='Reviewer', choices=rules.SIGNERS, help='for --approve-plan')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    repo = ['--repo', args.repo] if args.repo else []

    if args.approve_plan:
        body = f'# {args.signer}\n\nPlan approved: {args.approve_plan}\n'
        if args.dry_run:
            print(body)
            return 0
        result = gh('pr', 'comment', str(args.number), '-F', '-', *repo, stdin=body)
        print(result.stdout.strip() or result.stderr.strip())
        return result.returncode

    if not args.file:
        parser.error('-f is required unless --approve-plan')
    body = open(args.file, encoding='utf-8').read()
    first = body.splitlines()[0].strip() if body.strip() else ''
    problems = ([] if rules.SIGNATURE.match(first) else ['first line must be `# <Signer>`'])
    problems += rules.review_problems(body)
    open_items = rules.has_open_issues(body)
    if args.approve and open_items:
        problems.append('refusing to approve: an Issue to Fix is still open')
    if problems:
        print('refused:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1

    flag = '--approve' if args.approve else '--request-changes' if open_items else '--comment'
    command = ['pr', 'review', str(args.number), flag, '-F', args.file, *repo]
    print(f'{flag} with {args.file}')
    if args.dry_run:
        print('gh', ' '.join(command))
        return 0
    result = gh(*command)
    if result.returncode != 0:
        print(result.stderr.strip() or 'gh pr review failed', file=sys.stderr)
        return 1
    shown = gh('pr', 'view', str(args.number), '--json', 'reviews', '-q', '.reviews | last | "\\(.state) \\(.url)"',
               *repo)
    print(shown.stdout.strip() or 'review posted')
    return 0


if __name__ == '__main__':
    sys.exit(main())
