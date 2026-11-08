"""The `lesson-detect` job: find amnesia in bot transcripts, wake the bot that erred, record every event.

Only a false "cannot" wakes a bot (design.md #19, #22-23); headless blocks and broad "cannot" claims are
recorded for the daily counts. Events go to `events.jsonl` in the data dir.
"""
from __future__ import annotations

import datetime
import json
import sqlite3
import sys
import time
from dataclasses import asdict
from pathlib import Path

import board
import fleet_metrics

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'skills' / 'fleet-lessons' / 'scripts'))
import lesson  # noqa: E402

GENERAL_HOME = ROOT / 'memory' / 'shared'
PROFILES = ('advisor', 'manager', 'reviewer') + tuple(f'worker-{n}' for n in range(1, 6))
NOT_WOKEN = {'advisor'}
# Every wake from this job starts with this; a claim made inside such a turn is a repeat, not a new wake.
MARK = 'Watchdog: lesson check'


def rows_after(profile: str, after: int) -> list[tuple]:
    database = board.HERMES_ROOT / 'profiles' / profile / 'state.db'
    if not database.exists():
        return []
    connection = sqlite3.connect(f'file:{database.as_posix()}?mode=ro', uri=True, timeout=10)
    try:
        return list(fleet_metrics._rows(connection, after))
    finally:
        connection.close()


def homes() -> list[Path]:
    return [GENERAL_HOME, board.REPO / '.memory' / 'lessons']


def covering_lesson(category: str) -> tuple[str, str]:
    """(slug, what to do) of an accepted lesson whose symptom names this guard category exactly."""
    for home in homes():
        if not home.is_dir():
            continue
        for path in lesson.lessons(home):
            text = path.read_text(encoding='utf-8')
            if f'({category})' in lesson.symptom_of(text):
                fix = text.split('## What to do', 1)[-1].split('\n## ', 1)[0].strip() if '## What to do' in text else ''
                return path.stem, ' '.join(fix.split())
    return '', ''


def stamp(ts: float) -> str:
    return time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))


def message(event: dict, slug: str, fix: str) -> str:
    lines = [
        f'{MARK} - at {stamp(event["timestamp"])} you wrote: "{event["text"][:200]}"',
        f'Just before that, the guard blocked a `{event["category"]}` command because the turn was headless '
        f'(a DM or a wake): headless turns deny flagged commands, Bot Chat turns approve them. You ran the same '
        f'kind of command earlier in this session (message {event["approved_id"]}, {stamp(event["approved_ts"])}); '
        f'session search finds it.',
    ]
    if slug:
        lines.append(f'Lesson `{slug}` covers this: {fix} No new lesson is needed.')
    else:
        lines.append('No lesson covers this. Find the form that passes in a headless turn, then write a draft '
                     'lesson with `lesson.py add` (fleet-lessons skill), with the exact command and its result as '
                     'evidence.')
    lines.append('Then finish the task you said you could not do. If your claim was true for another reason, reply '
                 'with one line saying why, and do nothing else.')
    return '\n\n'.join(lines)


def record(event: dict, action: str) -> None:
    path = board.STATE_FILE.parent / 'events.jsonl'
    if board.DRY_RUN:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({**event, 'action': action}, ensure_ascii=False) + '\n')


def lesson_detect(now: float, state: dict) -> list[str]:
    pending = state.setdefault('pending', [])
    for profile in PROFILES:
        scanned = state.get(f'scan#{profile}')
        first = scanned is None
        scanned = scanned or {'last_id': 0, 'carry': {}}
        rows = rows_after(profile, scanned['last_id'])
        if not rows:
            state[f'scan#{profile}'] = scanned
            continue
        events, scanned['carry'] = fleet_metrics.scan(rows, scanned['carry'])
        scanned['last_id'] = rows[-1][0]
        state[f'scan#{profile}'] = scanned
        if first:
            board.log(f'{profile}: first scan of {len(rows)} rows, history not acted on '
                      f'({len(events["false_cannot"])} false cannot)')
            continue
        for kind in ('headless_block', 'cannot_claim'):
            for found in events[kind]:
                record({**asdict(found), 'profile': profile}, 'recorded')
        for found in events['false_cannot']:
            event = {**asdict(found), 'profile': profile}
            if profile in NOT_WOKEN:
                record(event, 'recorded')
            elif found.turn.startswith(MARK):
                record(event, 'repeat after teaching')
            else:
                pending.append(event)

    left = []
    for event in pending:
        profile = event['profile']
        day = datetime.date.fromtimestamp(now).isoformat()
        cap = f'lessonwake#{profile}#{event["category"]}#{day}'
        if cap in state:
            record(event, 'capped')
            continue
        if board.turn_running(profile):
            left.append(event)
            continue
        slug, fix = covering_lesson(event['category'])
        state[cap] = now
        record(event, f'woken, lesson {slug} failed in use' if slug else 'woken, draft asked')
        if board.DRY_RUN:
            board.log(f'would wake {profile} for a false cannot ({event["category"]})')
            continue
        board.wake(profile, message(event, slug, fix))
        board.log(f'woke {profile} for a false cannot ({event["category"]}, lesson {slug or "none"})')
    state['pending'] = left
    today = datetime.date.fromtimestamp(now).isoformat()
    for key in [k for k in state if k.startswith('lessonwake#') and not k.endswith(today)]:
        del state[key]
    return []
