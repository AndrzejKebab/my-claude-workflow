#!/usr/bin/env python3
"""Add the fleet's raw-gh deny globs to profiles' approvals.deny, keeping every existing entry.

    deny_apply.py --profile worker-1 --profile reviewer [--globs ../deny-globs.txt] [--dry-run]

Goes through `hermes config set`, never by editing config.yaml. Prove the result with
bot-tools/hermes/deny_check.py and ../deny-cases.txt. Programs started: hermes.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def hermes(*args: str) -> str:
    result = subprocess.run(['hermes', *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        sys.exit(f'hermes {" ".join(args)}: {result.stderr.strip() or result.stdout.strip()}')
    return result.stdout


def current_deny(profile: str) -> list[str]:
    out = hermes('-p', profile, 'config', 'get', 'approvals.deny')
    items = []
    for line in out.splitlines():
        if line.lstrip().startswith('- '):
            value = line.lstrip()[2:].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '\'"':
                value = value[1:-1].replace("''", "'") if value[0] == "'" else json.loads(value)
            items.append(value)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('--profile', action='append', required=True)
    parser.add_argument('--globs', default=str(Path(__file__).resolve().parents[1] / 'deny-globs.txt'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    wanted = [g.strip() for g in Path(args.globs).read_text(encoding='utf-8').splitlines() if g.strip()]
    for profile in args.profile:
        have = current_deny(profile)
        added = [g for g in wanted if g not in have]
        print(f'{profile}: {len(have)} existing, adding {len(added)}')
        if added and not args.dry_run:
            hermes('-p', profile, 'config', 'set', 'approvals.deny', json.dumps(have + added))
            missing = [g for g in have + added if g not in current_deny(profile)]
            if missing:
                sys.exit(f'{profile}: read-back is missing {missing[:3]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
