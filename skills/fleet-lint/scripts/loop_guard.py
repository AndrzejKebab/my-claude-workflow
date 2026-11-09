#!/usr/bin/env python3
"""Fail on tool loops that can run forever.

Owner rule: no tool may contain `while (true)` or any loop that can run without end.
A polling loop that never gives up is how a retry turned into a Hub window per second.

Rules (per file type):
  forever   literal infinite forms: sh `while true` / `while :` / `until false`,
            py `while True` / `while 1`, cs/ps1 `while (true)` / `while ($true)` / `for (;;)`.
  unbounded a shell `while`/`until` whose condition has neither `read` (bounded by input)
            nor a numeric comparison (`-lt`, `-le`, `-gt`, `-ge`, or `<`/`>` inside `(( ))`), i.e. nothing
            that ends it. Redirections such as `2>&1` do not count as a bound.

Escape hatch: a loop that is bounded some other way carries `loop-bound: <reason>` in a comment
on the loop line or the line above. The reason is read by a human; the lint only checks it exists.

Usage:
  loop_guard.py <path> [<path> ...]      scan files or directories (recursive)
  loop_guard.py --list-rules             print the rules
Exit 0 = clean, 1 = findings, 2 = bad arguments.
"""
import argparse
import os
import re
import sys

SKIP_DIRS = {'.git', 'node_modules', 'Library', 'Temp', 'Logs', 'obj', 'bin', '__pycache__', 'graphify-out', 'PackageCache'}

FOREVER = {
    '.sh': [re.compile(r'^\s*(while\s+(true|:)\b|while\s+:\s*;|until\s+false\b)')],
    '.bash': None,
    '.py': [re.compile(r'^\s*while\s+(True|1)\s*:')],
    '.cs': [re.compile(r'\bwhile\s*\(\s*true\s*\)'), re.compile(r'\bfor\s*\(\s*;\s*;\s*\)')],
    '.ps1': [re.compile(r'\bwhile\s*\(\s*\$true\s*\)', re.I), re.compile(r'\bfor\s*\(\s*;\s*;\s*\)')],
}
FOREVER['.bash'] = FOREVER['.sh']

SH_LOOP = re.compile(r'^\s*(while|until)\s+(.*?)(;\s*do\b|$)')
SH_BOUNDED = re.compile(r'\bread\b|-(lt|le|gt|ge)\b|\(\(.*[<>].*\)\)')
PRAGMA = 'loop-bound:'


def has_pragma(lines, index):
    if PRAGMA in lines[index]:
        return True
    return index > 0 and PRAGMA in lines[index - 1]


def scan_file(path):
    ext = os.path.splitext(path)[1].lower()
    rules = FOREVER.get(ext)
    if rules is None:
        return []
    try:
        with open(path, encoding='utf-8', errors='replace') as handle:
            lines = handle.read().splitlines()
    except OSError as error:
        return [(path, 0, 'unreadable', str(error))]

    findings = []
    for index, line in enumerate(lines):
        code = line.split('//')[0] if ext == '.cs' else line
        stripped = code.lstrip()
        if stripped.startswith('#') and ext in ('.sh', '.bash', '.py', '.ps1'):
            continue
        if has_pragma(lines, index):
            continue
        if any(rule.search(code) for rule in rules):
            findings.append((path, index + 1, 'forever', line.strip()))
            continue
        if ext in ('.sh', '.bash'):
            match = SH_LOOP.match(code)
            if match and not SH_BOUNDED.search(match.group(2)):
                findings.append((path, index + 1, 'unbounded', line.strip()))
    return findings


def walk(target):
    if os.path.isfile(target):
        yield target
        return
    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            yield os.path.join(root, name)


def main():
    parser = argparse.ArgumentParser(description='Fail on tool loops that can run forever.')
    parser.add_argument('paths', nargs='*')
    parser.add_argument('--list-rules', action='store_true')
    args = parser.parse_args()
    if args.list_rules:
        print(__doc__)
        return 0
    if not args.paths:
        parser.print_usage(sys.stderr)
        return 2

    findings = []
    for target in args.paths:
        if not os.path.exists(target):
            print(f'no such path: {target}', file=sys.stderr)
            return 2
        for path in walk(target):
            findings.extend(scan_file(path))

    for path, line, rule, text in findings:
        print(f'{path}:{line}: {rule}: {text[:140]}')
    print(f'loop_guard: {len(findings)} finding(s)')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
