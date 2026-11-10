#!/usr/bin/env python3
"""Check a fleet tool before it is promoted, and report what the toolbox still lacks (design.md #38-41).

    skill_check.py <tool-or-folder>... [--index SKILL.md] [--quiet]

Per tool: `--help` works (scripts), the tool is named in its index (the skill's SKILL.md, or --index), loop_guard
is clean, an example run is recorded, every program it starts is declared (`spawns:` or `Programs started:`),
and it starts no GUI program. Exit 1 on any finding. Programs started: the tool itself, with --help.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'fleet-lint' / 'scripts'))
import loop_guard  # noqa: E402

SCRIPTS = {'.py', '.sh', '.ps1'}
CHECKED = SCRIPTS | {'.cs'}
DECLARED = re.compile(r'(spawns:|Programs started:)', re.I)
STARTS = {
    '.py': re.compile(r'\b(subprocess\.(run|Popen|call|check_call|check_output)|os\.system|os\.startfile|os\.exec)'),
    '.ps1': re.compile(r'\b(Start-Process|&\s*["\']?[\w:/\\.-]+\.exe)', re.I),
    '.sh': re.compile(r'(\.exe\b|\bunity\b|\bpython\b|\bdotnet\b|\bcdb\b)', re.I),
    '.cs': re.compile(r'\bProcess\.Start\b'),
}
GUI = re.compile(r'^\s*["\']?(notepad(\.exe)?|explorer(\.exe)?|mspaint|[\w:/\\ .-]*Unity Hub\.exe|code|start\s+""|'
                 r'Invoke-Item)\b|\[\s*["\'](notepad|explorer|mspaint|code)(\.exe)?["\']', re.I)


def help_works(path: Path) -> bool:
    if path.suffix == '.ps1':  # a script's usage comes from Get-Help, not a --help flag
        command = ['powershell', '-NoProfile', '-Command', f"Get-Help '{path}'"]
    else:
        command = [sys.executable if path.suffix == '.py' else 'bash', str(path), '--help']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20,
                                stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool((result.stdout + result.stderr).strip())


def check(path: Path, index: Path | None) -> list[str]:
    problems = []
    text = path.read_text(encoding='utf-8', errors='replace')
    if path.suffix == '.py' and '__main__' not in text:
        return []  # a library other tools import: it has no command line to check
    body = index.read_text(encoding='utf-8', errors='replace') if index and index.exists() else ''
    if path.suffix in SCRIPTS and not help_works(path):
        problems.append('help: `--help` does not exit 0 with a usage text')
    if path.name not in body:
        problems.append(f'index: not named in {index.name if index else "an index"}')
    if not re.search(rf'Example run[\s\S]*?```[\s\S]*?{re.escape(path.stem)}[\s\S]*?```', body):
        problems.append('example: no recorded example run (command and real output) in the index')
    if loop_guard.scan_file(str(path)):
        problems.append('loop: loop_guard finds a loop that can run forever')
    starts = STARTS.get(path.suffix)
    if starts and starts.search(_code(text, path.suffix)) and not DECLARED.search(text):
        problems.append('spawns: starts programs but declares none (`spawns:` or `Programs started:`)')
    if any(GUI.search(line) for line in _start_lines(_code(text, path.suffix), path.suffix)):
        problems.append('gui: starts a GUI program')
    return problems


def _start_lines(code: str, suffix: str) -> list[str]:
    """Lines that start a program: every shell command line, else lines with a process-start call."""
    if suffix == '.sh':
        return [piece for line in code.splitlines() for piece in re.split(r'&&|\|\||;|\|', line)]
    starts = STARTS.get(suffix)
    return [line for line in code.splitlines() if starts and starts.search(line)]


def _code(text: str, suffix: str) -> str:
    marker = '//' if suffix == '.cs' else '#'
    return '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith(marker))


def tools_under(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob('*') if p.suffix in CHECKED and '__pycache__' not in p.parts
                  and 'tests' not in p.parts and 'retired' not in p.parts)


def index_for(path: Path, given: str | None) -> Path | None:
    if given:
        return Path(given)
    for folder in path.parents:
        for name in ('SKILL.md', 'README.md'):
            if (folder / name).exists():
                return folder / name
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('targets', nargs='+')
    parser.add_argument('--index', help='the index that must name each tool (default: nearest SKILL.md or README.md)')
    parser.add_argument('--quiet', action='store_true', help='print only the totals')
    args = parser.parse_args()
    totals: dict[str, int] = {}
    tools = [tool for target in args.targets for tool in tools_under(Path(target))]
    failing = 0
    for tool in tools:
        problems = check(tool, index_for(tool, args.index))
        failing += bool(problems)
        for problem in problems:
            kind = problem.split(':')[0]
            totals[kind] = totals.get(kind, 0) + 1
            if not args.quiet:
                print(f'{tool}: {problem}')
    print(f'skill_check: {len(tools)} tool(s), {failing} with findings' +
          (' (' + ', '.join(f'{k} {v}' for k, v in sorted(totals.items())) + ')' if totals else ''))
    return 1 if failing else 0


if __name__ == '__main__':
    sys.exit(main())
