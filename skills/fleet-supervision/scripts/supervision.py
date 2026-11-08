#!/usr/bin/env python3
"""The Advisor's supervision ledger: record each check of a first-line item, and say what to check next.

    supervision.py record --ledger <file.jsonl> --bot reviewer --category issues --outcome agree|disagree|skipped
                          --item "PR #431 round 2" --why "<one line; required for disagree>"
    supervision.py should-check --ledger <file.jsonl> --bot reviewer --category issues   # prints yes / no
    supervision.py status --ledger <file.jsonl> [--bot reviewer]

A bot and category start in full checking; 90% agreement over the last 20 checks earns a 1-in-5 spot check;
a disagreement in spot mode restores full checking and restarts the count. Programs started: none.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

WINDOW, RATE, SPOT_EVERY = 20, 0.9, 5


def mode(history: list[dict]) -> str:
    current, window = 'full', []
    for entry in history:
        if entry['outcome'] == 'skipped':
            continue
        if current == 'spot' and entry['outcome'] == 'disagree':
            current, window = 'full', []
            continue
        window = (window + [entry['outcome']])[-WINDOW:]
        if current == 'full' and len(window) == WINDOW and window.count('agree') / WINDOW >= RATE:
            current = 'spot'
    return current


def should_check(history: list[dict]) -> bool:
    if mode(history) == 'full':
        return True
    skipped = 0
    for entry in reversed(history):
        if entry['outcome'] != 'skipped':
            break
        skipped += 1
    return skipped >= SPOT_EVERY - 1


def load(ledger: Path, bot: str | None = None, category: str | None = None) -> list[dict]:
    if not ledger.exists():
        return []
    rows = [json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines() if line.strip()]
    return [r for r in rows if (bot is None or r['bot'] == bot) and (category is None or r['category'] == category)]


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    rec, check, status = sub.add_parser('record'), sub.add_parser('should-check'), sub.add_parser('status')
    for p in (rec, check, status):
        p.add_argument('--ledger', required=True)
        p.add_argument('--bot', required=p is not status)
    for p in (rec, check):
        p.add_argument('--category', required=True)
    rec.add_argument('--outcome', required=True, choices=('agree', 'disagree', 'skipped'))
    rec.add_argument('--item', required=True)
    rec.add_argument('--why', default='')
    args = parser.parse_args()
    ledger = Path(args.ledger)

    if args.command == 'record':
        if args.outcome == 'disagree' and not args.why.strip():
            print('refused: a disagreement needs --why (and a draft lesson)', file=sys.stderr)
            return 2
        ledger.parent.mkdir(parents=True, exist_ok=True)
        entry = {'at': dt.datetime.now().isoformat(timespec='seconds'), 'bot': args.bot, 'category': args.category,
                 'outcome': args.outcome, 'item': args.item, 'why': args.why}
        with ledger.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(entry) + '\n')
        print(f'{args.bot}/{args.category}: {mode(load(ledger, args.bot, args.category))}')
        return 0
    if args.command == 'should-check':
        print('yes' if should_check(load(ledger, args.bot, args.category)) else 'no')
        return 0
    rows = load(ledger, args.bot)
    for bot, category in sorted({(r['bot'], r['category']) for r in rows}):
        history = [r for r in rows if r['bot'] == bot and r['category'] == category]
        checked = [r for r in history if r['outcome'] != 'skipped'][-WINDOW:]
        agree = sum(r['outcome'] == 'agree' for r in checked)
        print(f'{bot}/{category}: {mode(history)}, {agree}/{len(checked)} agreed in the last {len(checked)} checks')
    if not rows:
        print('no checks recorded')
    return 0


if __name__ == '__main__':
    sys.exit(main())
