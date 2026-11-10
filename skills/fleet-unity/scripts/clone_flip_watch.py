#!/usr/bin/env python3
"""Catch whoever moves a clone's checkout: sample the branch, and on a change snapshot every live process command
line plus the old and new branch, so the culprit is a fact.

    clone_flip_watch.py --repo <clone> --out <log.jsonl> [--minutes 45]

Programs started: git (branch reads).
"""
import argparse
import json
import subprocess
import sys
import time

import psutil


def branch(repo: str) -> str:
    try:
        return subprocess.run(['git', '-C', repo, 'branch', '--show-current'],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception as error:  # noqa: BLE001 - a watcher must not die on one read
        return f'<error {error}>'


def snapshot(out: str, tag: str, old: str, new: str) -> None:
    rows = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'ppid']):
        try:
            rows.append({'pid': p.info['pid'], 'ppid': p.info['ppid'], 'name': p.info['name'],
                         'cmd': ' '.join(p.info['cmdline'] or [])[:400],
                         'born': time.strftime('%H:%M:%S', time.localtime(p.info['create_time']))})
        except psutil.Error:
            continue
    hot = [r for r in rows if any(k in r['cmd'].lower() for k in ('git', 'checkout', 'switch', 'hermes'))]
    with open(out, 'a', encoding='utf-8') as handle:
        handle.write(json.dumps({'at': time.strftime('%H:%M:%S'), 'tag': tag, 'old': old,
                                 'new': new, 'hot': hot[:40], 'count': len(rows)}) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('--repo', required=True, help='the clone to watch')
    parser.add_argument('--out', required=True, help='JSON-lines log, one line per change')
    parser.add_argument('--minutes', type=float, default=45)
    args = parser.parse_args()
    deadline = time.time() + args.minutes * 60
    last = branch(args.repo)
    snapshot(args.out, 'start', '', last)
    while time.time() < deadline:
        time.sleep(2)
        now = branch(args.repo)
        if now != last:
            snapshot(args.out, 'flip', last, now)
            last = now
    return 0


if __name__ == '__main__':
    sys.exit(main())
