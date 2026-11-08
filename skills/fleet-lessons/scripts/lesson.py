#!/usr/bin/env python3
"""Draft, accept, retire, index and search lessons in one or more lesson homes.

    lesson.py add --home <dir> [--domain hermes] --slug <s> --title <t> --symptom <one line>
                  --evidence <command and result> --body <what to do>
    lesson.py search --home <dir> [--home <dir> ...] "<symptom words>"
    lesson.py accept --home <dir> <slug> --sha <commit> [--skill <SKILL.md>]
    lesson.py retire --home <dir> <slug> --reason <why> [--skill <SKILL.md>]
    lesson.py index  --home <dir> [--skill <SKILL.md>]
    lesson.py check  --home <dir>

A home holds lessons as `<slug>.md` or `<domain>/<slug>.md`, plus INDEX.md, drafts/ and retired/.
Drafts are invisible to search. `accept` and `retire` are the Advisor's (the owner's until it exists).
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

NOT_LESSONS = {'INDEX.md', 'README.md', 'SKILL.md'}
SKIP_DIRS = {'drafts', 'retired'}
START, END = '<!-- lessons-index:start -->', '<!-- lessons-index:end -->'


def lessons(home: Path) -> list[Path]:
    found = []
    for path in sorted(home.rglob('*.md')):
        rel = path.relative_to(home)
        if path.name not in NOT_LESSONS and not (set(rel.parts[:-1]) & SKIP_DIRS):
            found.append(path)
    return found


def title_of(text: str) -> str:
    return next((line[2:].strip() for line in text.splitlines() if line.startswith('# ')), '')


def symptom_of(text: str) -> str:
    """The `Symptom:` line, else the first paragraph of a `## Symptom` section, else the title."""
    if match := re.search(r'^Symptom:\s*(.+)$', text, re.M):
        return match.group(1).strip()
    if match := re.search(r'^## Symptom\s*\n+(.+?)(\n\s*\n|\n## |\Z)', text, re.M | re.S):
        sentence = re.split(r'(?<=[.!?])\s', ' '.join(match.group(1).split()), maxsplit=1)[0]
        return sentence if len(sentence) <= 200 else sentence[:200].rsplit(' ', 1)[0] + ' …'
    return title_of(text)


def index_lines(home: Path) -> list[str]:
    lines = []
    for path in lessons(home):
        text = path.read_text(encoding='utf-8')
        lines.append(f'- {symptom_of(text)} → [{title_of(text)}]({path.relative_to(home).as_posix()})')
    return lines


def write_index(home: Path, skill: Path | None) -> None:
    lines = index_lines(home)
    body = '\n'.join(lines) if lines else '_No lessons yet._'
    (home / 'INDEX.md').write_text(f'# Lessons\n\nSymptom → lesson. Search with `lesson.py search`.\n\n{body}\n',
                                   encoding='utf-8')
    if skill:
        text = skill.read_text(encoding='utf-8')
        if START not in text or END not in text:
            sys.exit(f'{skill} has no {START} … {END} markers')
        head, rest = text.split(START, 1)
        _, tail = rest.split(END, 1)
        skill.write_text(f'{head}{START}\n{body}\n{END}{tail}', encoding='utf-8')


def find(home: Path, slug: str, where: str = 'lessons') -> Path | None:
    if where == 'drafts':
        path = home / 'drafts' / f'{slug}.md'
        return path if path.exists() else None
    return next((p for p in lessons(home) if p.stem == slug), None)


def search(homes: list[Path], query: str, limit: int) -> list[tuple[int, Path, str]]:
    words = {w for w in re.findall(r'[a-z0-9_]+', query.lower()) if len(w) >= 3}
    hits = []
    for home in homes:
        for path in lessons(home):
            text = path.read_text(encoding='utf-8')
            head = (title_of(text) + ' ' + symptom_of(text)).lower()
            score = sum(2 * head.count(w) + text.lower().count(w) for w in words)
            if score:
                hits.append((score, path, symptom_of(text)))
    return sorted(hits, key=lambda h: -h[0])[:limit]


def cmd_add(a) -> int:
    home = Path(a.home)
    if not a.evidence.strip():
        print('refused: a lesson needs evidence (the command and its real result)', file=sys.stderr)
        return 2
    if find(home, a.slug) or find(home, a.slug, 'drafts'):
        print(f'refused: {a.slug} already exists; extend that lesson instead', file=sys.stderr)
        return 2
    related = search([home], f'{a.title} {a.symptom}', 3)
    draft = home / 'drafts' / f'{a.slug}.md'
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(f'# {a.title}\n\nSymptom: {a.symptom}\nDomain: {a.domain or "-"}\nVerified: pending\n\n'
                     f'## What to do\n\n{a.body.strip()}\n\n## Evidence\n\n{a.evidence.strip()}\n', encoding='utf-8')
    print(f'draft written: {draft}')
    for _, path, symptom in related:
        print(f'  related, check it is not the same lesson: {path} — {symptom}')
    return 0


def cmd_accept(a) -> int:
    home = Path(a.home)
    draft = find(home, a.slug, 'drafts')
    if not draft:
        print(f'no draft {a.slug}', file=sys.stderr)
        return 2
    text = draft.read_text(encoding='utf-8')
    domain = (re.search(r'^Domain:\s*(\S+)', text, re.M) or [None, '-'])[1]
    target = (home / domain if domain != '-' else home) / f'{a.slug}.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = f'Verified: {dt.date.today().isoformat()} at {a.sha}'
    target.write_text(re.sub(r'^Verified:.*$', stamp, text, count=1, flags=re.M), encoding='utf-8')
    draft.unlink()
    write_index(home, Path(a.skill) if a.skill else None)
    print(f'accepted: {target}')
    return 0


def cmd_retire(a) -> int:
    home = Path(a.home)
    path = find(home, a.slug)
    if not path:
        print(f'no lesson {a.slug}', file=sys.stderr)
        return 2
    target = home / 'retired' / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding='utf-8').rstrip('\n')
    target.write_text(f'{text}\n\nRetired: {dt.date.today().isoformat()} — {a.reason}\n', encoding='utf-8')
    path.unlink()
    write_index(home, Path(a.skill) if a.skill else None)
    print(f'retired: {target}')
    return 0


def cmd_check(a) -> int:
    home = Path(a.home)
    index = (home / 'INDEX.md').read_text(encoding='utf-8') if (home / 'INDEX.md').exists() else ''
    linked = set(re.findall(r'\]\(([^)]+\.md)\)', index))
    present = {p.relative_to(home).as_posix() for p in lessons(home)}
    problems = [f'not in INDEX.md: {p}' for p in sorted(present - linked)]
    problems += [f'INDEX.md points at a missing file: {p}' for p in sorted(linked - present)]
    for line in problems:
        print(line)
    print(f'{len(problems)} problem(s)')
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('add', help='write a draft lesson (needs evidence)')
    p.add_argument('--home', required=True)
    p.add_argument('--domain', default='')
    p.add_argument('--slug', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--symptom', required=True, help='one line, written as what the bot sees')
    p.add_argument('--evidence', required=True)
    p.add_argument('--body', required=True)
    p = sub.add_parser('search', help='find accepted lessons by symptom words')
    p.add_argument('--home', action='append', required=True)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=5)
    for name, extra in (('accept', '--sha'), ('retire', '--reason')):
        p = sub.add_parser(name, help=f'{name} a lesson (the Advisor\'s step; the owner\'s until it exists)')
        p.add_argument('--home', required=True)
        p.add_argument('slug')
        p.add_argument(extra, required=True)
        p.add_argument('--skill', help='SKILL.md whose index section to refresh')
    p = sub.add_parser('index', help='rewrite INDEX.md (and a SKILL.md index section)')
    p.add_argument('--home', required=True)
    p.add_argument('--skill')
    p = sub.add_parser('check', help='INDEX.md and lesson files agree; exit 1 if not')
    p.add_argument('--home', required=True)
    a = parser.parse_args()
    if a.command == 'search':
        hits = search([Path(h) for h in a.home], a.query, a.limit)
        for score, path, symptom in hits:
            print(f'{path}  {symptom}')
        if not hits:
            print('no lesson matches')
        return 0
    if a.command == 'index':
        write_index(Path(a.home), Path(a.skill) if a.skill else None)
        return 0
    return {'add': cmd_add, 'accept': cmd_accept, 'retire': cmd_retire, 'check': cmd_check}[a.command](a)


if __name__ == '__main__':
    sys.exit(main())
