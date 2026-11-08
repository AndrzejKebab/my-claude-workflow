"""Signing repair for the watchdog: prepend `# <Signer>` to any unsigned bot comment.

Bots post through the owner's GitHub account, so an unsigned comment is unattributable to the
owner reading it. We can attribute it exactly: `gh` prints back the comment URL containing the id
to whoever posted it, so the id is in that bot's own transcript. An id found in no transcript is
the owner's own comment and is left alone.
"""
from __future__ import annotations

import datetime
import json
import sqlite3
import subprocess
from pathlib import Path

# Set by board.configure() from the Specific config.
ROOT = Path()
REPO_SLUG = ''
TITLE = {'advisor': 'Advisor', 'manager': 'Manager', 'reviewer': 'Reviewer'}


def _signer(profile: str) -> str:
    if profile.startswith('worker-'):
        return f'Worker-{profile.split("-", 1)[1]}'
    return TITLE.get(profile, profile)


def _gh(*args: str) -> str:
    try:
        result = subprocess.run(['gh', *args], capture_output=True, text=True, encoding='utf-8',
                                errors='replace', check=False, timeout=120)
    except subprocess.TimeoutExpired:
        return ''
    return result.stdout.strip() if result.returncode == 0 else ''


def unsigned_since(watermark: str) -> list[dict]:
    """Every comment updated since the watermark, repo-wide, that has no signature line.

    Paginated: `gh --jq` runs per page, so each match is emitted as one JSON line.
    """
    raw = _gh('api', f'repos/{REPO_SLUG}/issues/comments?since={watermark}&per_page=100', '--paginate',
              '-q', '.[] | select(.body | startswith("#") | not) | '
                    '{id, body, url: .html_url, created: .created_at, updated: .updated_at} | @json')
    found = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith('{'):
            try:
                found.append(json.loads(line))
            except ValueError:
                continue
    return found


def find_author(comment_id: str, pull_number_from_url: str = '') -> tuple[str, str]:
    """The profile whose transcript carries this comment id, plus the session id."""
    needle = str(comment_id)
    for profile in sorted(path.name for path in ROOT.iterdir() if (path / 'state.db').exists()):
        database = ROOT / profile / 'state.db'
        try:
            connection = sqlite3.connect(f'file:{database.as_posix()}?mode=ro', uri=True, timeout=5)
            row = connection.execute(
                'select session_id from messages where content like ? or tool_calls like ? limit 1',
                (f'%{needle}%', f'%{needle}%')).fetchone()
            connection.close()
        except sqlite3.Error:
            continue
        if row:
            return profile, row[0]
    return '', ''


def sign(comment_id: str, signer: str) -> bool:
    body = _gh('api', f'repos/{REPO_SLUG}/issues/comments/{comment_id}', '-q', '.body')
    if not body or body.lstrip().startswith('#'):
        return False
    return bool(_gh('api', '-X', 'PATCH', f'repos/{REPO_SLUG}/issues/comments/{comment_id}',
                    '-f', f'body=# {signer}\n\n{body}'))


def repair(watermark: str, *, apply: bool) -> tuple[list[str], str]:
    """Returns (report lines, new watermark)."""
    lines, newest = [], watermark
    for comment in unsigned_since(watermark):
        newest = max(newest, comment.get('updated') or comment.get('created') or watermark)
        profile, session = find_author(comment['id'])
        if not profile:
            continue  # the owner's own comment: leave unsigned
        signer = _signer(profile)
        if not apply:
            lines.append(f'would sign {comment["id"]} as {signer} ({profile}/{session[-6:]})')
            continue
        if sign(comment['id'], signer):
            lines.append(f'signed {comment["id"]} as {signer}')
    return lines, newest
