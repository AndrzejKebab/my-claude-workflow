"""Fleet watchdog checks, run as the `board-audit` and `daily` cron jobs. Design: docs/hermes-fleet/design.md #43-44."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import datetime
from pathlib import Path

import comment_signing

FLEET_GITHUB = Path(__file__).resolve().parents[3] / 'skills' / 'fleet-github' / 'scripts'
LABEL_PY = FLEET_GITHUB / 'label.py'
sys.path.insert(0, str(FLEET_GITHUB))
import fleet_rules  # noqa: E402

# Set by configure() from the Specific config; see configure().
REPO = Path()
GITHUB_REPO = ''
HERMES_ROOT = Path()
HERMES_EXE = Path()
DM_RUNNER = Path()
STATE_FILE = Path()
LOG_FILE = Path()
WORKTREE_PATTERN = ''
KEPT_BRANCHES: set[str] = set()
ALERT_PROFILE = ''
ALERT_CHANNEL = ''
DEADLINE = float('inf')
CONFIG_PATH = '.agents/fleet-watchdog.json'

WATCHDOG_MINUTES = 15
STALL_MINUTES = 30
REVIEW_NUDGE_MINUTES = 15
REVIEW_NUDGE_REPEAT_MINUTES = 0
FINAL_NUDGE_MINUTES = 30
STALE_LABEL_MINUTES = 30
PARKED_MINUTES = 120
IN_REVIEW_MINUTES = 30
STALE_LABEL_REPEAT_MINUTES = 0
MAX_WAKES = 2
DRY_RUN = '--dry-run' in sys.argv


def log(message: str) -> None:
    if DRY_RUN:
        print(f'[dry-run] {message}', file=sys.stderr)
        return
    stamp = time.strftime('%Y-%m-%d %H:%M:%S')
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open('a', encoding='utf-8') as handle:
        handle.write(f'{stamp} {message}\n')


class OverBudget(Exception):
    """The job ran past its time budget; remaining checks are skipped, not hung."""


def run(*args: str, cwd: Path | None = None, timeout: float = 120) -> str:
    remaining = DEADLINE - time.time()
    if remaining <= 0:
        raise OverBudget(f'{args[0]} {args[1] if len(args) > 1 else ""}')
    timeout = min(timeout, remaining)
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8',
                                errors='replace', check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        log(f'timed out after {timeout}s: {args[0]} {args[1] if len(args) > 1 else ""}')
        return ''
    return result.stdout.strip() if result.returncode == 0 else ''


def tool(name: str) -> str:
    return shutil.which(name) or name


def in_progress_items() -> list[dict]:
    items = []
    for kind in ('issue', 'pr'):
        fields = 'number,title,labels,url' + (',headRefName' if kind == 'pr' else '')
        raw = run(tool('gh'), kind, 'list', '-R', GITHUB_REPO, '--state', 'open', '--label', 'in-progress',
                  '--json', fields, '--limit', '100')
        for entry in json.loads(raw or '[]'):
            labels = [label['name'] for label in entry['labels']]
            workers = [name.split(':', 1)[1] for name in labels if name.startswith('worker:')]
            if not workers:
                continue
            items.append({'kind': kind, 'number': entry['number'], 'title': entry['title'], 'url': entry['url'],
                          'worker': workers[0], 'branch': entry.get('headRefName')})
    return items


def worktrees() -> dict[str, Path]:
    found, path = {}, None
    for line in run(tool('git'), 'worktree', 'list', '--porcelain', cwd=REPO).splitlines():
        if line.startswith('worktree '):
            path = Path(line[len('worktree '):])
        elif line.startswith('branch refs/heads/') and path is not None:
            found[line[len('branch refs/heads/'):]] = path
    return found


def push_time(branch: str) -> float:
    value = run(tool('git'), 'log', '-1', '--format=%ct', f'origin/{branch}', cwd=REPO)
    return float(value) if value else 0.0


def worktree_time(path: Path) -> float:
    newest = 0.0
    head = run(tool('git'), 'log', '-1', '--format=%ct', cwd=path)
    if head:
        newest = float(head)
    for line in run(tool('git'), 'status', '--porcelain', '--untracked-files=normal', cwd=path).splitlines()[:300]:
        name = line[3:].strip().strip('"')
        if ' -> ' in name:
            name = name.split(' -> ', 1)[1]
        try:
            newest = max(newest, (path / name).stat().st_mtime)
        except OSError:
            pass
    return newest


def session_time(profile: str) -> float:
    database = HERMES_ROOT / 'profiles' / profile / 'state.db'
    if not database.exists():
        return 0.0
    try:
        connection = sqlite3.connect(f'file:{database.as_posix()}?mode=ro', uri=True, timeout=5)
        row = connection.execute('select max(timestamp) from messages').fetchone()
        connection.close()
        return float(row[0] or 0.0)
    except sqlite3.Error:
        return 0.0


def turn_running(profile: str) -> bool:
    """Whether a *turn* is running, not merely whether the bot's backend is alive.

    A desktop Bot Chat keeps a live backend process for the whole session and records it with
    `surface: "desktop"`. Counting that as a running turn made every nudge for that bot be skipped
    forever, so an idle Reviewer looked permanently busy and never got told about a PR (2026-10-17).
    Only CLI wake turns (`surface: "cli"`) mean someone is actually working.
    """
    leases = HERMES_ROOT / 'profiles' / profile / 'runtime' / 'active_sessions.json'
    try:
        entries = json.loads(leases.read_text(encoding='utf-8')).get('entries', [])
    except (OSError, ValueError):
        return False
    return any(entry.get('surface') != 'desktop'
               and process_alive(entry.get('pid'), entry.get('process_start_time'))
               for entry in entries)


def process_alive(pid, started) -> bool:
    """Stdlib-only liveness check (the cron interpreter has no psutil). Guards against PID reuse by
    comparing the process creation time with the lease's recorded start time."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if os.name != 'nt':
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    try:
        code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value != 259:  # STILL_ACTIVE
            return False
        if started is None:
            return True
        creation, exit_, kernel, user = (wintypes.FILETIME() for _ in range(4))
        if not kernel32.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_),
                                        ctypes.byref(kernel), ctypes.byref(user)):
            return True
        ticks = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        created = ticks / 10_000_000 - 11_644_473_600  # FILETIME epoch 1601 -> Unix
        return abs(created - float(started)) < 5
    finally:
        kernel32.CloseHandle(handle)


def hermes_python() -> str:
    """Hermes' bundled interpreter, the one message_agent's delivery runner uses."""
    candidates = sorted((HERMES_ROOT / 'tools').glob('python-3*/python.exe'), reverse=True)
    return str(candidates[0]) if candidates else sys.executable


def dm_text(text: str) -> str:
    """Every line the watchdog sends is signed `Watchdog:`.

    The bot posts as the owner's GitHub account and its DMs land as the same user, so a message with
    no prefix reads as something the owner wrote to himself (2026-10-19).
    """
    stripped = text.lstrip()
    return stripped if stripped.startswith('Watchdog:') else f'Watchdog: {stripped}'


def wake(profile: str, text: str) -> bool:
    text = dm_text(text)
    handle, dm_file = tempfile.mkstemp(prefix='watchdog-', suffix='.txt')
    with os.fdopen(handle, 'w', encoding='utf-8') as stream:
        stream.write(text)
    command = [hermes_python(), str(DM_RUNNER), '--run-delivery',
               '--author', json.dumps({'id': 'bot:watchdog', 'name': 'watchdog', 'is_bot': True}),
               'query-file', dm_file,
               str(HERMES_EXE), '-p', profile, 'chat', '--in', '~', '-c', 'Bot Chat', '--create-if-missing', '-Q']
    if DRY_RUN:
        os.unlink(dm_file)
        return True
    # Fire and forget: the runner owns the turn, the file cleanup and the reply.
    # CREATE_NO_WINDOW only: DETACHED_PROCESS would make each console child open its own visible window.
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0)
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=flags, close_fds=True)
    return True


