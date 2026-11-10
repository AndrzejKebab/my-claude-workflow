#!/usr/bin/env python3
"""Ping the owner on Discord from a bot profile, in that bot's own thread, with the owner mentioned.

Programs started: hermes (send).

The thread is read from the profile's `DISCORD_HOME_CHANNEL`, so no bot ever types a channel id: a
copied command from an old turn cannot send to a retired channel, and a missing mention cannot
produce a message the owner never sees.

    python ping_owner.py --as manager "Need your decision on #394: inner corners connect? -> <link>"
    python ping_owner.py --as reviewer --dry-run "..."
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import os

_home = Path(os.environ.get('HERMES_HOME') or r'F:\Programowanie\KebabAI OS\Hermes')
HERMES = _home.parents[1] if _home.parent.name == 'profiles' else _home  # a bot's HERMES_HOME is profiles/<bot>
OWNER = '<@384732396806733846>'
PROFILES = ('advisor', 'manager', 'reviewer') + tuple(f'worker-{n}' for n in range(1, 6))


def home_channel(profile: str) -> str:
    env = HERMES / 'profiles' / profile / '.env'
    for line in env.read_text(encoding='utf-8').splitlines():
        if line.startswith('DISCORD_HOME_CHANNEL='):
            value = line.split('=', 1)[1].strip().strip('"\'')
            if value:
                return value
    raise SystemExit(f'{profile} has no DISCORD_HOME_CHANNEL in its .env; ask the owner which thread it uses')


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').split('\n')[0])
    parser.add_argument('--as', dest='profile', required=True, choices=PROFILES)
    parser.add_argument('--dry-run', action='store_true', help='print what would be sent, send nothing')
    parser.add_argument('text', help='one line: "Need your decision on #<n>: <question> -> <link>"')
    args = parser.parse_args()

    text = ' '.join(args.text.split())
    if OWNER in text:
        text = text.replace(OWNER, '').strip()
    message = f'{OWNER} {text}'
    channel = home_channel(args.profile)

    if args.dry_run:
        print(f'would send to discord:{channel} as {args.profile}: {message}')
        return 0
    result = subprocess.run(['hermes', '-p', args.profile, 'send', '--to', f'discord:{channel}', message],
                            capture_output=True, text=True, encoding='utf-8', errors='replace')
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or 'sent' not in output.lower():
        print(f'NOT SENT ({result.returncode}): {output[-300:]}')
        return 1
    print(f'sent to discord:{channel}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
