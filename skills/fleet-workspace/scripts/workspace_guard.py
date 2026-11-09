#!/usr/bin/env python3
"""Hermes `pre_tool_call` hook: keep a bot's files inside its work folders, and its run outputs in its scratch.

    workspace_guard.py --root F:/Programowanie --root F:/Unity --scratch <bot scratch> [--home C:/Users/x]
                       [--allow read-only.txt] [--log guard.jsonl]

Reads the hook payload on stdin and prints `{"action": "block", "message": ...}`, `{"action": "modify", ...}`
(a command with no workdir runs in the scratch), or nothing. Writes go only under a root; reads and commands may
also name a path on the read-only list. Programs started: none.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ALLOW = Path(__file__).resolve().parents[1] / 'read-only.txt'
WRITE_TOOLS = {'write_file', 'patch'}
READ_TOOLS = {'read_file': 'path', 'search_files': 'path', 'vision_analyze': 'image_url'}
# A drive path, or Git Bash's /c/... form; the lookbehind keeps URLs (`https://`, `github.com/c/x`) out.
DRIVE = re.compile(r'(?<![A-Za-z0-9_\\-])([A-Za-z]):[\\/]+[^\s"\'|;&<>()`]*')  # `\n:/g`, `-r:/` in a sed: no drive
MSYS = re.compile(r'(?<![\w./\\-])/([A-Za-z])/[^\s"\'|;&<>()`]*')
QUOTED = re.compile(r'(["\'])((?:[A-Za-z]:[\\/]|/[A-Za-z]/)[^"\']*)\1')
POSIX_TMP = re.compile(r'(?<![\w./\\$-])/tmp(?=[/\s"\'`;|&)]|$)')
PATCH_FILES = re.compile(r'^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$', re.M)


@dataclass
class Rules:
    roots: list[str]
    home: str
    scratch: str
    read_only: list[str] = field(default_factory=list)
    drives: set[str] | None = None  # None: the drives this machine has
    cwd: str = ''  # the session's folder; '' when unknown, and then a relative file path is refused

    def is_drive(self, letter: str) -> bool:
        if self.drives is None:
            self.drives = {chr(c) for c in range(ord('A'), ord('Z') + 1) if os.path.isdir(f'{chr(c)}:\\')}
        return letter.upper() in self.drives


def norm(path: str) -> str:
    path = path.replace('\\', '/').strip().strip('"\'')
    path = re.sub(r'/+', '/', path)
    if re.match(r'^/[A-Za-z]/', path):
        path = f'{path[1].upper()}:{path[2:]}'
    return path.rstrip('/').lower()


def under(path: str, prefixes: list[str]) -> bool:
    path = norm(path)
    return any(path == norm(p) or path.startswith(norm(p) + '/') for p in prefixes)


def expand(text: str, home: str) -> str:
    local = f'{home}/AppData/Local'
    for name, value in (('USERPROFILE', home), ('HOME', home), ('LOCALAPPDATA', local),
                        ('APPDATA', f'{home}/AppData/Roaming')):
        text = re.sub(rf'\$\{{?{name}\}}?|%{name}%|\$env:{name}', value.replace('\\', '/'), text, flags=re.I)
    # Only `~/` and `~\`: a bare `~` is also awk's match operator.
    return re.sub(r'(?<![\w./\\-])~(?=[/\\])', home.replace('\\', '/'), text)


def command_paths(command: str, rules: Rules) -> list[str]:
    text = expand(command, rules.home).replace('\\ ', '\0')  # `Program\ Files` is one path
    found = []
    for match in QUOTED.finditer(text):  # a quoted path may hold spaces: take it whole, then drop it
        found.append(match.group(2))
    text = QUOTED.sub(' ', text)
    found += [m.group(0) for m in DRIVE.finditer(text)] + [m.group(0) for m in MSYS.finditer(text)]
    found = [path.replace('\0', ' ') for path in found if rules.is_drive(norm(path)[0])]
    return found + ['/tmp' for _ in POSIX_TMP.finditer(text)]


def refusal(path: str, rules: Rules, write: bool) -> dict:
    where = 'write there' if write else 'touch it'
    shown = f'`{path}`'
    if not is_absolute(path, rules.home) and path != '/tmp':
        shown += f' (a relative path, so it lands in `{rules.cwd or "an unknown folder"}`; give an absolute path)'
    return {'action': 'block', 'message': (
        f'Refused by the workspace guard: {shown} is outside your work folders ({", ".join(rules.roots)}), so you '
        f'may not {where}. Put every output, report and temporary file in your scratch, {rules.scratch} '
        f'(also $TMPDIR). Do not retry this path another way. If you need to read a tool or log that lives there, '
        f'ask the owner through Manager to add it to the read-only list.')}


def verdict(tool: str, args: dict, rules: Rules) -> dict | None:
    if tool == 'terminal':
        workdir = args.get('workdir')
        if workdir and not under(expand(workdir, rules.home), rules.roots):
            return refusal(workdir, rules, write=False)
        for path in command_paths(args.get('command') or '', rules):
            if path == '/tmp':
                return refusal('/tmp', rules, write=True)
            if not under(path, rules.roots + rules.read_only):
                return refusal(path, rules, write=False)
        if not workdir:
            return {'action': 'modify', 'args': {'workdir': rules.scratch}}
        return None
    if tool in WRITE_TOOLS:
        paths = [args.get('path') or '']
        if args.get('mode') == 'patch':
            paths += [a or b for a, b in PATCH_FILES.findall(args.get('patch') or '')]
        for path in filter(None, paths):
            if not under(resolve(path, rules), rules.roots):
                return refusal(path, rules, write=True)
        return None
    if tool in READ_TOOLS:
        path = args.get(READ_TOOLS[tool]) or ''
        if path and not re.match(r'^[a-z]+://', path, re.I) \
                and not under(resolve(path, rules), rules.roots + rules.read_only):
            return refusal(path, rules, write=False)
    return None


def resolve(path: str, rules: Rules) -> str:
    """An absolute form of a file tool's path: a relative one lands in the session's folder, which for a group chat
    or a CLI-made session is the home folder."""
    if is_absolute(path, rules.home):
        return expand(path, rules.home)
    return f'{rules.cwd}/{path}' if rules.cwd else f'(unknown folder)/{path}'


def session_cwd(state_db: Path, session: str) -> str:
    """The folder Hermes recorded for this session, following a continuation back to the session that has one."""
    if not session or not state_db.exists():
        return ''
    import sqlite3
    try:
        db = sqlite3.connect(f'file:{state_db.as_posix()}?mode=ro', uri=True, timeout=5)
        try:
            for _ in range(20):
                row = db.execute('select cwd, parent_session_id from sessions where id = ?', (session,)).fetchone()
                if not row:
                    return ''
                if row[0]:
                    return row[0].replace('\\', '/')
                session = row[1]
        finally:
            db.close()
    except sqlite3.Error:
        return ''
    return ''


def is_absolute(path: str, home: str) -> bool:
    path = expand(path, home)
    return bool(re.match(r'^([A-Za-z]:[\\/]|/[A-Za-z]/|/tmp\b|[\\/])', path.strip()))


def read_only_list(path: Path, home: str) -> list[str]:
    if not path.exists():
        return []
    lines = [line.split('#', 1)[0].strip() for line in path.read_text(encoding='utf-8').splitlines()]
    return [expand(line, home) for line in lines if line]


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('--root', action='append', required=True)
    parser.add_argument('--scratch', required=True)
    parser.add_argument('--home', default=str(Path.home()))
    parser.add_argument('--allow', default=str(DEFAULT_ALLOW))
    parser.add_argument('--log')
    parser.add_argument('--profile', default='', help='recorded in the log')
    args = parser.parse_args()
    payload = json.loads(sys.stdin.read() or '{}')
    home = args.home.replace('\\', '/')
    rules = Rules(args.root, home, args.scratch, read_only_list(Path(args.allow), home))
    tool, tool_input = payload.get('tool_name') or '', payload.get('tool_input') or {}
    if tool in WRITE_TOOLS or tool in READ_TOOLS:
        profile_home = os.environ.get('HERMES_HOME') or (
            str(Path(args.log).resolve().parents[1] / 'profiles' / (payload.get('profile') or args.profile))
            if args.log else '')
        if profile_home:
            rules.cwd = session_cwd(Path(profile_home) / 'state.db', payload.get('session_id') or '')
    result = verdict(tool, tool_input, rules)
    if result and result['action'] == 'modify':
        try:
            os.makedirs(rules.scratch, exist_ok=True)
        except OSError:
            pass
    if result and result['action'] == 'block' and args.log:
        log_entry(args, payload, tool, tool_input, result)
    if result:
        print(json.dumps(result))
    return 0


def log_entry(args, payload: dict, tool: str, tool_input: dict, result: dict) -> None:
    """Never let the log break the guard: it fails closed, so a crash here would block every tool call."""
    try:
        Path(args.log).parent.mkdir(parents=True, exist_ok=True)
        with open(args.log, 'a', encoding='utf-8') as handle:
            handle.write(json.dumps({'at': time.time(), 'profile': args.profile, 'tool': tool,
                                     'session': payload.get('session_id', ''),
                                     'message': result['message'][:300],
                                     'input': json.dumps(tool_input)[:300]}) + '\n')
    except OSError:
        pass


if __name__ == '__main__':
    sys.exit(main())
