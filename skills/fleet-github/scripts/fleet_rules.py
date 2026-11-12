"""The fleet's GitHub posting rules as pure checks, shared by review.py, comment.py and label.py.

Each function returns a list of problems; an empty list means the text may be posted. Every message names
the format it expects, so a bot can fix its post from the refusal alone.
"""
from __future__ import annotations

import re

SIGNERS = ('Advisor', 'Manager', 'Reviewer', 'Watchdog', *(f'Worker-{n}' for n in range(1, 6)))
SIGNATURE = re.compile(r'^# (' + '|'.join(SIGNERS) + r')\s*$')
PRIVACY = re.compile(r'(^|[^A-Za-z])[A-Za-z]:[\\/]|AppData|Users[\\/]')
GROUNDS = re.compile(r'\((criterion|rule|breakage):\s*[^)]+\)\s*$')
OLD_HEADINGS = re.compile(r'^#{2,}\s*(blocking|should[- ]fix|nits?)\b', re.I | re.M)
SPEC_HEADING = re.compile(r'^#{2,}\s*spec questions?\b', re.I | re.M)
ACK = re.compile(r'^\W*(ack|noted|thanks|thank you|got it|acknowledged|understood|on it|will do)\b', re.I)
DETAILS = re.compile(r'<details>.*?</details>', re.I | re.S)
SELF_CHECK_LINES = ('Failure', 'Own cause ruled out', 'Tried', 'Claim')
MAX_CHARS = 2000  # measured: refuses the longest 20% of 3,170 real bot posts; 800 refused 70%
PLAN_GATE_SINCE = '2026-11-08'  # PRs opened earlier keep the evidence gate but skip the work-plan gate

SELF_CHECK_FORMAT = ('Failure: <exact command> -> <output>\nOwn cause ruled out: <what you changed since it last '
                     'worked, and why that is not it>\nTried: <session search result>; <lesson search result>; '
                     '<the other route and its result>\nClaim: <what is broken, where, shown by what>')


def _section(text: str, heading: str) -> str:
    match = re.search(rf'^#{{2,3}}\s*{heading}\s*$\n(.*?)(?=^#{{2,3}}\s|\Z)', text, re.I | re.M | re.S)
    return match.group(1) if match else ''


def _items(section: str) -> list[str]:
    return [line.strip() for line in section.splitlines() if re.match(r'\s*- ', line)]


def review_problems(body: str) -> list[str]:
    problems = []
    if OLD_HEADINGS.search(body):
        problems.append('Blocking / Should-fix / Nit headings are retired: put every item under `### Issues to Fix`')
    if SPEC_HEADING.search(body):
        problems.append('spec questions do not go in a review: send each one to the Advisor, one line each')
    for item in _items(_section(body, 'Issues to Fix')):
        if not GROUNDS.search(item):
            problems.append(f'no grounds on: {item[:90]} — end it with (criterion: "<quote>"), (rule: <file or '
                            f'rule>) or (breakage: <evidence>); with none of these it is a spec question')
    return problems


def has_open_issues(body: str) -> bool:
    return any(item.startswith('- [ ]') for item in _items(_section(body, 'Issues to Fix')))


def review_verdict(body: str) -> str:
    """'fixes', 'clean', or '' when the body has no `Issues to Fix` section to read a verdict from."""
    if not re.search(r'^#{2,3}\s*Issues to Fix\s*$', body, re.I | re.M):
        return ''
    return 'fixes' if has_open_issues(body) else 'clean'


def self_check_problems(text: str) -> list[str]:
    problems = []
    for name in SELF_CHECK_LINES:
        match = re.search(rf'^\W*{name}:\s*(\S.*)$', text, re.M)
        if not match:
            problems.append(f'self-check line missing: `{name}:`')
        elif name == 'Tried':
            tried = match.group(1).lower()
            if 'session' not in tried:
                problems.append('`Tried:` must quote your session search for the failing command')
            if 'lesson' not in tried:
                problems.append('`Tried:` must quote the lesson search result (even "no lesson matches")')
    if problems:
        problems.append('self-check format:\n' + SELF_CHECK_FORMAT)
    return problems