def owner_replies() -> list[dict]:
    """Open items waiting on the owner where an UNSIGNED comment arrived after the last signed one.

    Bots sign every comment with `# Manager` / `# Reviewer` / `# Worker N` as its first line, and
    every bot posts through the owner's GitHub account, so an unsigned comment on a waiting item is
    the owner's own reply. Nothing else polls GitHub for it, which is how answers used to sit unseen.
    """
    items = []
    for label in ('needs-owner', 'waits-for-final-review', 'waits-for-eye-review', 'blocked'):
        raw = run(tool('gh'), 'issue', 'list', '-R', GITHUB_REPO, '--state', 'open', '--label', label,
                  '--json', 'number,title,url,labels', '--limit', '100')
        for entry in json.loads(raw or '[]'):
            if entry['number'] in {item['number'] for item in items}:
                continue
            items.append({'number': entry['number'], 'title': entry['title'], 'url': entry['url'],
                          'labels': [label['name'] for label in entry['labels']]})
    for entry in json.loads(run(tool('gh'), 'pr', 'list', '-R', GITHUB_REPO, '--state', 'open',
                                '--label', 'waits-for-final-review', '--json', 'number,title,url,labels',
                                '--limit', '100') or '[]'):
        if entry['number'] not in {item['number'] for item in items}:
            items.append({'number': entry['number'], 'title': entry['title'], 'url': entry['url'],
                          'labels': [label['name'] for label in entry['labels']]})

    waiting = []
    for item in items:
        raw = run(tool('gh'), 'api', f'repos/{GITHUB_REPO}/issues/{item["number"]}/comments?per_page=100')
        comments = json.loads(raw or '[]')[-30:]
        signed = [index for index, comment in enumerate(comments)
                  if (comment.get('body') or '').lstrip().startswith('#')]
        # Only an unsigned comment NEWER than the newest signed one is an unanswered owner reply.
        after = comments[(max(signed) + 1) if signed else 0:]
        unsigned_after = [comment for comment in after if not (comment.get('body') or '').lstrip().startswith('#')]
        if not unsigned_after:
            continue
        newest = unsigned_after[-1]
        item['comment_id'] = newest.get('id')
        item['comment_url'] = newest.get('html_url')
        item['body'] = (newest.get('body') or '')[:300]
        waiting.append(item)
    return waiting


def responsible(profile_labels: list[str], labels: list[str]) -> str:
    for label in labels:
        if label.startswith('worker:'):
            return f'worker-{label.split(":", 1)[1]}'
    if {'waits-for-final-review', 'waits-for-eye-review'} & set(labels):
        return 'advisor'
    return 'manager'


_FETCH_CACHE: dict[tuple[int, str], object] = {}


def fetched(number: int, kind: str, loader):
    """One GitHub read per item per run, whatever asks for it."""
    key = (number, kind)
    if key not in _FETCH_CACHE:
        _FETCH_CACHE[key] = loader()
    return _FETCH_CACHE[key]


def _paged_json_lines(path: str, jq: str) -> list[dict]:
    """Every page of a GitHub list endpoint; `jq` must emit one `@json` line per element."""
    found = []
    for line in run(tool('gh'), 'api', path, '--paginate', '-q', jq).splitlines():
        line = line.strip()
        if line.startswith('{'):
            try:
                found.append(json.loads(line))
            except ValueError:
                continue
    return found


def labelled_items(label: str) -> list[dict]:
    """Open issues and PRs carrying one label: when the label was last applied, and the comments since.

    Waiting time is measured from the label event, not from comments: the label is what says the
    item is waiting, and a comment-based clock read old comments as new on long threads.
    """
    items = []
    for command in (('issue', 'list'), ('pr', 'list')):
        raw = run(tool('gh'), *command, '-R', GITHUB_REPO, '--state', 'open', '--label', label,
                  '--json', 'number,title,url,updatedAt,labels', '--limit', '100')
        for entry in json.loads(raw or '[]'):
            if any(item['number'] == entry['number'] for item in items):
                continue
            number = entry['number']
            events = fetched(number, 'timeline', lambda: _paged_json_lines(
                f'repos/{GITHUB_REPO}/issues/{number}/timeline?per_page=100',
                '.[] | select(.event == "labeled" or .event == "cross-referenced") | '
                '{event: .event, at: .created_at, label: (.label.name // ""), '
                'is_pr: ((.source.issue.pull_request // null) != null)} | @json'))
            entry['labelled_at'] = max((event['at'] for event in events
                                        if event['event'] == 'labeled' and event['label'] == label),
                                       default='') or entry['updatedAt']
            # A cross-reference with a pull request is how an issue knows its PR exists.
            entry['has_pr'] = any(event['is_pr'] for event in events)
            comments = fetched(number, 'comments', lambda: _paged_json_lines(
                f'repos/{GITHUB_REPO}/issues/{number}/comments?per_page=100',
                '.[] | {at: .created_at, head: ((.body // "") | ltrimstr(" ") | .[0:20]), '
                'url: .html_url, body: ((.body // "") | .[0:4000])} | @json'))
            after = [comment for comment in comments if comment['at'] >= entry['labelled_at']]
            entry['reviewer_answered'] = any(c['head'].startswith('# Reviewer') for c in after)
            entry['reviewer_at'] = max((c['at'] for c in after if c['head'].startswith('# Reviewer')), default='')
            # `worker` is read below, so resolve the author prefix after the labels are parsed.
            entry['comments_after'] = after
            entry['is_pr'] = '/pull/' in (entry.get('url') or '')
            entry['kind'] = 'PR' if entry['is_pr'] else 'Issue'
            entry['review_submitted_at'] = ''
            entry['review_last_state'] = ''
            entry['review_last_url'] = ''
            entry['review_blocking'] = False
            blocking_any = False
            entry['reviewer_last_at'] = ''
            entry['reviewer_last_url'] = ''
            entry['reviewer_last_kind'] = ''
            entry['waiting_reason'] = ''
            entry['wait_declared_at'] = ''
            entry['wait_until'] = 0.0
            reviews = []
            if entry['is_pr']:
                # `gh pr review` writes to pulls/N/reviews, not to issue comments. A COMMENTED,
                # APPROVED or CHANGES_REQUESTED review is the Reviewer having answered.
                reviews = fetched(number, 'reviews', lambda: _paged_json_lines(
                    f'repos/{GITHUB_REPO}/pulls/{number}/reviews?per_page=100',
                    '.[] | select(.submitted_at != null) | {at: .submitted_at, state: .state, '
                    'url: .html_url, body: (.body // "")} | @json'))
                entry['review_submitted_at'] = max(
                    (review['at'] for review in reviews if review['at'] >= entry['labelled_at']),
                    default='')
                entry['review_states'] = sorted({review['state'] for review in reviews})
                newest_review = max(((review['at'], review) for review in reviews if review['at']),
                                    default=('', {}))[1]
                entry['review_last_state'] = newest_review.get('state', '')
                entry['review_last_url'] = newest_review.get('url', '')
                entry['review_last_at'] = newest_review.get('at', '')
                entry['review_last_body'] = newest_review.get('body') or ''
                body = (newest_review.get('body') or '').lower()
                # An unchecked box under a Blocking heading is an open finding, whatever the state says.
                entry['review_blocking'] = 'blocking' in body and '- [ ]' in body
                if not entry['review_blocking']:
                    entry['review_blocking'] = blocking_any
                if entry['review_submitted_at']:
                    entry['reviewer_answered'] = True
                    entry['reviewer_at'] = max(entry['reviewer_at'], entry['review_submitted_at'])
            entry['labels'] = [label_entry['name'] for label_entry in entry.get('labels') or []]
            entry['worker'] = next((name.split(':', 1)[1] for name in entry['labels']
                                    if name.startswith('worker:')), '')
            # Only the item's author counts as movement: a Manager comment on a Worker's PR is a
            # conversation, not work, and counting it made a silent Worker look active.
            author_head = f'# Worker-{entry["worker"]}' if entry['worker'] else '# Manager'
            # What the Reviewer last put on this item, comment or review. Across the whole thread: the
            # newest finding often predates the current label (a re-labelled PR keeps its reviews).
            reviewer_items = [(c['at'], c['url'], 'comment') for c in comments
                              if c['head'].startswith('# Reviewer')]
            reviewer_items += [(r['at'], r.get('url', ''), 'review') for r in reviews]
            newest = max(reviewer_items, default=('', '', ''), key=lambda item: item[0])
            blocking_any = any('blocking' in ((r.get('body') or '').lower()) and '- [ ]' in (r.get('body') or '')
                               for r in reviews)
            entry['reviewer_last_at'], entry['reviewer_last_url'] = newest[0], newest[1]
            entry['reviewer_last_kind'] = newest[2]

            # A declared wait: `Waiting: <reason>` in a comment from Manager or the Reviewer, optionally
            # `until HH:MM` (local). Nobody is stalled while that holds.
            entry['waiting_reason'], entry['wait_until'] = '', 0.0
            entry['waiting_on'], entry['waiting_on_open'] = [], False
            for comment in comments:
                # Any bot may declare a wait: the author waiting on a dependency is the common case.
                if not re.match(r'# (Manager|Reviewer|Worker-[0-9]+)', comment['head']):
                    continue
                for line in (comment.get('body') or '').splitlines():
                    if not line.strip().lower().startswith('waiting:'):
                        continue
                    entry['waiting_reason'] = line.strip()
                    entry['wait_declared_at'] = comment['at']
                    clock = re.search(r'until\s+(\d{1,2}):(\d{2})', line, re.I)
                    if clock:
                        moment = datetime.datetime.now().replace(
                            hour=int(clock.group(1)), minute=int(clock.group(2)), second=0, microsecond=0)
                        if moment.timestamp() < _stamp(comment['at']):
                            moment += datetime.timedelta(days=1)
                        entry['wait_until'] = moment.timestamp()

            # References in the declaration: `#164` open means the task is held by a dependency.
            reason_text = entry['waiting_reason'] or ''
            if not reason_text:
                for comment in comments:
                    body = (comment.get('body') or '')
                    if 'blocked' in body.lower() and re.search(r'#\d+', body):
                        reason_text = body
                reason_text = reason_text[:1500]
            numbers = {int(found) for found in re.findall(r'#(\d{1,5})', reason_text)}
            numbers.discard(entry['number'])
            entry['waiting_on'] = sorted(numbers)
            entry['waiting_on_open'] = any(issue_state(number) == 'OPEN' for number in numbers)

            entry['author_at'] = max((c['at'] for c in entry['comments_after']
                                      if c['head'].startswith(author_head)), default='')
            entry['other_at'] = max((c['at'] for c in entry['comments_after']
                                     if not c['head'].startswith(author_head)
                                     and not c['head'].startswith('# Reviewer')), default='')
            entry['head_committed_at'] = ''
            if entry['is_pr']:
                head = run(tool('gh'), 'api', f'repos/{GITHUB_REPO}/pulls/{number}',
                           '-q', '.head.sha').strip()
                if head:
                    entry['head_committed_at'] = run(
                        tool('gh'), 'api', f'repos/{GITHUB_REPO}/commits/{head}',
                        '-q', '.commit.committer.date').strip()
            entry['last_activity_at'] = max([entry['reviewer_at'], entry['author_at'],
                                             entry['head_committed_at'], ''])
            items.append(entry)
    return items


