#!/usr/bin/env python3
"""Fleet counts from Hermes transcripts and GitHub, plus the trend trigger the daily job uses.

    python fleet_metrics.py baseline --hermes-home <dir> --profiles manager,reviewer,worker-1 \
        --repo owner/name --since 2026-10-01 --out <file.json> [--samples 20] [--skip-github]

Stdlib only: the cron interpreter has no site-packages. Reads every database read-only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sqlite3
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

APPROVED = re.compile(r'flagged \(([^)]+)\) and auto-approved')
HEADLESS_BLOCK = re.compile(r'BLOCKED: Command flagged as dangerous \(([^)]+)\) but single-query')
# First person only: "the worktree cannot compile" describes the code, "I cannot run it" claims inability.
CANNOT = re.compile(r"\b(I|I'm|I am|we)\s+(cannot|can't|can not|could not|couldn't|am unable to|was unable to|"
                    r"have no way to|am not able to|don't have (a |the )?(way|tool|access))\b", re.I)
NOT_A_TURN = ('[CONTEXT COMPACTION', '[IMPORTANT: Background process')
SIGNER = re.compile(r'^#\s+(.+?)\s*$')
STATUS_LABELS = {'ready', 'in-progress', 'waits-for-review', 'in-review', 'waits-for-final-review',
                 'waits-for-eye-review', 'ready-to-merge', 'blocked', 'needs-owner', 'needs-human'}


def final_review_bounces(labels: list[str]) -> int:
    """Times a PR went from waiting for final review back to the author, over status labels only."""
    status = [name.removeprefix('status:') for name in labels if name.removeprefix('status:') in STATUS_LABELS]
    return sum(1 for a, b in zip(status, status[1:]) if a == 'waits-for-final-review' and b == 'in-progress')


@dataclass(frozen=True)
class Event:
    kind: str
    session: str
    message_id: int
    timestamp: float
    category: str
    text: str


def _rows(db: sqlite3.Connection):
    return db.execute('select id, session_id, role, coalesce(content, ""), timestamp from messages order by id')


def turn_starts(db: sqlite3.Connection) -> list[float]:
    """Timestamps of user rows that start a turn: owner messages, peer DMs, wakes."""
    return [ts for _, _, role, text, ts in _rows(db)
            if role == 'user' and not text.lstrip().startswith(NOT_A_TURN)]


def headless_blocks(db: sqlite3.Connection) -> list[Event]:
    events = []
    for mid, session, role, text, ts in _rows(db):
        if role == 'tool' and (match := HEADLESS_BLOCK.search(text)):
            events.append(Event('headless_block', session, mid, ts, match.group(1), text[:200]))
    return events


def false_cannot(db: sqlite3.Connection) -> list[Event]:
    """A headless block of a command category the guard had approved earlier in the same session,
    followed in that turn by a claim of inability. Replayed claims (same session, same text) count once."""
    approved: dict[str, set[str]] = {}
    pending: dict[str, str] = {}
    seen: set[tuple[str, str]] = set()
    events = []
    for mid, session, role, text, ts in _rows(db):
        if role == 'tool':
            if match := APPROVED.search(text):
                approved.setdefault(session, set()).add(match.group(1))
            elif (match := HEADLESS_BLOCK.search(text)) and match.group(1) in approved.get(session, set()):
                pending[session] = match.group(1)
        elif role == 'user' and not text.lstrip().startswith(NOT_A_TURN):
            pending.pop(session, None)
        elif role == 'assistant' and session in pending and CANNOT.search(text):
            if (session, text) not in seen:
                seen.add((session, text))
                events.append(Event('false_cannot', session, mid, ts, pending[session], text[:300]))
            pending.pop(session, None)
    return events


def cannot_claims(db: sqlite3.Connection) -> list[Event]:
    """Broad secondary count: any assistant text claiming inability, replays counted once."""
    seen, events = set(), []
    for mid, session, role, text, ts in _rows(db):
        if role == 'assistant' and CANNOT.search(text) and (session, text) not in seen:
            seen.add((session, text))
            events.append(Event('cannot_claim', session, mid, ts, '', text[:300]))
    return events


def simulate_trigger(days: list[tuple[int, int]], *, base_days: int, window_days: int, factor: float,
                     min_events: int, hold_days: int, cooldown_days: int) -> list[int]:
    """Day indexes where the trend trigger fires. `days` holds (events, denominator) per day, oldest first.

    Fires when the window rate is at least `factor` times the base rate, the window has `min_events`, and that
    held for `hold_days` days in a row. A fire silences the count for `cooldown_days` unless the rate gets
    another `factor` worse. A base with no events counts as one event, so a zero base cannot divide by zero.
    """
    fires, streak, last_rate, last_fire = [], 0, 0.0, None
    for i in range(base_days + window_days - 1, len(days)):
        window = days[i - window_days + 1:i + 1]
        base = days[i - window_days - base_days + 1:i - window_days + 1]
        events = sum(e for e, _ in window)
        rate = events / max(sum(d for _, d in window), 1)
        base_rate = max(sum(e for e, _ in base), 1) / max(sum(d for _, d in base), 1)
        streak = streak + 1 if events >= min_events and rate >= factor * base_rate else 0
        if streak >= hold_days and (last_fire is None or i - last_fire >= cooldown_days
                                    or rate >= factor * last_rate):
            fires.append(i)
            last_fire, last_rate = i, rate
    return fires


def daily_series(events: list[Event], turns: list[float], dates: list[dt.date]) -> list[tuple[int, int]]:
    count = {d: 0 for d in dates}
    denominator = {d: 0 for d in dates}
    for event in events:
        day = dt.datetime.fromtimestamp(event.timestamp).date()
        if day in count:
            count[day] += 1
    for ts in turns:
        day = dt.datetime.fromtimestamp(ts).date()
        if day in denominator:
            denominator[day] += 1
    return [(count[d], denominator[d]) for d in dates]


def _gh(args: list[str], cache: Path) -> list:
    key = cache / (re.sub(r'[^A-Za-z0-9]+', '_', ' '.join(args))[:180] + '.json')
    if key.exists():
        return json.loads(key.read_text(encoding='utf-8'))
    for attempt in range(3):  # transient GitHub errors: three tries, then fail with gh's own message
        result = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            break
        time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError(f'gh {" ".join(args)}: {result.stderr.strip()[-300:]}')
    out = result.stdout
    data =[json.loads(line) for line in out.splitlines() if line.strip()]
    key.write_text(json.dumps(data), encoding='utf-8')
    return data


def _signer(body: str) -> str:
    first = (body or '').strip().splitlines()[0] if (body or '').strip() else ''
    match = SIGNER.match(first)
    if not match:
        return 'unsigned'
    return re.sub(r'^Worker[ -]?(\d)$', r'Worker-\1', match.group(1))


def pr_stats(repo: str, since: str, cache: Path, state: str = 'merged') -> list[dict]:
    """Per PR (merged since `since`, or open now): posts and characters by signer, review requests, age,
    final-review bounces. Open PRs are aged to now, so a long-running one shows how long it has run."""
    cache.mkdir(parents=True, exist_ok=True)
    search = ['--search', f'merged:>={since}'] if state == 'merged' else []
    prs = _gh(['pr', 'list', '-R', repo, '--state', state, '--limit', '500', *search,
               '--json', 'number,createdAt,mergedAt', '-q', '.[] | @json'], cache)
    now = dt.datetime.now(dt.timezone.utc)
    stats = []
    for pr in prs:
        n = pr['number']
        posts = (_gh(['api', '--paginate', f'repos/{repo}/issues/{n}/comments', '-q', '.[] | @json'], cache)
                 + _gh(['api', '--paginate', f'repos/{repo}/pulls/{n}/reviews', '-q', '.[] | @json'], cache))
        timeline = _gh(['api', '--paginate', f'repos/{repo}/issues/{n}/timeline', '-q', '.[] | @json'], cache)
        by_signer: dict[str, list[int]] = {}
        for post in posts:
            body = post.get('body') or ''
            if body.strip():
                entry = by_signer.setdefault(_signer(body), [0, 0])
                entry[0] += 1
                entry[1] += len(body)
        labels = [e['label']['name'].removeprefix('status:') for e in timeline
                  if e.get('event') == 'labeled' and e.get('label')]
        created = dt.datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
        ended = dt.datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00')) if pr.get('mergedAt') else now
        stats.append({'pr': n, 'posts': sum(v[0] for v in by_signer.values()),
                      'chars': sum(v[1] for v in by_signer.values()), 'by_signer': by_signer,
                      'review_requests': labels.count('waits-for-review'),
                      'final_review_bounces': final_review_bounces(labels),
                      'age_days': round((ended - created).total_seconds() / 86400, 2)})
    return stats


def _summary(values: list[float]) -> dict:
    if not values:
        return {'n': 0}
    return {'n': len(values), 'median': statistics.median(values), 'mean': round(statistics.mean(values), 2),
            'max': max(values)}


def baseline(args) -> dict:
    home = Path(args.hermes_home)
    start = dt.date.fromisoformat(args.since)
    end = dt.date.today()
    report = {'since': args.since, 'until': end.isoformat(), 'bots': {}, 'calibration': {}, 'samples': {}}
    fleet_turns: dict[dt.date, int] = {}
    per_bot = {}
    for profile in args.profiles.split(','):
        db = sqlite3.connect(f'file:{home / "profiles" / profile / "state.db"}?mode=ro', uri=True)
        turns = [ts for ts in turn_starts(db) if dt.datetime.fromtimestamp(ts).date() >= start]
        counts = {'false_cannot': false_cannot(db), 'headless_block': headless_blocks(db),
                  'cannot_claim': cannot_claims(db)}
        counts = {k: [e for e in v if dt.datetime.fromtimestamp(e.timestamp).date() >= start] for k, v in counts.items()}
        for ts in turns:
            day = dt.datetime.fromtimestamp(ts).date()
            fleet_turns[day] = fleet_turns.get(day, 0) + 1
        per_bot[profile] = (turns, counts)
        report['bots'][profile] = {'turns': len(turns),
                                   **{k: {'events': len(v), 'per_100_turns': round(100 * len(v) / max(len(turns), 1), 2)}
                                      for k, v in counts.items()}}
        if args.samples:
            report['samples'][profile] = {k: [asdict(e) for e in v[-args.samples:]] for k, v in counts.items()}
    # Days the whole fleet was down (no turns anywhere) are not days: they would read as a quiet stretch.
    dates = sorted(d for d, n in fleet_turns.items() if n > 0)
    report['live_days'] = len(dates)
    for base_days in (14, 28):
        for factor in (1.25, 1.5, 2.0, 3.0):
            key = f'base{base_days}_x{factor}'
            row = {}
            # Per-bot counts are often too sparse to reach min_events; the fleet-wide series shows whether
            # aggregating would make the trigger usable.
            fleet = ([t for turns, _ in per_bot.values() for t in turns],
                     {kind: [e for _, counts in per_bot.values() for e in counts[kind]] for kind in
                      next(iter(per_bot.values()))[1]})
            for profile, (turns, counts) in [*per_bot.items(), ('fleet', fleet)]:
                for kind, events in counts.items():
                    series = daily_series(events, turns, dates)
                    fires = simulate_trigger(series, base_days=base_days, window_days=7, factor=factor,
                                             min_events=args.min_events, hold_days=2, cooldown_days=7)
                    row[f'{profile}/{kind}'] = {'fires': len(fires),
                                                'evaluable_days': max(len(series) - base_days - 6, 0)}
            report['calibration'][key] = row
    if not args.skip_github:
        stats = pr_stats(args.repo, args.since, Path(args.cache))
        report['prs'] = {'merged': len(stats),
                         **{k: _summary([s[k] for s in stats])
                            for k in ('posts', 'chars', 'review_requests', 'final_review_bounces', 'age_days')},
                         'bounced_prs': sum(1 for s in stats if s['final_review_bounces'])}
        report['pr_detail'] = stats
        open_prs = pr_stats(args.repo, args.since, Path(args.cache), state='open')
        # Decision 47's trigger (5 review rounds or 7 days open) would fire on these the day it goes live.
        report['open_prs'] = [{k: s[k] for k in ('pr', 'posts', 'chars', 'review_requests', 'age_days')}
                              | {'long_pr_trigger': s['review_requests'] >= 5 or s['age_days'] >= 7}
                              for s in open_prs]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    base = sub.add_parser('baseline', help='counts over history plus trigger calibration')
    base.add_argument('--hermes-home', required=True)
    base.add_argument('--profiles', required=True, help='comma-separated profile names')
    base.add_argument('--repo', help='owner/name for PR counts')
    base.add_argument('--since', required=True, help='YYYY-MM-DD')
    base.add_argument('--out', required=True)
    base.add_argument('--cache', help='GitHub response cache dir (default: <out>.ghcache)')
    base.add_argument('--samples', type=int, default=0, help='keep the last N events per count for hand-checking')
    base.add_argument('--skip-github', action='store_true')
    base.add_argument('--min-events', type=int, default=5, help='trigger minimum events in the 7-day window')
    args = parser.parse_args()
    if not args.skip_github and not args.repo:
        parser.error('--repo is required unless --skip-github')
    args.cache = args.cache or args.out + '.ghcache'
    report = baseline(args)
    Path(args.out).write_text(json.dumps(report, indent=1, default=str), encoding='utf-8')
    print(f'wrote {args.out}: {report["live_days"]} live days, {len(report["bots"])} bots')
    return 0


if __name__ == '__main__':
    sys.exit(main())
