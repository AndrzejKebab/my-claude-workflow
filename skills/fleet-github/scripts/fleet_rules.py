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
CANNOT = re.compile(r"\b(I|I'm|I am|we)\s+(cannot|can't|can not|could not|couldn't|am unable to|was unable to|"
                    r"have no way to|am not able to)\b", re.I)
DETAILS = re.compile(r'<details>.*?</details>', re.I | re.S)
SELF_CHECK_LINES = ('Failure', 'Own cause ruled out', 'Tried', 'Claim')
MAX_CHARS = 800

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
        problems.append('spec questions do not go in a review: send each one to the Advisor (the owner until '
                        'the Advisor exists), one line each')
    for item in _items(_section(body, 'Issues to Fix')):
        if not GROUNDS.search(item):
            problems.append(f'no grounds on: {item[:90]} — end it with (criterion: "<quote>"), (rule: <file or '
                            f'rule>) or (breakage: <evidence>); with none of these it is a spec question')
    return problems


def has_open_issues(body: str) -> bool:
    return any(item.startswith('- [ ]') for item in _items(_section(body, 'Issues to Fix')))


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
    if CANNOT.search(visible):
        problems += self_check_problems(rest)
    if not allow_paths:
        hits = [f'line {n}: {line.strip()}' for n, line in enumerate(lines, 1)
                if PRIVACY.search(line) and 'privacy-ok:' not in line]
        if hits:
            problems.append('local paths in the body:\n  ' + '\n  '.join(hits))
    return problems


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
    reproduction and the approach approval (the Advisor's, or the owner's until the Advisor exists)."""
    problems = []
    wanted, given = len(criteria(issue_body)), len(_items(_section(pr_body, 'Evidence')))
    if given < wanted:
        problems.append(f'the PR body\'s `## Evidence` has {given} line(s) for {wanted} acceptance criteria: one '
                        f'`- <criterion>: <command> -> <result>` line each')
    if is_bug:
        for line in ('Cause', 'Reproduction'):
            if not re.search(rf'^\W*{line}:\s*\S', pr_body, re.M):
                problems.append(f'bug PR: the body needs a `{line}:` line (confirmed with unity-diagnose)')
        if not _approved(comments, 'approach approved', ('Advisor',), owner_counts=True):
            problems.append('bug PR: no "Approach approved" comment from the Advisor (or the owner) yet')
    return problems


def start_problems(pr_body: str, comments: list[str]) -> list[str]:
    """Before the first `in-progress`: a work plan in the draft PR body and the Reviewer's plan approval."""
    problems = []
    if not _section(pr_body, 'Work plan').strip():
        problems.append('the draft PR body needs a `## Work plan`: the phase-plan step it serves, the approach, '
                        'what it touches, and the evidence per criterion')
    if not _approved(comments, 'plan approved', ('Reviewer', 'Advisor'), owner_counts=True):
        problems.append('no "Plan approved" comment from Reviewer yet (review.py --approve-plan)')
    return problems