_STATE_CACHE: dict[int, str] = {}


def issue_state(number: int) -> str:
    """OPEN or CLOSED for an issue or PR, cached for the run so a dependency costs one query."""
    if number not in _STATE_CACHE:
        state = run(tool('gh'), 'api', f'repos/{GITHUB_REPO}/issues/{number}',
                    '-q', '.state').strip().upper()
        _STATE_CACHE[number] = state or 'UNKNOWN'
    return _STATE_CACHE[number]


SPRAWL = re.compile(r'(?:[-_]?b|[0-9])\.(?:py|cs|sh|ps1|js|ts)$', re.I)
SPRAWL_GRACE_MINUTES = 15


def scratch_dirs(profile: str) -> list[Path]:
    dirs = [HERMES_ROOT / 'profiles' / profile / 'cache' / 'scratch']
    if profile.startswith('worker-'):
        dirs.append((REPO / WORKTREE_PATTERN.format(n=profile.split('-')[-1])).resolve() / '.scratch')
    return [directory for directory in dirs if directory.is_dir()]


def numbered_copies(now: float, state: dict) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]], list[str]]:
    """`foo2.py` next to `foo.py`, or `foo-b.py` next to `foo.py`: one tool written twice.

    Pair-based on purpose: a name that merely ends in a digit (`neut3116.py`) is not a copy. A file
    younger than the grace period may still be a variant being folded in, so it is left alone.
    """
    wakes, reports, seen = [], [], []
    # The main profile's home is the Hermes root, so its scratch is `cache/scratch`. It is checked, but
    # only reported: the owner has no bot to wake.
    main_scratch = HERMES_ROOT / 'cache' / 'scratch'
    if main_scratch.is_dir():
        names = {path.name for path in main_scratch.iterdir() if path.is_file()}
        for name in sorted(names):
            match = re.match(r'^(?P<stem>.+?)(?P<suffix>(?:[-_]?b|[2-9]))'
                             r'(?P<ext>\.(?:py|cs|sh|ps1|psm1|js|ts|tsx))$', name, re.I)
            if not match or f'{match.group("stem")}{match.group("ext")}' not in names:
                continue
            key = f'sprawl#main#{name}'
            seen.append(key)
            if state.get(f'{key}#reported'):
                continue
            state[f'{key}#reported'] = now
            reports.append((f'{key}#report', f'main profile: {name} duplicates '
                                             f'{match.group("stem")}{match.group("ext")}'))

    for profile in ('advisor', 'reviewer', 'manager') + tuple(f'worker-{n}' for n in range(1, 6)):
        for directory in scratch_dirs(profile):
            names = {path.name for path in directory.iterdir() if path.is_file()}
            for name in sorted(names):
                match = re.match(r'^(?P<stem>.+?)(?P<suffix>(?:[-_]?b|[2-9]))(?P<ext>\.(?:py|cs|sh|ps1|psm1|js|ts|tsx))$', name, re.I)
                if not match:
                    continue
                stem, ext = match.group('stem'), match.group('ext')
                base = f'{stem}{ext}'
                if base not in names:
                    continue  # no original here: not a copy of anything in this directory
                path = directory / name
                if (now - path.stat().st_mtime) / 60 < SPRAWL_GRACE_MINUTES:
                    continue
                key = f'sprawl#{profile}#{name}'
                seen.append(key)
                if state.get(f'{key}#reported'):
                    continue
                state[f'{key}#reported'] = now
                reports.append((f'{key}#report', f'{profile}: {name} duplicates {base}'))
                wakes.append((f'{key}#dm', profile, (
                    f'Watchdog: `{name}` sits next to `{base}` in `{directory}` — the same tool twice. Decide '
                    f'what the copy does that the base cannot, fold it in as a flag, give the result a name '
                    f'that describes the job, then delete the copy. A tool this project needs goes to '
                    f'`bot-tools/<area>/` with a README line; one built for another project goes to '
                    f'`bot-tools/external/<project>/` and is not presented as project tooling.')))
    return wakes, reports, seen


LOCAL_REVIEW_COPY_HOURS = 6


def kept_branches() -> set[str]:
    """Branches the owner has asked to keep, whatever the PR says."""
    return KEPT_BRANCHES


