"""The daily stray sweep (design.md #52): files bots left outside their workspaces. Reports, never deletes.

The first run records what is already there as known; removing those is the owner's call.
"""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import board
import lesson_detect

DRIVE_FOLDERS = ('tmp', 'c', 'f')
MAX_FILES = 2000
HIDDEN_OR_SYSTEM = 0x2 | 0x4  # pagefile.sys, desktop.ini and the like are Windows', never a bot's


def places() -> tuple[list[Path], Path, list[Path]]:
    """(drive roots, the home folder, copies of known trees on a drive they do not live on)."""
    drives = sorted({Path(p.anchor) for p in (board.REPO, board.HERMES_ROOT)} | {Path('C:/')})
    trees = [board.REPO.parent, board.HERMES_ROOT.parents[1]]
    copies = [drive / tree.relative_to(tree.anchor) for tree in trees for drive in drives
              if Path(tree.anchor) != drive]
    return drives, Path.home(), copies


def files_in(folder: Path, recursive: bool) -> list[Path]:
    if not folder.is_dir():
        return []
    found = []
    try:
        for path in (folder.rglob('*') if recursive else folder.iterdir()):
            if len(found) >= MAX_FILES:
                break
            try:
                if path.is_file() and not getattr(path.stat(), 'st_file_attributes', 0) & HIDDEN_OR_SYSTEM:
                    found.append(path)
            except OSError:
                continue
    except OSError:
        pass
    return found


def subfolders(folder: Path) -> list[Path]:
    try:
        return sorted(path for path in folder.iterdir() if path.is_dir()) if folder.is_dir() else []
    except OSError:
        return []


def mentions(path: Path, home: Path) -> list[str]:
    """Strings a transcript must hold to have written `path`: a bare name alone matches too much."""
    forms = [str(path), path.as_posix()]
    if path.parent == home:
        forms.append(f'~/{path.name}')
    elif path.parent != Path(path.anchor):
        forms += [f'{path.parent.name}/{path.name}', f'{path.parent.name}\\{path.name}']
    return forms


def attribute(paths: list[Path], home: Path) -> dict[Path, str]:
    """File -> the bot whose transcript names it most recently."""
    found: dict[Path, tuple[float, str]] = {}
    for profile in lesson_detect.PROFILES:
        database = board.HERMES_ROOT / 'profiles' / profile / 'state.db'
        if not database.exists():
            continue
        db = sqlite3.connect(f'file:{database.as_posix()}?mode=ro', uri=True, timeout=10)
        try:
            for path in paths:
                forms = mentions(path, home)
                where = ' or '.join('instr(content, ?) > 0' for _ in forms)
                row = db.execute(f'select max(timestamp) from messages where {where}', forms).fetchone()
                if row and row[0] and row[0] > found.get(path, (0.0, ''))[0]:
                    found[path] = (row[0], profile)
        finally:
            db.close()
    return {path: profile for path, (_, profile) in found.items()}


def stray_sweep(now: float, state: dict) -> list[str]:
    """Digest lines for new strays; the bot that left them is woken once a day for a draft lesson."""
    drives, home, copies = places()
    candidates = [path for drive in drives for path in files_in(drive, False)]
    counts: dict[Path, int] = {}
    for folder in (drive / name for drive in drives for name in DRIVE_FOLDERS):
        candidates += files_in(folder, False)
        for sub in subfolders(folder):
            counts[sub] = len(files_in(sub, True))  # a cloned repo or a build tree is one stray, not a file each
    candidates += list(counts)
    home_files = files_in(home, False)
    trees = {str(copy): len(files_in(copy, True)) for copy in copies if copy.is_dir()}
    current = sorted({str(path) for path in candidates + home_files} | set(trees))
    first = 'strays#known' not in state
    known = set(state.get('strays#known') or [])
    state['strays#known'] = current
    if first:
        board.log(f'stray sweep: {len(current)} existing files and trees recorded as known')
        return []
    new = [path for path in candidates + home_files if str(path) not in known]
    owners = attribute(new, home) if new else {}
    lines, by_bot = [], {}
    for path in new:
        owner = owners.get(path)
        if path in home_files and not owner:
            continue  # unnamed in every bot transcript: the owner's own file
        size = f' ({counts[path]} files)' if path in counts else ''
        lines.append(f'stray {path}{size}: ' + (f'left by {owner}' if owner else 'no bot transcript names it'))
        if owner and owner not in lesson_detect.NOT_WOKEN:
            by_bot.setdefault(owner, []).append(path)
    for tree, count in trees.items():
        if tree not in known:
            lines.append(f'copy of a known tree on the wrong drive: {tree} ({count} files)')
    day = dt.date.fromtimestamp(now).isoformat()
    for profile, paths in sorted(by_bot.items()):
        if state.get(f'strays#woke#{profile}') == day:
            continue
        state[f'strays#woke#{profile}'] = day
        board.wake(profile, 'Watchdog: these files were written outside your workspace:\n'
                   + '\n'.join(f'- {path}' for path in paths)
                   + f'\n\nYour workspace is {board.workspace(profile)}. Find the command that wrote each one (session '
                     'search), move anything you still need into the workspace, and write a draft lesson with '
                     '`lesson.py add` (fleet-lessons skill) naming the cause: a POSIX path such as /tmp given to a '
                     'Windows program, a path with no drive letter, or a turn that started outside the workspace. Do '
                     'not delete files you did not write.')
    return lines