def comment_problems(body: str, signer: str, allow_paths: bool = False) -> list[str]:
    lines = body.splitlines()
    first = lines[0].strip() if lines else ''
    if not SIGNATURE.match(first):
        return [f'the first line must be the signer, one of: {", ".join("# " + s for s in SIGNERS)}']
    problems = [] if first == signer.strip() else [f'first line is {first!r}, expected {signer!r}']
    rest = '\n'.join(lines[1:])
    opener = next((line for line in rest.splitlines() if line.strip()), '')
    if ACK.match(opener):
        problems.append('no acknowledgements on GitHub: a PR comment is history (a decision, its reason, or '
                        'what went wrong). Tell the bot by DM instead')
    visible = DETAILS.sub('', rest).strip()
    if len(visible) > MAX_CHARS:
        problems.append(f'{len(visible)} characters outside <details>; the cap is {MAX_CHARS}. Lead with the '
                        f'point, move evidence into <details><summary>Evidence</summary> … </details>')
    if not allow_paths:
        hits = [f'line {n}: {line.strip()}' for n, line in enumerate(lines, 1)
                if PRIVACY.search(line) and 'privacy-ok:' not in line]
        if hits:
            problems.append('local paths in the body:\n  ' + '\n  '.join(hits))
    return problems


def _filled(text: str, name: str) -> bool:
    """A `## Name` section or a `Name:` line with real content; a template's `<...>` placeholder is not content."""
    content = _section(text, name) + '\n' + '\n'.join(re.findall(rf'^\W*{name}:\s*(.*)$', text, re.M))
    content = re.sub(r'<[^>\n]*>|<!--.*?-->', '', content, flags=re.S)
    return bool(re.search(r'[^\W\d_]', content))  # a letter: a bare `1.` list marker is not content


def criteria(issue_body: str) -> list[str]:
    return _items(_section(issue_body, 'Acceptance criteria'))


def _approved(comments: list[str], phrase: str, signers: tuple[str, ...], owner_counts: bool) -> bool:
    for comment in comments:
        text = comment.strip()
        first = text.splitlines()[0].strip() if text else ''
        if SIGNATURE.match(first):
            if first[2:].strip() in signers and phrase.lower() in text.lower():
                return True
        elif owner_counts and phrase.lower() in text.lower():
            return True  # an unsigned comment is the owner's own
    return False


def ready_problems(pr_body: str, issue_body: str, is_bug: bool, comments: list[str]) -> list[str]:
    """Before `waits-for-review`: one evidence line per acceptance criterion; on a bug, the cause, the
    reproduction and the approach approval (the Advisor's or the owner's)."""
    problems = []
    wanted, given = len(criteria(issue_body)), len(_items(_section(pr_body, 'Evidence')))
    if given < wanted:
        problems.append(f'the PR body\'s `## Evidence` has {given} line(s) for {wanted} acceptance criteria: one '
                        f'`- <criterion>: <command> -> <result>` line each')
    if is_bug:
        for name in ('Cause', 'Reproduction'):
            if not any(_filled(text, name) for text in (issue_body, pr_body)):
                problems.append(f'bug: the issue needs its `## {name}` section filled in (confirmed with unity-diagnose)')
        if not _approved(comments, 'approach approved', ('Advisor',), owner_counts=True):
            problems.append('bug PR: no "Approach approved" comment from the Advisor (or the owner) yet')
    return problems


def linked_pr_problems(linked_prs: list[int]) -> list[str]:
    """An issue may wait for review only through a PR that closes it; the gate runs on that PR."""
    if linked_prs:
        return []
    return ['no PR closes this issue: put `closes #<issue>` in the PR body, then label the PR or the issue']


def start_problems(pr_body: str, comments: list[str], created_at: str | None = None) -> list[str]:
    """Before the first `in-progress`: a work plan in the draft PR body and the Reviewer's plan approval."""
    if created_at and created_at[:10] < PLAN_GATE_SINCE:
        return []
    problems = []
    if not _section(pr_body, 'Work plan').strip():
        problems.append('the draft PR body needs a `## Work plan`: the phase-plan step it serves, the approach, '
                        'what it touches, and the evidence per criterion')
    if not _approved(comments, 'plan approved', ('Reviewer', 'Advisor'), owner_counts=True):
        problems.append('no "Plan approved" comment from Reviewer yet (review.py --approve-plan)')
    return problems