def dead_branches(now: float, state: dict) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]], list[str]]:
    """Branches that outlived their purpose: a merged/closed PR's branch on origin, a branch with no PR
    at all, a `pr<N>` review copy pushed to origin, and a local `pr<N>` left in the main clone.

    A branch is a claim that work is in flight. Everything here is a branch that makes that claim and
    nothing else, which is why the owner's branch list grew to 25 entries.
    """
    wakes, reports, seen = [], [], []
    kept = kept_branches()
    try:
        prs = json.loads(run(tool('gh'), 'pr', 'list', '--state', 'all', '--json',
                             'headRefName,state,number', '-R', GITHUB_REPO, '--limit', '300') or '[]')
    except (OSError, ValueError):
        prs = []
    by_branch = {entry['headRefName']: entry for entry in prs}

    try:
        dated = run(tool('git'), 'for-each-ref', 'refs/remotes/origin',
                    '--format=%(refname:short)|%(committerdate:unix)', cwd=REPO)
    except Exception:  # noqa: BLE001 - a missing date only costs the quiet check
        dated = ''
    touched = {}
    for line in dated.splitlines():
        parts = line.split('|')
        if len(parts) == 2 and parts[1].strip():
            touched[parts[0].removeprefix('origin/')] = float(parts[1])

    heads = run(tool('git'), 'ls-remote', '--heads', 'origin', cwd=REPO)
    for line in heads.splitlines():
        if 'refs/heads/' not in line:
            continue
        name = line.split('refs/heads/')[-1].strip()
        if name == 'main' or name in kept:
            continue
        if name.startswith('pr') and name[2:].isdigit():
            reason = 'a review copy pushed to origin; review branches are local to the main clone'
            who = 'reviewer'
        else:
            entry = by_branch.get(name)
            if entry and entry['state'] == 'MERGED':
                reason = f'PR #{entry["number"]} merged and the branch is still on origin'
                who = 'reviewer'
            elif entry and entry['state'] == 'CLOSED':
                reason = f'PR #{entry["number"]} was closed unmerged and the branch is still on origin'
                who = 'manager'
            elif not entry:
                if now - touched.get(name, now) < 6 * 3600:
                    continue  # touched within the last six hours: a base branch being built on
                reason = 'no pull request points at it'
                who = 'manager'
            else:
                continue  # an open PR: the branch is doing its job
        key = f'deadbranch#{name}'
        seen.append(key)
        if state.get(f'{key}#reported'):
            continue
        state[f'{key}#reported'] = now
        reports.append((f'{key}#report', f'remote branch {name}: {reason}'))
        wakes.append((f'{key}#dm', who, (
            f'Watchdog: `origin/{name}` is a dead branch — {reason}. Delete it '
            f'(`git push origin --delete {name}`) and, if a local copy is left, `git branch -D {name}`. '
            f'Never push a `pr<N>` branch at all: it is your local view of a PR head.')))

    current = run(tool('git'), 'branch', '--show-current', cwd=REPO).strip()
    listing = run(tool('git'), 'branch', '--list', 'pr*', '--format=%(refname:short) %(committerdate:unix)',
                  cwd=REPO)
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) != 2 or parts[0] == current:
            continue
        name, stamp = parts[0], float(parts[1])
        if now - stamp < LOCAL_REVIEW_COPY_HOURS * 3600:
            continue
        key = f'deadbranch#local#{name}'
        seen.append(key)
        if state.get(f'{key}#reported'):
            continue
        state[f'{key}#reported'] = now
        hours = (now - stamp) / 3600
        reports.append((f'{key}#report', f'local review copy {name} is {hours:.0f}h old'))
        wakes.append((f'{key}#dm', 'reviewer', (
            f'Watchdog: `{name}` is a review copy left in the main clone {hours:.0f}h after its review. '
            f'Delete it (`git branch -D {name}`) now, and delete it at the end of every review: the PR head '
            f'is on GitHub, the local copy is only a view.')))
    return wakes, reports, seen


def local_branches(now: float, state: dict) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]], list[str]]:
    """Dead branches in the owner's clone, and the clone being checked out on something other than main.

    Origin was the only thing watched, so a merged PR's branch survived on disk forever and the owner's
    clone sat on the Reviewer's `pr317` review copy — the file on screen was not what `main` holds.
    """
    wakes, reports, seen = [], [], []
    kept = kept_branches()
    try:
        prs = json.loads(run(tool('gh'), 'pr', 'list', '--state', 'all', '--json',
                             'headRefName,state,number,labels', '-R', GITHUB_REPO, '--limit', '300') or '[]')
    except (OSError, ValueError):
        prs = []
    by_branch = {entry['headRefName']: entry for entry in prs}

    # The clone is the owner's. A checkout of his — a review he started — looks exactly like a review
    # copy somebody forgot, and there is no way to tell them apart from the repository alone. So this
    # reports and never switches: only the owner moves his own checkout (#branch-cleanup).
    current = run(tool('git'), 'branch', '--show-current', cwd=REPO).strip()

    checked_out = set()
    listing = run(tool('git'), 'worktree', 'list', '--porcelain', cwd=REPO)
    for line in listing.splitlines():
        if line.startswith('branch refs/heads/'):
            checked_out.add(line.split('branch refs/heads/')[-1].strip())

    refs = run(tool('git'), 'for-each-ref', 'refs/heads',
               '--format=%(refname:short)|%(upstream:track)|%(committerdate:unix)', cwd=REPO)
    for line in refs.splitlines():
        parts = line.split('|')
        if len(parts) != 3:
            continue
        name, track, stamp = parts[0], parts[1], parts[2]
        if name == 'main' or name in checked_out or name in kept:
            continue
        if name.startswith('pr') and name[2:].isdigit():
            continue  # the six-hour rule below owns review copies
        entry = by_branch.get(name)
        merged = bool(entry) and entry['state'] in ('MERGED', 'CLOSED')
        orphan = not entry and not track.strip() and (now - float(stamp)) > 24 * 3600
        if not merged and '[gone]' not in track and not orphan:
            continue
        key = f'localbranch#{name}'
        seen.append(key)
        if state.get(f'{key}#reported'):
            continue
        state[f'{key}#reported'] = now
        if orphan:
            ahead = run(tool('git'), 'rev-list', '--count', name, '--not', 'origin/main', cwd=REPO).strip()
            label = f'no PR, no upstream, {ahead} commits not in main'
        elif entry:
            label = f'PR #{entry["number"]} {entry["state"].lower()}'
        else:
            label = 'its upstream is gone'
        reports.append((f'{key}#report', f'local branch {name} is dead: {label}'))
        owner = 'manager'
        if entry:
            for label_entry in entry.get('labels', []):
                match = re.match(r'worker:(\d)', label_entry.get('name', ''))
                if match:
                    owner = f'worker-{match.group(1)}'
        wakes.append((f'{key}#dm', owner, (
            f'Watchdog: `{name}` is a dead local branch in the main clone ({label}). Delete it: '
            f'`git branch -D {name}`. A branch in the clone is a claim that work is in flight; merged work '
            f'is in `main`.' if not orphan else
            f'Watchdog: `{name}` in the main clone has {label} and nobody will merge it. Either open a PR for '
            f'it or delete it (`git branch -D {name}`) and tell the owner which it was.')))
    return wakes, reports, seen


def parked(item: dict, now: float) -> bool:
    """True when someone declared a wait on this item and it has not run out.

    A build slot, a lock, another bot's merge: real waits that no commit can show. The declaration
    must be newer than the last work, so a stale note cannot park an item forever, and an `until
    HH:MM` expires 15 minutes after that time so a missed slot is caught rather than trusted.
    """
    if not item.get('waiting_reason'):
        return False
    declared = _stamp(item.get('wait_declared_at') or '')
    work = _stamp(max([item.get('author_at') or '', item.get('head_committed_at') or '']))
    if declared and work and declared < work:
        return False  # the wait was declared before the work: it is stale
    # A dependency that is still open is the strongest park: `until 11:00` cannot express "until #164
    # merges", and reporting it every 15 minutes is noise on a decision already taken.
    if item.get('waiting_on_open'):
        return True
    if item.get('wait_until'):
        return now < item['wait_until'] + 15 * 60
    return now - declared < PARKED_MINUTES * 60


def signed_ago(stamp: str, minutes: float, now: float) -> bool:
    """True when an ISO timestamp is older than `minutes`."""
    try:
        when = datetime.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ').replace(
            tzinfo=datetime.timezone.utc).timestamp()
    except ValueError:
        return False
    return (now - when) / 60 >= minutes


def _digest(value: str) -> str:
    """Short, stable key for a PR state."""
    return hashlib.sha1(value.encode('utf-8')).hexdigest()[:10]


