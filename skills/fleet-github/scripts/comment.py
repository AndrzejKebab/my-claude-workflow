#!/usr/bin/env python3
"""Post a signed PR or issue comment that passes the fleet's rules, or say exactly why not.

    comment.py --pr 286 --body-file body.md --signer "# Worker-3"
    echo body | comment.py --issue 274 --stdin --signer "# Manager"

Refused: a missing or wrong signer, an acknowledgement opener, more than 2000 characters outside
<details> blocks, local paths.
Programs started: gh.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # found when run isolated or through a shim
import fleet_rules as rules  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--pr', type=int)
    target.add_argument('--issue', type=int)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--body-file')
    source.add_argument('--stdin', action='store_true')
    parser.add_argument('--signer', required=True, help="exact first line, e.g. '# Worker-3'")
    parser.add_argument('--repo')
    parser.add_argument('--allow-paths', action='store_true', help='post despite local paths (say why in the body)')
    parser.add_argument('--dry-run', action='store_true', help='run the checks only')
    args = parser.parse_args()

    body = sys.stdin.read() if args.stdin else Path(args.body_file).read_text(encoding='utf-8')
    problems = rules.comment_problems(body, args.signer, allow_paths=args.allow_paths)
    if problems:
        print('refused:\n- ' + '\n- '.join(problems), file=sys.stderr)
        return 1
    kind, number = ('pr', args.pr) if args.pr else ('issue', args.issue)
    if args.dry_run:
        print(f'would comment on {kind} {number} ({len(body)} chars)')
        return 0
    repo = ['--repo', args.repo] if args.repo else []
    result = subprocess.run(['gh', kind, 'comment', str(number), '-F', '-', *repo], input=body, capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(f'gh exited {result.returncode}: {result.stderr.strip()}', file=sys.stderr)
        return 1
    print(result.stdout.strip())
    return 0


if __name__ == '__main__':
    sys.exit(main())
