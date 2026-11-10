"""The daily digest, the Advisor's daily batch and the trend trigger (design.md #19-23, #27-28).

`daily` builds the facts. With work for the Advisor it writes them to `digest-<date>.md`, wakes the Advisor and
leaves a `.pending.json`; `board-audit` sends the digest once the Advisor's notes file exists, or the facts alone
after NOTES_HOURS. With no work the digest goes out at once, through the Advisor's Discord account.
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import sys
import time
from pathlib import Path

import board
import fleet_metrics
import lesson_detect

SUPERVISION = lesson_detect.ROOT / 'skills' / 'fleet-supervision' / 'scripts' / 'supervision.py'
WATCHED = {'false_cannot': 'false "cannot"', 'headless_block': 'headless blocks'}
REPORTED = {'cannot_claim': '"cannot" claims'}
BOTS = tuple(p for p in lesson_detect.PROFILES if p != 'advisor')
TRIGGER = dict(base_days=14, window_days=7, factor=1.5, hold_days=2, cooldown_days=7)
MIN_EVENTS = {'fleet': 5, 'bot': 3}
NOTES_HOURS = 3
DIGEST_PROFILE = 'advisor'


def database(profile: str) -> sqlite3.Connection | None:
    path = board.HERMES_ROOT / 'profiles' / profile / 'state.db'
    return sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True, timeout=10) if path.exists() else None


def history(profile: str) -> tuple[list[float], dict[str, list]]:
    """Turn starts and every event kind for one bot, from its whole transcript."""
    db = database(profile)
    if db is None:
        return [], {kind: [] for kind in (*WATCHED, *REPORTED)}
    try:
        turns = fleet_metrics.turn_starts(db)
        events, _ = fleet_metrics.scan(fleet_metrics._rows(db), {})
    finally:
        db.close()
    return turns, events


def live_days(turns_by_bot: dict[str, list[float]], today: dt.date) -> list[dt.date]:
    """Complete days with at least one turn anywhere: a day the fleet was off is not a quiet day."""
    days = {dt.datetime.fromtimestamp(ts).date() for turns in turns_by_bot.values() for ts in turns}
    return sorted(day for day in days if day < today)


def trends(now: float) -> tuple[list[str], list[str], bool]:
    """(count lines, trigger lines, Reviewer or Manager active in the last day)."""
    today = dt.date.fromtimestamp(now)
    data = {bot: history(bot) for bot in BOTS}
    dates = live_days({bot: turns for bot, (turns, _) in data.items()}, today)
    span = TRIGGER['window_days']
    series_of = {}
    for bot, (turns, events) in data.items():
        for kind in (*WATCHED, *REPORTED):
            series_of[(bot, kind)] = fleet_metrics.daily_series(events[kind], turns, dates)
    for kind in (*WATCHED, *REPORTED):
        per_bot = [series_of[(bot, kind)] for bot in BOTS]
        series_of[('fleet', kind)] = [(sum(day[0] for day in days), sum(day[1] for day in days))
                                      for days in zip(*per_bot)] if dates else []

    def rate(part):
        return sum(e for e, _ in part), 100 * sum(e for e, _ in part) / max(sum(t for _, t in part), 1)

    counts, fired = [], []
    for who in ('fleet', *BOTS):
        parts = []
        for kind, name in {**WATCHED, **REPORTED}.items():
            series = series_of[(who, kind)]
            events, now_rate = rate(series[-span:])
            _, base_rate = rate(series[-span - TRIGGER['base_days']:-span])
            if who == 'fleet' or events:
                parts.append(f'{name} {events} ({now_rate:.2f}/100 turns, base {base_rate:.2f})')
            if kind in WATCHED and len(series) >= TRIGGER['base_days'] + TRIGGER['window_days']:
                fires = fleet_metrics.simulate_trigger(
                    series, min_events=MIN_EVENTS['fleet' if who == 'fleet' else 'bot'], **TRIGGER)
                if fires and fires[-1] == len(series) - 1:
                    fired.append(f'{who} {name}: {events} in 7 days, {now_rate:.2f}/100 turns against a base of '
                                 f'{base_rate:.2f}')
        if parts:
            counts.append(f'{who}: ' + ', '.join(parts))
    since = now - 86400
    active = any(ts >= since for bot in ('reviewer', 'manager') for ts in data[bot][0])
    if len(dates) < TRIGGER['base_days'] + TRIGGER['window_days']:
        counts.append(f'(trend trigger needs {TRIGGER["base_days"] + TRIGGER["window_days"]} live days; '
                      f'{len(dates)} so far)')
    return counts, fired, active


def lesson_files(since: float) -> tuple[list[Path], list[str]]:
    """(drafts waiting, lessons accepted or retired since `since`) across both homes."""
    drafts, changed = [], []
    for home in lesson_detect.homes():
        if not home.is_dir():
            continue
        drafts += sorted((home / 'drafts').glob('*.md')) if (home / 'drafts').is_dir() else []
        for path in lesson_detect.lesson.lessons(home):
            if path.stat().st_mtime >= since:
                changed.append(f'accepted or changed: {path.stem}')
        for path in sorted((home / 'retired').glob('*.md')) if (home / 'retired').is_dir() else []:
            if path.stat().st_mtime >= since:
                changed.append(f'retired: {path.stem}')
    return drafts, changed


def lesson_events(since: float) -> tuple[dict[str, int], list[dict]]:
    """Actions taken on lesson-detect events since `since`, and the lessons that failed in use."""
    path = board.STATE_FILE.parent / 'events.jsonl'
    actions, failed = {}, []
    if not path.exists():
        return actions, failed
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('kind') != 'false_cannot' or event.get('timestamp', 0) < since:
            continue
        actions[event['action']] = actions.get(event['action'], 0) + 1
        if 'failed in use' in event['action']:
            failed.append(event)
    return actions, failed


def advisor_usage(now: float, state: dict) -> str:
    """Advisor API calls and tokens over the last 7 days, from daily snapshots of its running totals."""
    db = database('advisor')
    if db is None:
        return 'Advisor: no transcript yet'
    try:
        calls, tokens = db.execute('select coalesce(sum(api_call_count), 0), coalesce(sum(input_tokens + '
                                   'output_tokens + cache_read_tokens + cache_write_tokens), 0) '
                                   'from session_model_usage').fetchone()
        turns = [ts for ts in fleet_metrics.turn_starts(db) if ts >= now - 7 * 86400]
    finally:
        db.close()
    today = dt.date.fromtimestamp(now)
    state[f'advtokens#{today.isoformat()}'] = [calls, tokens]
    older = sorted((key, value) for key, value in state.items()
                   if key.startswith('advtokens#') and key[10:] <= (today - dt.timedelta(days=7)).isoformat())
    for key in [key for key, _ in older[:-1]]:
        del state[key]
    if older:
        then, (old_calls, old_tokens) = older[-1][0][10:], older[-1][1]
        usage = f'{calls - old_calls} calls, {tokens - old_tokens:,} tokens since {then}'
    else:
        first = min(key for key in state if key.startswith('advtokens#'))[10:]
        usage = f'{calls} calls, {tokens:,} tokens in all (snapshots since {first})'
    return f'Advisor: {usage}; {len(turns)} escalations and other non-watchdog turns in 7 days'


def supervision() -> list[str]:
    ledger = board.STATE_FILE.parent / 'supervision.jsonl'
    out = board.run(sys.executable, str(SUPERVISION), 'status', '--ledger', str(ledger))
    return out.splitlines() if out else ['supervision: no checks recorded']


LONG_PR_ROUNDS, LONG_PR_DAYS = 5, 7
WITH_ADVISOR_OR_OWNER = {'waits-for-final-review', 'waits-for-eye-review', 'ready-to-merge'}


def open_prs() -> list[dict]:
    raw = board.run(board.tool('gh'), 'pr', 'list', '-R', board.GITHUB_REPO, '--state', 'open', '--limit', '200',
                    '--json', 'number,createdAt,url,title,labels')
    return json.loads(raw or '[]')


def pr_labels(number: int) -> list[tuple[str, str]]:
    """(when, label) for every label put on the PR, oldest first."""
    events = board._paged_json_lines(f'repos/{board.GITHUB_REPO}/issues/{number}/timeline?per_page=100',
                                     '.[] | select(.event == "labeled") | {at: .created_at, label: .label.name} | @json')
    return sorted((event['at'], event['label']) for event in events)


def advisor_view(number: int) -> str:
    """URL of the newest `# Advisor` comment on the PR, or ''."""
    comments = board._paged_json_lines(f'repos/{board.GITHUB_REPO}/issues/{number}/comments?per_page=100',
                                       '.[] | select((.body // "") | startswith("# Advisor")) | '
                                       '{at: .created_at, url: .html_url} | @json')
    return max(comments, key=lambda c: c['at'])['url'] if comments else ''


def long_prs(now: float, state: dict) -> tuple[list[dict], list[str]]:
    """(PRs for the Advisor's batch, second-trigger lines for the owner), design.md #47.

    Trigger: LONG_PR_ROUNDS review requests since the PR last reached final review, or LONG_PR_DAYS days, both
    counted from the PR's opening or its last trigger, whichever is later.
    """
    first, second = [], []
    for pr in open_prs():
        number = pr['number']
        if {label['name'] for label in pr.get('labels') or []} & WITH_ADVISOR_OR_OWNER:
            continue
        record = state.get(f'longpr#{number}') or {'since': board._stamp(pr['createdAt']), 'triggers': 0}
        since = max(record['since'], board._stamp(pr['createdAt']))
        labels = [(board._stamp(at), name) for at, name in pr_labels(number) if board._stamp(at) >= since]
        finals = [at for at, name in labels if name == 'waits-for-final-review']
        rounds = sum(1 for at, name in labels if name == 'waits-for-review' and at > max(finals, default=0))
        days = (now - since) / 86400
        if rounds < LONG_PR_ROUNDS and days < LONG_PR_DAYS:
            continue
        why = f'{rounds} review rounds' if rounds >= LONG_PR_ROUNDS else f'{days:.0f} days'
        if record['triggers'] == 0:
            first.append({**pr, 'why': why})
        else:
            view = advisor_view(number) or 'no Advisor comment found'
            second.append(f'PR #{number} {pr["title"]} hit the long-PR trigger again ({why} since the Advisor\'s '
                          f'look); the Advisor\'s view: {view} - {pr["url"]}')
        state[f'longpr#{number}'] = {'since': now, 'triggers': record['triggers'] + 1}
    return first, second


def batch_message(day: str, drafts: list[Path], failed: list[dict], fired: list[str], active: bool,
                  facts: Path, notes: Path, long: list[dict] = ()) -> str:
    parts = [f'Watchdog: daily batch for {day}. Every path below is absolute.']
    if drafts:
        parts.append('Draft lessons to review (accept, rewrite and accept, merge, or reject):\n'
                     + '\n'.join(f'- {path}' for path in drafts))
    if failed:
        parts.append('Lessons that failed in use since the last digest (re-check each):\n' + '\n'.join(
            f'- {e["action"].split("lesson ", 1)[-1].split(" ", 1)[0]}: {e["profile"]} wrote "{e["text"][:120]}"'
            for e in failed))
    if fired:
        parts.append('Trend trigger fired; find the cause and act on it:\n' + '\n'.join(f'- {line}' for line in fired))
    if long:
        parts.append('Long PRs (#47). For each, name the cause from the PR history (spec not settled, scope grew, '
                     'Worker stuck, Reviewer moving goalposts), act on it, and post one history comment on the PR, '
                     'signed `# Advisor`:\n' + '\n'.join(f'- #{p["number"]} {p["title"]} ({p["why"]}) {p["url"]}'
                                                          for p in long))
    if active:
        parts.append('Reviewer or Manager worked since yesterday: run the daily-batch audits (Reviewer\'s Issues to '
                     'Fix, Manager\'s explanatory answers) and record each check in the supervision ledger.')
    parts.append(f'The facts digest is {facts}. When you are done, write your notes for the owner with write_file to '
                 f'{notes}: one line per lesson accepted, rejected or retired, per SOUL edit, and per audit '
                 f'disagreement, or "No changes." The watchdog sends the digest with your notes.')
    return '\n\n'.join(parts)


def owner_mention() -> str:
    sys.path.insert(0, str(board.HERMES_ROOT / 'bot-tools' / 'discord'))
    try:
        import ping_owner
        return ping_owner.OWNER
    except Exception:  # noqa: BLE001 - the digest still goes out, unmentioned
        return ''


def send(text: str) -> bool:
    return board.send_text(f'{owner_mention()} {text}'.strip(), DIGEST_PROFILE, 'discord')


def guard_refusals(since: float) -> str:
    """Workspace-guard refusals since `since`, per tool, from the guard's own log."""
    path = board.STATE_FILE.parent / 'guard.jsonl'
    counts: dict[str, int] = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get('at', 0) >= since:
                counts[entry.get('profile', '?')] = counts.get(entry.get('profile', '?'), 0) + 1
    return 'Workspace guard refusals: ' + (', '.join(f'{p} {n}' for p, n in sorted(counts.items())) or 'none')


RETIRE_DAYS = 60


def unused_tools() -> str:
    """Toolbox scripts no bot named in a tool call for RETIRE_DAYS: the Advisor's to retire (#40)."""
    skills = lesson_detect.ROOT / 'skills'
    toolbox = [p for p in skills.glob('fleet-*') if p.name not in HERMES_RUN]
    rows = fleet_metrics.tool_uses(board.HERMES_ROOT, list(lesson_detect.PROFILES), toolbox, RETIRE_DAYS)
    unused = sorted(Path(path).relative_to(skills).as_posix() for count, _, path in rows
                    if count == 0 and retirable(Path(path)))
    return f'Unused for {RETIRE_DAYS} days (retire to retired/): ' + (', '.join(unused) or 'none')


HERMES_RUN = {'fleet-hooks', 'fleet-workspace'}  # hook scripts Hermes runs itself; no bot ever names them


def retirable(path: Path) -> bool:
    """A command-line tool in a skill's scripts/ that has been in git for RETIRE_DAYS (a newer one has no history)."""
    if path.parent.name != 'scripts' or path.suffix not in ('.py', '.sh', '.ps1', '.cs'):
        return False
    if path.suffix == '.py' and '__main__' not in path.read_text(encoding='utf-8', errors='replace'):
        return False  # a library other tools import
    added = board.run(board.tool('git'), 'log', '--diff-filter=A', '--format=%ct', '--', path.name, cwd=path.parent)
    first = min((float(t) for t in added.split()), default=time.time())
    return time.time() - first >= RETIRE_DAYS * 86400


def tool_use(since: float) -> str:
    """fleet_run runs since `since`, most-used first, with how many each stopped and why (#40)."""
    path = board.STATE_FILE.parent / 'runs.jsonl'
    runs: dict[str, list[str]] = {}
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get('at', 0) >= since:
                runs.setdefault(entry.get('tool') or '?', []).append(entry.get('reason') or '?')
    parts = []
    for tool, reasons in sorted(runs.items(), key=lambda item: -len(item[1])):
        stops = sorted({r for r in reasons if r != 'finished'})
        detail = ', '.join(f'{reasons.count(r)} {r}' for r in stops)
        parts.append(f'{tool} {len(reasons)}' + (f' ({detail})' if detail else ''))
    return 'Tool runs (fleet_run): ' + (', '.join(parts[:12]) or 'none')


def digest(now: float, state: dict) -> None:
    """Called by `daily`: build the facts, then send them or hand them to the Advisor's batch."""
    since = float(state.get('digest#last') or now - 86400)
    day = dt.date.fromtimestamp(now).isoformat()
    counts, fired, active = trends(now)
    drafts, changed = lesson_files(since)
    actions, failed = lesson_events(since)
    long, again = long_prs(now, state)
    lines = [f'Fleet digest {day}', '', 'Counts, last 7 live days against the 14 before (watchdog wakes are not turns):',
             *counts, '', 'Trend trigger: ' + ('; '.join(fired) if fired else 'quiet'), '',
             f'Lessons: {len(drafts)} draft(s) waiting' + (f' ({", ".join(p.stem for p in drafts)})' if drafts else ''),
             *changed,
             'Lesson checks: ' + (', '.join(f'{n} {action}' for action, n in sorted(actions.items())) or 'none'),
             '', 'Long PRs: ' + (', '.join(f'#{p["number"]} ({p["why"]}) sent to the Advisor' for p in long) or 'none new'),
             *again, guard_refusals(since), tool_use(since), unused_tools(), '', *supervision(), advisor_usage(now, state),
             'Not counted here yet: per-PR figures (#21).']
    text = '\n'.join(lines)
    data = board.STATE_FILE.parent
    facts, notes, pending = (data / f'digest-{day}.md', data / f'digest-{day}-advisor.md',
                             data / f'digest-{day}.pending.json')
    state['digest#last'] = now
    if board.DRY_RUN:
        print(text)
        return
    data.mkdir(parents=True, exist_ok=True)
    facts.write_text(text + '\n', encoding='utf-8')
    if not (drafts or failed or fired or active or long):
        send(text)
        board.log(f'digest {day} sent, no Advisor batch needed')
        return
    pending.write_text(json.dumps({'facts': str(facts), 'notes': str(notes), 'woken': now}), encoding='utf-8')
    board.wake('advisor', batch_message(day, drafts, failed, fired, active, facts, notes, long))
    board.log(f'digest {day}: Advisor woken for its batch')


def send_pending(now: float) -> None:
    """Called by `board-audit`: send a digest whose Advisor notes have arrived, or whose wait ran out."""
    for pending in sorted(board.STATE_FILE.parent.glob('digest-*.pending.json')):
        record = json.loads(pending.read_text(encoding='utf-8'))
        facts, notes = Path(record['facts']), Path(record['notes'])
        if notes.exists():
            tail = 'Advisor:\n' + notes.read_text(encoding='utf-8').strip()
        elif now - record['woken'] >= NOTES_HOURS * 3600:
            tail = f'Advisor batch did not finish within {NOTES_HOURS} h; these are the facts alone.'
        else:
            continue
        if board.DRY_RUN:
            board.log(f'would send {facts.name}')
            continue
        send(facts.read_text(encoding='utf-8').strip() + '\n\n' + tail)
        pending.unlink()
        board.log(f'digest sent: {facts.name}')