def pending_reviews(now: float) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]], list[str]]:
    """Returns (wakes, owner_pings, seen_keys).

    wakes: [(profile, message)] — a Worker has handed a PR to Reviewer and Reviewer has not answered.
    owner_pings: Discord lines — a PR is through its review rounds and is waiting on the owner,
    which needs the owner's own look at the changes in the Editor.
    """
    wakes, pings, seen = [], [], []

    seen_final = set()
    # The Advisor runs final reviews (one wake per PR state); the owner is pinged only for eye review.
    for item in labelled_items('waits-for-final-review'):
        if not item['is_pr'] or not signed_ago(item['labelled_at'], FINAL_NUDGE_MINUTES, now):
            continue
        signature = '|'.join(('final', item['labelled_at'], item.get('head_committed_at', '')))
        key = f'finalwake#{item["number"]}#{_digest(signature)}'
        seen.append(key)
        seen_final.add(item['number'])
        wakes.append((key, 'advisor', f'Watchdog: PR #{item["number"]} waits for your final review - '
                                      f'{item["url"]}'))
    waiting_on = (('waits-for-eye-review', 'your eye review'),
                  ('ready-to-merge', 'your merge approval'))
    for label, wording in waiting_on:
        for item in labelled_items(label):
            age_source = item['labelled_at']
            signature = '|'.join((label, item['labelled_at'], item.get('head_committed_at', ''),
                                  item.get('reviewer_at', ''), item.get('author_at', '')))
            key = f'finalping#{item["number"]}#{_digest(signature)}'
            if item['number'] in seen_final:
                continue
            seen_final.add(item['number'])
            if not item['is_pr']:
                continue  # a final review is a PR; a stale label on an issue is Manager's cleanup
            if not signed_ago(age_source, FINAL_NUDGE_MINUTES, now):
                continue
            seen.append(key)
            pings.append((key, f'PR #{item["number"]} has been waiting for {wording} for '
                               f'{int((now - _stamp(age_source)) / 60)} min - {item["url"]}'))

    return wakes, pings, seen


def _stamp(value: str) -> float:
    try:
        return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(
            tzinfo=datetime.timezone.utc).timestamp()
    except ValueError:
        return time.time()


def label_fixes(now: float, state: dict) -> set[int]:
    """Move a label whose next state follows from the Reviewer's newest review alone (#44).

    Only a review newer than the head commit, signed `# Reviewer`, with an `Issues to Fix` section: an
    open item means `in-progress`, none means `waits-for-final-review`. One attempt per review; returns
    the items moved, so the stray check leaves them alone this run.
    """
    moved = set()
    for label in ('waits-for-review', 'in-review', 'in-progress'):
        for item in labelled_items(label):
            body, at = item.get('review_last_body') or '', item.get('review_last_at') or ''
            pushed = item.get('head_committed_at') or ''
            if not (item['is_pr'] and at and pushed and at > pushed and body.lstrip().startswith('# Reviewer')):
                continue
            verdict = fleet_rules.review_verdict(body)
            target = {'fixes': 'in-progress', 'clean': 'waits-for-final-review'}.get(verdict)
            if not target or target == label or parked(item, now) or not signed_ago(at, WATCHDOG_MINUTES, now):
                continue
            key = f'labelfix#{item["number"]}#{_digest(at + target)}'
            if key in state:
                continue
            reason = (f'the Reviewer\'s review of {_ago(at, now)} has '
                      f'{"open Issues to Fix" if verdict == "fixes" else "no open Issues to Fix"} '
                      f'and the label did not move ({item.get("review_last_url") or "newest review"})')
            output = run(sys.executable, str(LABEL_PY), str(item['number']), '--to', target, '--signer', 'Watchdog',
                         '--reason', reason, '--repo', GITHUB_REPO, *(['--dry-run'] if DRY_RUN else []))
            state[key] = now if output else f'failed {now:.0f}'
            if output:
                moved.add(item['number'])
                log(f'label fix #{item["number"]}: {label} -> {target}')
            else:
                log(f'label fix #{item["number"]} {label} -> {target} refused by label.py; waking instead')
    return moved


def nudge_record(state: dict, key: str, profile: str) -> dict:
    """Wake count for one stray state; the single-file watchdog's `#dm#`/`#reported` keys read as one wake
    and as the owner already told."""
    name = f'{key}#nudge'
    if not isinstance(state.get(name), dict):
        told = state.get(f'{key}#dm#{profile}')
        told = told if isinstance(told, (int, float)) else 0.0
        state[name] = {'wakes': 1 if told else 0, 'last_wake': float(told),
                       'alerted': bool(state.get(f'{key}#reported'))}
    return state[name]


