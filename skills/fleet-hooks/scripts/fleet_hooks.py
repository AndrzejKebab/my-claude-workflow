#!/usr/bin/env python3
"""The owner's Claude Code hooks, ported to Hermes for the bots, plus the FFF nudge.

    fleet_hooks.py pre-tool   --state <file.json>   # Hermes pre_tool_call
    fleet_hooks.py pre-verify                       # Hermes pre_verify

Rules come from the Claude hooks in this repository's bin/ (cc-whole-file-reads, cc-comment-wall, cc-no-hedge);
cc-nospin is re-implemented here because it is a bash script with Claude-only advice. Reads the hook payload on
stdin, prints a Hermes directive or nothing, and fails open. Programs started: none.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

BIN = Path(__file__).resolve().parents[3] / 'bin'


def claude_hook(name: str):
    loader = importlib.machinery.SourceFileLoader(name.replace('-', '_'), str(BIN / name))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


whole_file = claude_hook('cc-whole-file-reads')
comment_wall = claude_hook('cc-comment-wall')
no_hedge = claude_hook('cc-no-hedge')

SPIN_WINDOW, SPIN_REPEATS = 120, 6
NO_OP = re.compile(r'^(true|:|echo|printf)(\s+[^|;&<>$`]{0,12})?$')
SPIN_ADVICE = ('Do not poll with no-op or repeated commands. For a long run, start it with `background: true` and '
               '`notify_on_complete: true`; you are told when it ends. To wait on a condition, wait in one call: '
               '`while <still running>; do sleep 30; done`.')
FFF_RETRY_SECONDS = 600
FFF_ADVICE = ('Search code with the FFF tools, not grep, rg, find or search_files: `mcp_fff_grep` (file contents), '
              '`mcp_fff_find_files` (file names), `mcp_fff_multi_grep` (several patterns at once). They index your '
              'workspace and rank by what you use. If FFF cannot answer this one (a path outside your workspace, or '
              'FFF is not loaded), run the same command again and it goes through.')
SCRIPT_SUFFIXES = {'.py', '.sh', '.ps1', '.cs', '.js', '.ts'}
NEW_SCRIPT_ADVICE = ('Before writing a new script, look for one that already does the job: the skill list in your '
                     'prompt (read one with `skill_view <name>`; the toolbox skills start with `fleet-`), and the '
                     "game's `.agents/skills`. If one exists, use it or add a flag to it instead of a copy. If none "
                     'fits, write this file again and it goes through.')


def new_scratch_script(path: str) -> bool:
    """A script file that does not exist yet, being written into a scratch folder (#40)."""
    target = Path(path)
    parts = {part.lower() for part in target.parts}
    in_scratch = '.scratch' in parts or ('cache' in parts and 'scratch' in parts)
    return in_scratch and target.suffix.lower() in SCRIPT_SUFFIXES and not target.exists()


SEGMENT = re.compile(r'\s*(\|\||&&|;|\|)\s*')
RECURSIVE_GREP = re.compile(r'^(sudo\s+)?(grep|egrep)\s+(.*\s)?(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)\b')
RG = re.compile(r'^(rg|ag)\s')
FIND = re.compile(r'^find\s+\S+.*\s-(i?name|i?path)\s')


class State:
    """Small per-profile memory between hook runs (spin counts, FFF nudges)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            self.data = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.data = {}

    def save(self, now: float) -> None:
        for bucket, keep in (('spin', SPIN_WINDOW), ('fff', FFF_RETRY_SECONDS)):
            items = self.data.get(bucket, {})
            for key in list(items):
                stamps = [t for t in (items[key] if isinstance(items[key], list) else [items[key]]) if now - t <= keep]
                if stamps:
                    items[key] = stamps if bucket == 'spin' else stamps[-1]
                else:
                    del items[key]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle, temp = tempfile.mkstemp(dir=self.path.parent, suffix='.tmp')
        with os.fdopen(handle, 'w', encoding='utf-8') as stream:
            json.dump(self.data, stream)
        os.replace(temp, self.path)


def block(message: str) -> dict:
    return {'action': 'block', 'message': message}


def digest(*parts: str) -> str:
    return hashlib.sha1('\0'.join(parts).encode('utf-8')).hexdigest()[:16]


def searches_code(command: str) -> bool:
    """A recursive grep, rg or find run as a command; grep on a pipe is filtering output, not searching."""
    pieces = SEGMENT.split(command.strip())
    for index in range(0, len(pieces), 2):
        piece = pieces[index].strip()
        after_pipe = index > 0 and pieces[index - 1] == '|'
        if not after_pipe and (RECURSIVE_GREP.match(piece) or RG.match(piece) or FIND.match(piece)):
            return True
    return False


CD = re.compile(r'^\s*cd\s+("[^"]+"|\'[^\']+\'|\S+)')


def graph_for(*places: str) -> Path | None:
    """The repository holding a graphify graph that contains the first place given, if any."""
    for place in filter(None, places):
        path = Path(place.strip('"\''))
        if re.match(r'^/[a-zA-Z]/', place):
            path = Path(f'{place[1]}:{place[2:]}')
        for folder in (path, *path.parents):
            if (folder / 'graphify-out' / 'graph.json').is_file():
                return folder
    return None


DOCS = re.compile(r'(^|[/\\\s"\'])(Docs|\.memory|\.project-state)([/\\\s"\']|$)|\.md\b', re.I)
PATHS = re.compile(r'[A-Za-z]:[\\/][^\s"\'|;&]+|/[a-zA-Z]/[^\s"\'|;&]+')


def semantica_for(*places: str) -> Path | None:
    """The folder of the document graph this bot's own `semantica` MCP server reads, else one beside the search."""
    home = os.environ.get('HERMES_HOME')
    if home:
        try:
            config = (Path(home) / 'config.yaml').read_text(encoding='utf-8', errors='replace')
        except OSError:
            config = ''
        match = re.search(r'SEMANTICA_KG_PATH:\s*["\']?([^"\'\n]+)', config)
        if match:
            return Path(match.group(1).strip()).parent
    for place in filter(None, places):
        path = Path(f'{place[1]}:{place[2:]}') if re.match(r'^/[a-zA-Z]/', place) else Path(place.strip('"\''))
        for folder in (path, *path.parents):
            if (folder / 'semantica-graph.json').is_file():
                return folder
    return None


def fff_nudge(key: str, state: State, now: float, repo: Path | None, docs: Path | None = None) -> dict | None:
    nudged = state.data.setdefault('fff', {})
    if now - nudged.get(key, -1e18) <= FFF_RETRY_SECONDS:
        return None
    nudged[key] = now
    advice = FFF_ADVICE
    if repo is not None:
        advice = (f'This repository has a code graph. To learn how things connect (who calls what, where a concept '
                  f'lives), first run `graphify query "<question>"` in {repo.as_posix()}. Then: ' + advice)
    if docs is not None:
        advice = (f'This searches the project\'s documents. Their decisions, lessons, notes and state records are a '
                  f'graph: ask `mcp_semantica_query_graph`, `mcp_semantica_query_decisions` or '
                  f'`mcp_semantica_find_precedents` first ({docs.as_posix()}). For literal text: ' + advice)
    return block(advice)


def walls_in(text: str, suffix: str) -> list[str]:
    handle, temp = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as stream:
            stream.write(text)
        lines = text.splitlines()
        return ['\n'.join(lines[start - 1:start - 1 + count]) for start, count in comment_wall.walls(temp)]
    finally:
        os.unlink(temp)


def new_wall(path: str, new_text: str) -> str:
    try:
        old_text = Path(path).read_text(encoding='utf-8', errors='replace')
    except OSError:
        old_text = ''
    suffix = Path(path).suffix or '.sh'
    old = set(walls_in(old_text, suffix)) if old_text else set()
    added = [wall for wall in walls_in(new_text, suffix) if wall not in old]
    if not added:
        return ''
    return (f'Comment wall in {Path(path).name}: {len(added[0].splitlines())} comment lines in a row. Comments are '
            'one-liners: a comment earns its place only by saying something the code cannot (a constraint, a '
            'gotcha, a reason someone would otherwise "fix" it). A design header, a numbered rationale or a record '
            'of measurements belongs in a doc page with a one-line pointer left here. Cut or move it, then write again.')


def pre_tool(tool: str, args: dict, session: str, state: State, now: float, cwd: str = '') -> dict | None:
    if tool == 'read_file':
        name = os.path.basename(str(args.get('path') or ''))
        if name in whole_file.WHOLE_FILE and (args.get('limit') or args.get('offset')):
            return block(f'Partial read of {name} refused. ' + whole_file.WHY)
    if tool == 'terminal':
        command = str(args.get('command') or '')
        if whole_file.HEAD_TAIL.search(command):
            return block('head/tail on AGENTS.md or CONTEXT.md refused. ' + whole_file.WHY)
        trimmed = re.sub(r'\s*;?\s*$', '', command.strip())
        if NO_OP.match(trimmed):
            return block(f'Refused: `{trimmed}` does no work. ' + SPIN_ADVICE)
        stamps = state.data.setdefault('spin', {}).setdefault(digest(session, command), [])
        stamps[:] = [t for t in stamps if now - t <= SPIN_WINDOW] + [now]
        if len(stamps) > SPIN_REPEATS:
            return block(f'Refused: this exact command ran {len(stamps)} times in {SPIN_WINDOW} s, which is a spin, '
                         'not work. ' + SPIN_ADVICE)
        if searches_code(command):
            cd = CD.match(command)
            places = [cd.group(1) if cd else '', *PATHS.findall(command), str(args.get('workdir') or ''), cwd]
            repo = graph_for(*places)
            docs = semantica_for(*places) if DOCS.search(command) else None
            return fff_nudge(digest(session, command), state, now, repo, docs)
    if tool == 'search_files':
        places = [str(args.get('path') or ''), cwd]
        text = json.dumps(args, sort_keys=True)
        docs = semantica_for(*places) if DOCS.search(text) else None
        return fff_nudge(digest(session, text), state, now, graph_for(*places), docs)
    if tool == 'write_file' and new_scratch_script(str(args.get('path') or '')):
        nudged = state.data.setdefault('fff', {})
        key = digest(session, 'new-script', str(args.get('path')))
        if now - nudged.get(key, -1e18) > FFF_RETRY_SECONDS:
            nudged[key] = now
            return block(NEW_SCRIPT_ADVICE)
    if tool in ('write_file', 'patch'):
        path = str(args.get('path') or '')
        if not path or not comment_wall.is_code(path, '')[0] and Path(path).suffix:
            return None
        if tool == 'write_file':
            text = str(args.get('content') or '')
        elif args.get('old_string') is not None and args.get('mode', 'replace') == 'replace':
            try:
                current = Path(path).read_text(encoding='utf-8', errors='replace')
            except OSError:
                return None
            text = current.replace(str(args['old_string']), str(args.get('new_string') or ''), 1)
        else:
            return None
        reason = new_wall(path, text)
        return block(reason) if reason else None
    return None


def pre_verify(text: str) -> dict | None:
    text = no_hedge.strip_quoted(text or '')
    hedges = sorted({m.group(0).strip().lower() for m in no_hedge.HEDGE.finditer(text)})
    counts = sorted({m.group(0).strip().lower() for m in no_hedge.COUNTING.finditer(text)})
    cautions = sorted({m.group(0).strip().lower() for s in no_hedge.SENTENCE.split(text)
                       if not no_hedge.MEASURED.search(s) for m in no_hedge.CAUTION.finditer(s)})
    reasons = []
    if hedges:
        reasons.append('Offering the next step instead of taking it: ' + ', '.join(hedges) + '. When the step follows '
                       'from the work just finished, do it and report what happened. Ask only for a decision the '
                       'owner owns.')
    if counts:
        reasons.append('Counting the things written about: ' + ', '.join(counts) + '. Name them instead.')
    if cautions:
        reasons.append('A caveat with no measurement: ' + ', '.join(cautions) + '. Cut it, or give the number.')
    return {'action': 'continue', 'message': ' '.join(reasons) + ' Rewrite your reply without it.'} if reasons else None


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('event', choices=('pre-tool', 'pre-verify'))
    parser.add_argument('--state', help='per-profile state file (pre-tool)')
    args = parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read() or '{}')
        if args.event == 'pre-verify':
            result = pre_verify((payload.get('extra') or {}).get('final_response') or '')
        else:
            if not args.state:
                return 0
            state, now = State(Path(args.state)), time.time()
            result = pre_tool(payload.get('tool_name') or '', payload.get('tool_input') or {},
                              payload.get('session_id') or '', state, now, payload.get('cwd') or '')
            state.save(now)
    except Exception:  # noqa: BLE001 - advisory hooks fail open; the workspace guard is the hard one
        return 0
    if result:
        print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