def stray_labels(now: float, skip: set[int] = frozenset()) -> tuple[list[tuple[str, str, str, str]], list[str]]:
    """Returns (strays, seen_keys) for labels that no longer describe reality.

    A stray is (state key, profile holding the next step, owner line, message to that profile). The label
    map in each bot's SOUL says who must act next, so a label sitting wrong is somebody having stopped
    without moving it. `waits-for-final-review` and `ready-to-merge` are left to the owner ping.
    """
    strays, seen = [], []

    def stray(key: str, line: str, profile: str, message: str) -> None:
        strays.append((key, profile, line, message))

    # `waits-for-review` — queued for Reviewer. Nobody has started reviewing.
    for item in labelled_items('waits-for-review'):
        key = f'stray#waits-for-review#{item["number"]}#{item["labelled_at"]}'
        seen.append(key)
        if not signed_ago(item['labelled_at'], STALE_LABEL_MINUTES, now):
            continue
        wait = _hours(int((now - _stamp(item['labelled_at'])) / 60))
        if item['reviewer_answered']:
            stray(key, f'#{item["number"]} stale label waits-for-review {wait}: Reviewer posted findings '
                       f'{_ago(item["reviewer_at"], now)} and the label never moved. It should be '
                       f'in-progress (fixes) or waits-for-final-review (clean).',
                  'reviewer',
                  f'PR #{item["number"]} {item["title"]} ({item["url"]}) is still labelled '
                  f'waits-for-review, but you posted your findings {_ago(item["reviewer_at"], now)}. Set the '
                  f'label to what is actually true: in-progress if the author must fix something, '
                  f'waits-for-final-review if the review is clean.')
        # Not answered: the Reviewer queue wakes the Reviewer and tells the owner.

    # `in-review` — the Reviewer has it open. This is minutes of work, so hours mean it was abandoned.
    for item in labelled_items('in-review'):
        key = f'stray#in-review#{item["number"]}#{item["labelled_at"]}'
        seen.append(key)
        if not signed_ago(item['labelled_at'], IN_REVIEW_MINUTES, now):
            continue
        wait = _hours(int((now - _stamp(item['labelled_at'])) / 60))
        if item['reviewer_answered']:
            stray(key, f'#{item["number"]} stale label in-review {wait}: the review ended '
                       f'{_ago(item["reviewer_at"], now)} but the label still says you are reviewing it. '
                       f'It should be in-progress (fixes) or waits-for-final-review (clean).',
                  'reviewer',
                  f'PR #{item["number"]} {item["title"]} ({item["url"]}): you reviewed it and left findings '
                  f'{_ago(item["reviewer_at"], now)}, but it is still labelled in-review. The label says you '
                  f'are still reading it. Set in-progress (the author fixes) or waits-for-final-review now.')
        # Not answered: the Reviewer queue wakes the Reviewer and tells the owner.

    # `in-progress` — the author is working. A long silence means they stopped without saying so.
    for item in labelled_items('in-progress'):
        key = f'stray#in-progress#{item["number"]}#{item["labelled_at"]}'
        seen.append(key)
        wait = _hours(int((now - _stamp(item['labelled_at'])) / 60))
        author = f'worker-{item["worker"]}' if item['worker'] else 'manager'
        if not signed_ago(item['labelled_at'], STALE_LABEL_MINUTES, now):
            continue  # inside the grace period: a fresh task has no PR yet by design
        if not item['is_pr']:
            if item['has_pr']:
                # Its work is on a PR, and that PR's own label says where it stands.
                continue
            # No PR at all: the issue has been claimed and nothing is visible.
            stray(key, f'#{item["number"]} (Issue, {author}) in-progress {wait} with no PR opened.',
                  author,
                  f'Issue #{item["number"]} {item["title"]} ({item["url"]}) has been in-progress for '
                  f'{wait} and no PR references it, so your work is invisible and nobody can review '
                  f'progress. Now: branch off origin/main, commit the first thing you touch (a failing '
                  f'test, the file skeleton), push it, and open the draft PR with `gh pr create --draft '
                  f'--label worker:{item["worker"] or "N"} --label in-progress`. Then carry on.')
            continue
        if not signed_ago(item['labelled_at'], STALE_LABEL_MINUTES, now):
            continue
        if parked(item, now):
            continue  # a declared wait (build slot, lock) is not a stall
        activity = max([item['author_at'], item['head_committed_at'], ''])
        # The ball turns on the last *code* the Reviewer reviewed, not on the last message: an author
        # status comment ("nothing is pending") must not make it look like the author's turn (#249).
        pushed = item['head_committed_at'] or item['author_at']
        approved_last = item.get('review_last_state') == 'APPROVED'
        if item['is_pr'] and approved_last and item['reviewer_at'] and item['reviewer_at'] > pushed:
            # The Reviewer acted last: it owes the next step (usually the label move) and the author
            # has nothing left to do. Telling the author "fix the label" was wrong on #249.
            state_word = {'APPROVED': 'approved', 'CHANGES_REQUESTED': 'requested changes',
                          'COMMENTED': 'reviewed'}.get(item.get('review_last_state'), 'reviewed')
            wait = _hours(int((now - _stamp(item['labelled_at'])) / 60))
            stray(key, f'#{item["number"]} ({item["kind"]}, worker:{item["worker"] or "?"}) in-progress '
                       f'{wait}: the Reviewer {state_word} it {_ago(item["reviewer_at"], now)} and the '
                       f'label never moved. The Reviewer holds the next step.',
                  'reviewer',
                  f'PR #{item["number"]} {item["title"]} ({item["url"]}): you {state_word} it '
                  f'{_ago(item["reviewer_at"], now)} and it is still labelled in-progress. Set the label '
                  f'to what your review decided — waits-for-final-review if it is clean, in-progress stays '
                  f'only if the author still has work — and DM the author. Nothing else is pending on it.')
            continue
        if activity and not signed_ago(activity, STALE_LABEL_MINUTES, now):
            continue  # work is landing; the label is honest
        since = (f'the author last pushed or commented {_ago(activity, now)}'
                 if activity else 'the author has pushed and said nothing since the label went on')
        if item.get('reviewer_last_url'):
            findings = ('and its newest open finding is below it — read it before calling this done'
                        if item.get('review_blocking') else 'read it before calling this done')
            since += (f'; the Reviewer\'s newest output is the {item.get("reviewer_last_kind") or "comment"} '
                      f'at {item["reviewer_last_url"]} — {findings}')
        if item['other_at'] and item['other_at'] > activity:
            since += f' (someone else commented {_ago(item["other_at"], now)}, which is not work)'
        stray(key, f'#{item["number"]} ({item["kind"]}, {author}) in-progress {wait}: {since}.',
              author,
              f'PR #{item["number"]} {item["title"]} ({item["url"]}) has been labelled in-progress for '
              f'{wait} and {since}. Push what you have and say on the PR what is left and when '
              f'you will finish, or move the label if it no longer matches. A task that stopped silently is '
              f'what this report exists for.')

    # `blocked` — the author cannot continue until someone answers. Two ways it goes wrong: the answer
    # came and the label stayed (the author now has work and looks stuck), or nobody answers.
    for item in labelled_items('blocked'):
        key = f'stray#blocked#{item["number"]}#{item["labelled_at"]}'
        seen.append(key)
        if parked(item, now):
            # Held by an open dependency: the decision is taken and there is nobody to chase.
            continue
        author = f'worker-{item["worker"]}' if item['worker'] else 'manager'
        answer = max([item['other_at'], item['reviewer_at'], ''])
        wait = _hours(int((now - _stamp(item['labelled_at'])) / 60))
        if answer and not signed_ago(answer, WATCHDOG_MINUTES, now):
            continue  # an answer just landed; give the author one run to act on it
        if answer:
            stray(key, f'#{item["number"]} ({item["kind"]}, {author}) still blocked {wait} after it was '
                       f'answered {_ago(answer, now)}: the label should be back to in-progress.',
                  author,
                  f'{item["kind"]} #{item["number"]} {item["title"]} ({item["url"]}) is still labelled '
                  f'blocked, but it was answered {_ago(answer, now)}. Read the answer, set the label to '
                  f'in-progress with a one-line comment `Label: blocked → in-progress — <why>`, and carry on. '
                  f'If the answer does not unblock you, say exactly what is still missing on the PR.')
        elif signed_ago(item['labelled_at'], STALE_LABEL_MINUTES, now):
            stray(key, f'#{item["number"]} ({item["kind"]}, {author}) blocked {wait} and nobody has '
                       f'answered.',
                  'manager',
                  f'{item["kind"]} #{item["number"]} {item["title"]} ({item["url"]}) has been blocked for '
                  f'{wait} with no answer. Read the blocker, answer it or relay it to the owner as an '
                  f'Owner-inbox question, and set the label back to in-progress when it is answered.')

    return [entry for entry in strays if int(entry[0].split('#')[2]) not in skip], seen


def _ago(stamp: str, now: float) -> str:
    """A short human age for one timestamp."""
    return f'{_hours(int((now - _stamp(stamp)) / 60))} ago'


def _hours(minutes: int) -> str:
    return f'{minutes // 60}h{minutes % 60:02d}m' if minutes >= 60 else f'{minutes}m'


def configure(repo: Path, hermes_root: Path, data_dir: Path, job: str, config: dict) -> None:
    """Point every module global at one deployment. `config` is the Specific config file's content."""
    global REPO, GITHUB_REPO, HERMES_ROOT, HERMES_EXE, DM_RUNNER, STATE_FILE, LOG_FILE
    global WORKTREE_PATTERN, KEPT_BRANCHES, ALERT_PROFILE, ALERT_CHANNEL
    REPO, HERMES_ROOT = Path(repo), Path(hermes_root)
    GITHUB_REPO = config['github_repo']
    WORKTREE_PATTERN = config['worker_worktree']
    KEPT_BRANCHES = set(config.get('kept_branches', []))
    ALERT_PROFILE, ALERT_CHANNEL = config['alerts']['profile'], config['alerts']['channel']
    HERMES_EXE = HERMES_ROOT / 'hermes-agent' / '.hermes' / 'bin' / 'hermes.exe'
    DM_RUNNER = HERMES_ROOT / 'hermes-agent' / 'tools' / 'bot_mode_dm.py'
    STATE_FILE = Path(data_dir) / f'{job}-state.json'
    LOG_FILE = Path(data_dir) / 'watchdog.log'
    comment_signing.ROOT = HERMES_ROOT / 'profiles'
    comment_signing.REPO_SLUG = GITHUB_REPO


def read_config(repo: Path) -> dict:
    """The Specific config as committed on the repo's `main`, whatever branch the clone has checked out."""
    raw = run(tool('git'), 'show', f'main:{CONFIG_PATH}', cwd=repo)
    if not raw:
        raise SystemExit(f'no {CONFIG_PATH} on main in {repo}')
    return json.loads(raw)


# State keys each job owns; `seed_state` copies them out of the single-file watchdog's state.
DAILY_KEYS = ('deadbranch#', 'localbranch#', 'digest#', 'advtokens#')


def owns_key(job: str, key: str) -> bool:
    if job == 'daily':
        return key.startswith(DAILY_KEYS)
    return job == 'board-audit' and not key.startswith(DAILY_KEYS)


def load_state(job: str, legacy: Path | None) -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        pass
    try:
        old = json.loads(legacy.read_text(encoding='utf-8')) if legacy else {}
    except (OSError, ValueError):
        old = {}
    return {key: value for key, value in old.items() if owns_key(job, key)}


def save_state(state: dict) -> None:
    if not DRY_RUN:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=1), encoding='utf-8')


def send_alerts(lines: list[str]) -> None:
    """Owner alerts go out through the alert profile's own Discord account; the job's profile has none."""
    if lines:
        send_text('\n'.join(lines), ALERT_PROFILE, f'discord:{ALERT_CHANNEL}')


def send_text(text: str, profile: str, target: str) -> bool:
    """Send through `profile`'s own platform account; an unsent text is logged and kept in the run output."""
    if DRY_RUN:
        print(text)
        return True
    command = [str(HERMES_EXE), '-p', profile, 'send', '--to', target, '--quiet', text]
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace',
                                timeout=120)
        failed = result.returncode != 0
        detail = (result.stdout + result.stderr).strip()[-300:]
    except (OSError, subprocess.TimeoutExpired) as error:
        failed, detail = True, f'{type(error).__name__}: {error}'
    if failed:
        log(f'not sent as {profile} ({detail}): {text[:300]}')
        print(text)  # kept in the cron run output, so it is not lost
    return not failed


def daily(now: float, state: dict) -> list[str]:
    """Dead branches on origin and in the owner's clone."""
    alerts = []
    seen = set()
    for name, check in (('dead branch', dead_branches), ('local branch', local_branches)):
        try:
            wakes, reports, keys = check(now, state)
        except Exception as error:
            log(f'{name} check failed: {type(error).__name__}: {error}')
            continue
        seen.update(keys)
        for _report_key, line in reports:
            alerts.append(line)
            log(f'{name}: {line}')
        for _key, profile, message in wakes:
            if turn_running(profile):
                continue
            if DRY_RUN:
                log(f'would tell {profile} about a {name}: {message[:70]}')
                continue
            wake(profile, message)
            log(f'told {profile} about a {name}')
    state_keys = {key: value for key, value in state.items() if key in seen or key.startswith(DAILY_KEYS)}
    state.clear()
    state.update(state_keys)
    import daily_digest
    try:
        daily_digest.digest(now, state)
    except OverBudget:
        raise
    except Exception as error:
        log(f'digest failed: {type(error).__name__}: {error}')
    return alerts


def cli(job: str, repo: Path, hermes_root: Path, data_dir: Path, legacy_state: Path | None = None,
        budget_seconds: float = 600) -> int:
    """Entry point for the cron shims in `HERMES_HOME/scripts/`."""
    global DEADLINE
    DEADLINE = time.time() + budget_seconds
    configure(repo, hermes_root, data_dir, job, read_config(Path(repo)))
    now = time.time()
    state = load_state(job, legacy_state)
    _STATE_CACHE.clear()
    _FETCH_CACHE.clear()
    import lesson_detect
    jobs = {'board-audit': board_audit, 'daily': daily, 'lesson-detect': lesson_detect.lesson_detect}
    try:
        if job != 'lesson-detect':
            run(tool('git'), 'fetch', '-q', 'origin', cwd=REPO)
        alerts = jobs[job](now, state)
    except OverBudget as error:
        log(f'{job} stopped: over its {budget_seconds:.0f}s budget at {error}')
        alerts = []
    save_state(state)
    send_alerts(alerts)
    return 0


def board_audit(now: float, state: dict) -> list[str]:
    import daily_digest
    try:
        daily_digest.send_pending(now)
    except OverBudget:
        raise
    except Exception as error:
        log(f'pending digest check failed: {type(error).__name__}: {error}')
    try:
        moved = label_fixes(now, state)
    except Exception as error:
        log(f'label fix check failed: {type(error).__name__}: {error}')
        moved = set()
    trees = worktrees()
    items = in_progress_items()

    # One entry per worker. A Worker holds one issue until it merges, so wake it only for its OLDEST
    # open item; prefer the PR (it names the branch). A second item is flagged to the owner, not woken.
    by_worker: dict[str, dict] = {}
    extra: dict[str, list[int]] = {}
    for item in sorted(items, key=lambda entry: (entry['kind'] != 'pr', entry['number'])):
        if item['worker'] in by_worker:
            if item['kind'] == 'pr':
                extra.setdefault(item['worker'], []).append(item['number'])
            continue
        by_worker[item['worker']] = item

    alerts = []
    # Tell the owner once per exact combination of PRs, ever. He may have allowed it; repeating is spam.
    told = set(state.get('multijob#told') or [])
    for worker, numbers in sorted(extra.items()):
        combination = '+'.join(str(n) for n in sorted([by_worker[worker]['number'], *numbers]))
        marker = f'worker-{worker}:{combination}'
        if marker not in told:
            alerts.append(f'Worker-{worker} has more than one in-progress PR (#{by_worker[worker]["number"]} plus '
                          + ', '.join(f'#{n}' for n in sorted(numbers)) + '). Only the oldest is kept awake.')
            told.add(marker)
    state['multijob#told'] = sorted(told)
    seen = {'multijob#told'}
    parked_numbers = set()
    try:
        for label in ('in-progress', 'waits-for-review'):
            parked_numbers |= {entry['number'] for entry in labelled_items(label) if parked(entry, now)}
    except Exception as error:
        log(f'parked check failed: {type(error).__name__}: {error}')

    for worker, item in sorted(by_worker.items()):
        profile = f'worker-{worker}'
        key = f'{profile}#{item["number"]}'
        seen.add(key)
        record = state.get(key, {'wakes': 0, 'last_wake': 0.0, 'alerted': False})

        branch = item.get('branch')
        activity = session_time(profile)
        if branch:
            activity = max(activity, push_time(branch))
            if branch in trees:
                activity = max(activity, worktree_time(trees[branch]))

        quiet = (now - activity) / 60 if activity else float('inf')
        label = f'{"PR" if item["kind"] == "pr" else "issue"} #{item["number"]}'

        running = turn_running(profile)
        if item['number'] in parked_numbers:
            state[key] = {'wakes': 0, 'last_wake': 0.0, 'alerted': False}
            if DRY_RUN:
                log(f'{profile} {label}: parked on a declared wait, not woken')
            continue
        if DRY_RUN:
            log(f'{profile} {label}: quiet {quiet:.0f} min, turn running {running}, record {record}')
        if quiet < STALL_MINUTES:
            record = {'wakes': 0, 'last_wake': 0.0, 'alerted': False}
        if running or quiet < STALL_MINUTES:
            state[key] = record
            continue
        if now - record['last_wake'] < WATCHDOG_MINUTES * 60:
            state[key] = record
            continue

        if record['wakes'] < MAX_WAKES:
            text = (f'Watchdog: {label} is in-progress, no activity for {quiet:.0f} min. '
                    'Continue the work now; commit and push as you go. If you are waiting, set the label: '
                    'waits-for-review (DM Reviewer) or blocked (DM Manager).')
            wake(profile, text)
            record['wakes'] += 1
            record['last_wake'] = now
            log(f'woke {profile} for {label}, quiet {quiet:.0f} min, wake {record["wakes"]}/{MAX_WAKES}')
        elif not record['alerted']:
            hours, minutes = divmod(int(quiet), 60)
            alerts.append(f'Worker-{worker} stalled on {label} for {hours}h{minutes:02d}, '
                          f'{MAX_WAKES} wakes ignored -> {item["url"]}')
            record['alerted'] = True
            log(f'alerted owner: {profile} {label} quiet {quiet:.0f} min')
        state[key] = record

    # The Reviewer is woken like a Worker: whenever a PR is its turn and it has been quiet.
    # Its turn = `waits-for-review` with no Reviewer comment since the request, or anything `in-review`.
    try:
        queue = []
        for label in ('waits-for-review', 'in-review', 'in-progress'):
            for item in labelled_items(label):
                if label == 'in-progress':
                    pushed = item['head_committed_at'] or item['author_at']
                    if not (item['is_pr'] and item['reviewer_at'] and item['reviewer_at'] > pushed):
                        continue  # the author holds this one
                if any(entry['number'] == item['number'] for entry in queue):
                    continue
                if label == 'waits-for-review' and item['reviewer_answered']:
                    continue  # it answered (comment or review); whether the label moved is the audit's job
                item['queue_label'] = label
                item['quiet_since'] = max(item['labelled_at'], item['reviewer_at'])
                queue.append(item)
    except Exception as error:
        log(f'reviewer queue check failed: {type(error).__name__}: {error}')
        queue = []

    key = 'reviewer#queue'
    seen.add(key)
    record = state.get(key, {'wakes': 0, 'last_wake': 0.0, 'alerted': False, 'prs': []})
    numbers = sorted(item['number'] for item in queue)
    if not queue:
        record = {'wakes': 0, 'last_wake': 0.0, 'alerted': False, 'prs': []}
    else:
        if record.get('prs') != numbers:
            # A different set of PRs is a new situation: the wake count starts again.
            record = {'wakes': 0, 'last_wake': 0.0, 'alerted': False, 'prs': numbers}
        oldest = min(queue, key=lambda item: item['quiet_since'])
        quiet = (now - _stamp(oldest['quiet_since'])) / 60
        running = turn_running('reviewer')
        if DRY_RUN:
            log(f'reviewer queue {numbers}: oldest #{oldest["number"]} quiet {quiet:.0f} min, '
                f'turn running {running}, record {record}')
        if (not running and quiet >= REVIEW_NUDGE_MINUTES
                and now - record['last_wake'] >= WATCHDOG_MINUTES * 60 - 60):
            listing = '; '.join(f'#{item["number"]} {item["queue_label"]} {item["url"]}' for item in
                                sorted(queue, key=lambda item: item['quiet_since']))
            if record['wakes'] < MAX_WAKES:
                text = (f'Watchdog: {len(queue)} PR(s) are your turn and you have been quiet for '
                        f'{quiet:.0f} min: {listing}. Start with #{oldest["number"]}: set in-review, '
                        f'review the head SHA, post findings, then set in-progress (fixes needed) or '
                        f'waits-for-final-review (clean) and DM the author. Then the next one.')
                wake('reviewer', text)
                record['wakes'] += 1
                record['last_wake'] = now
                log(f'woke reviewer for {numbers}, oldest #{oldest["number"]} quiet {quiet:.0f} min, '
                    f'wake {record["wakes"]}/{MAX_WAKES}')
            elif not record['alerted']:
                hours, minutes = divmod(int(quiet), 60)
                alerts.append(f'Reviewer stalled for {hours}h{minutes:02d} with {listing}; '
                              f'{MAX_WAKES} wakes ignored.')
                record['alerted'] = True
                log(f'alerted owner: reviewer quiet {quiet:.0f} min on {numbers}')
    state[key] = record

    for item in owner_replies():
        key = f'ownerreply#{item["comment_id"]}'
        if state.get(key):
            continue
        profile = responsible([], item['labels'])
        kind = 'PR' if 'waits-for-final-review' in item['labels'] else 'item'
        text = (f'Owner replied on {kind} #{item["number"]} ({item["comment_url"]}):\n\n'
                f'{item["body"]}\n\n'
                'Record it on the item the way the Owner-inbox rules say (owner chose X, date, via GitHub), '
                'then update the labels: remove needs-owner/blocked once answered, or move the item on. '
                'Never re-ask a question the owner has already answered.')
        if DRY_RUN:
            log(f'would wake {profile} about owner reply on #{item["number"]}: {item["body"][:80]!r}')
        else:
            wake(profile, text)
            state[key] = now
            log(f'woke {profile}: owner replied on #{item["number"]}')
        seen.add(key)

    # Review flow: nudge Reviewer on an unanswered request, and ping the owner when a PR is
    # waiting on his own final look at the changes.
    try:
        review_wakes, owner_pings, review_keys = pending_reviews(now)
    except Exception as error:
        log(f'pending review check failed: {type(error).__name__}: {error}')
    else:
        for key, profile, message in review_wakes:
            last = state.get(f'{key}#nudged') or 0
            if last and (profile == 'advisor' or (now - last) / 60 < REVIEW_NUDGE_REPEAT_MINUTES):
                continue  # the Advisor costs the owner's plan limit: one wake per PR state
            if DRY_RUN:
                log(f'would nudge {profile}: {message[:80]}')
                continue
            state[f'{key}#nudged'] = now
            wake(profile, message)
            log(f'nudged {profile} about a waiting review')
        # One ping per PR state. A push, a comment, a review or a label move makes a new state and
        # earns one new ping; the same state never pings twice, however long it sits there.
        for key, line in owner_pings:
            if state.get(f'{key}#sent'):
                continue
            if DRY_RUN:
                log(f'would ping owner: {line[:100]}')
                continue
            state[f'{key}#sent'] = now
            alerts.append(line)
            log(f'owner ping: {line[:100]}')

    # Stray labels: a label is a claim about who must act next, and these two ways of it being wrong
    # are what leaves a PR sitting for hours with nobody moving.
    try:
        strays, stray_keys = stray_labels(now, skip=moved)
    except Exception as error:
        log(f'stray label check failed: {type(error).__name__}: {error}')
    else:
        for key in stray_keys:
            state.setdefault(key, now)
        for key, profile, line, message in strays:
            number = key.split('#')[2]
            record = nudge_record(state, key, profile)
            if record['alerted'] or (record['wakes'] and now - record['last_wake'] < STALE_LABEL_MINUTES * 60):
                continue
            if record['wakes'] >= MAX_WAKES:
                alerts.append(f'{line} {profile} was told {MAX_WAKES} times and did not act.')
                record['alerted'] = True
                log(f'stray label, owner told: {line[:120]}')
                continue
            if turn_running(profile):
                record['skips'] = record.get('skips', 0) + 1
                log(f'{profile} is mid-turn; will tell it about {number} next run (skipped {record["skips"]}x)')
                if record['skips'] == 4:
                    alerts.append(f'{profile} has been mid-turn for an hour and #{number} '
                                  f'is still waiting for it. It cannot be nudged, so it needs you.')
                    record['alerted'] = True
                continue
            record['wakes'] += 1
            record['last_wake'] = now
            if DRY_RUN:
                log(f'would tell {profile}: {message[:90]}')
                continue
            wake(profile, message)
            log(f'told {profile} about stray label {number} ({record["wakes"]}/{MAX_WAKES})')

    # Numbered copies in a scratch directory: the tool rule, enforced.
    try:
        sprawl_wakes, sprawl_reports, sprawl_keys = numbered_copies(now, state)
    except Exception as error:
        log(f'scratch sprawl check failed: {type(error).__name__}: {error}')
    else:
        for key in sprawl_keys:
            seen.add(key)
        for report_key, line in sprawl_reports:
            alerts.append(line)
            log(f'scratch sprawl: {line}')
        for key, profile, message in sprawl_wakes:
            if turn_running(profile):
                continue
            if DRY_RUN:
                log(f'would tell {profile} about a numbered copy: {message[:70]}')
                continue
            wake(profile, message)
            log(f'told {profile} about a numbered copy')

    # Repair unsigned bot comments: an unsigned comment is unattributable to the owner reading it.
    # Re-scan a small overlap each run; comments already signed are skipped, so repeats are cheap.
    watermark = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now - 21600))
    if not state.get('signing_watermark'):
        watermark = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now - 30 * 86400))
    try:
        signed_lines, watermark = comment_signing.repair(watermark, apply=not DRY_RUN)
    except Exception as error:  # never let this break the stall checks
        log(f'signing repair failed: {type(error).__name__}: {error}')
    else:
        state['signing_watermark'] = watermark
        for line in signed_lines:
            log(line)

    kept = ('ownerreply#', 'finalping#', 'finalwake#', 'labelfix#', 'waitreview#', 'stray#', 'sprawl#', 'multijob#')
    state_keys = {key: value for key, value in state.items()
                  if key in seen or key == 'signing_watermark' or key.startswith(kept)}
    state.clear()
    state.update(state_keys)
    return alerts
