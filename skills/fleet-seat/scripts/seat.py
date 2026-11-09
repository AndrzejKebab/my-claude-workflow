#!/usr/bin/env python3
"""The Unity seat: one bot at a time may build players, run players or play in the Editor.

    seat.py take --minutes 30 --purpose "client build for #431"   # exit 0 taken, 2 queued or refused
    seat.py renew --minutes 30 | release | status | check         # check: exit 0 only for the holder

The owner's own Editor on a watched project always comes first; then the Advisor; then the rest in arrival
order. A lease lasts its minutes plus 10 min grace. The caller is the bot whose HERMES_HOME runs the command
(`--as` overrides). Compiles and EditMode tests do not need the seat. Programs started: none.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

GRACE = 10 * 60
QUEUE_TTL = 60 * 60  # a queued bot that has not asked again for an hour has given up
FIRST = ('advisor',)


@dataclass
class Result:
    ok: bool
    message: str


def default_state() -> Path:
    home = Path(os.environ.get('HERMES_HOME') or Path.home())
    root = home.parents[1] if home.parent.name == 'profiles' else home
    return root / 'fleet-watchdog' / 'seat.json'


def caller() -> str:
    home = Path(os.environ.get('HERMES_HOME') or '')
    return home.name if home.parent.name == 'profiles' else 'owner'


class Board:
    def __init__(self, path: Path):
        self.path = Path(path)

    def owner_editor(self) -> bool:
        """An interactive Unity Editor open on a project listed in seat-config.json (the owner's own work)."""
        try:
            projects = json.loads((self.path.parent / 'seat-config.json').read_text(encoding='utf-8'))['owner_projects']
        except (OSError, ValueError, KeyError):
            return False
        import psutil
        wanted = [p.replace('\\', '/').rstrip('/').lower() for p in projects]
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                if (proc.info['name'] or '').lower() != 'unity.exe':
                    continue
                line = [a.replace('\\', '/').rstrip('/').lower() for a in proc.info['cmdline'] or []]
                if '-batchmode' in line or any(a.startswith('--internal-') for a in line):
                    continue
                project = line[line.index('-projectpath') + 1] if '-projectpath' in line else ''
                if project in wanted:
                    return True
            except (OSError, ValueError, IndexError):
                continue
            except Exception:  # noqa: BLE001 - psutil access errors on other users' processes
                continue
        return False

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            return {'holder': None, 'queue': []}

    def _save(self, state: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(f'.{os.getpid()}.tmp')
        temp.write_text(json.dumps(state, indent=1), encoding='utf-8')
        os.replace(temp, self.path)

    def _locked(self, change):
        """Run `change(state)` under an exclusive lock file; the lock is bounded so a crash cannot wedge the seat."""
        lock = self.path.with_suffix('.lock')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(100):  # 10 s
            try:
                handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError:
                if time.time() - lock.stat().st_mtime > 30:
                    lock.unlink(missing_ok=True)  # a holder that died mid-write
                time.sleep(0.1)
        else:
            return Result(False, 'seat state is locked; try again')
        try:
            state = self._load()
            result = change(state)
            self._save(state)
            return result
        finally:
            os.close(handle)
            lock.unlink(missing_ok=True)

    @staticmethod
    def _live(holder: dict | None, now: float) -> bool:
        return bool(holder) and now <= holder['until'] + GRACE

    @staticmethod
    def _order(queue: list[dict]) -> list[dict]:
        return sorted(queue, key=lambda entry: (entry['bot'] not in FIRST, entry['since']))

    def take(self, bot: str, minutes: float, purpose: str, now: float) -> Result:
        owner = self.owner_editor()

        def change(state):
            state['queue'] = [q for q in state['queue'] if now - q['asked'] <= QUEUE_TTL]
            holder = state['holder'] if self._live(state['holder'], now) else None
            if holder and holder['bot'] == bot:
                holder['until'] = now + minutes * 60
                return Result(True, f'{bot} already holds the seat; lease runs to {clock(holder["until"])}')
            if owner:
                return Result(False, "refused: the owner's Editor is open on the project; wait until he closes it")
            queue = self._order(state['queue'])
            first = queue[0]['bot'] if queue else bot
            if holder or first != bot:
                entry = next((q for q in state['queue'] if q['bot'] == bot), None)
                if entry is None:
                    entry = {'bot': bot, 'since': now, 'purpose': purpose}
                    state['queue'].append(entry)
                entry['asked'] = now
                place = [q['bot'] for q in self._order(state['queue'])].index(bot) + 1
                who = f'{holder["bot"]} holds it to {clock(holder["until"])}' if holder else 'it is free but not yours'
                return Result(False, f'queued: queue {place}; {who}. Ask again later.')
            state['queue'] = [q for q in state['queue'] if q['bot'] != bot]
            state['holder'] = {'bot': bot, 'since': now, 'until': now + minutes * 60, 'purpose': purpose}
            return Result(True, f'{bot} holds the seat to {clock(now + minutes * 60)} (+10 min grace)')
        return self._locked(change)

    def renew(self, bot: str, minutes: float, now: float) -> Result:
        def change(state):
            holder = state['holder']
            if not (self._live(holder, now) and holder['bot'] == bot):
                return Result(False, f'{bot} does not hold the seat; take it first')
            holder['until'] = now + minutes * 60
            return Result(True, f'lease runs to {clock(holder["until"])}')
        return self._locked(change)

    def release(self, bot: str, now: float) -> Result:
        def change(state):
            if state['holder'] and state['holder']['bot'] == bot:
                state['holder'] = None
                return Result(True, 'released')
            return Result(True, f'{bot} did not hold the seat')
        return self._locked(change)

    def check(self, bot: str, now: float) -> Result:
        holder = self._load()['holder']
        if self.owner_editor():
            return Result(False, "the owner's Editor is open on the project: no player builds, player runs or Play")
        if self._live(holder, now) and holder['bot'] == bot:
            return Result(True, f'{bot} holds the seat to {clock(holder["until"])}')
        return Result(False, f'{bot} does not hold the Unity seat. Take it first: seat.py take --minutes N --purpose "..."')

    def preempted(self, now: float) -> str | None:
        """When the owner's Editor is open, free the seat and return the bot that held it."""
        if not self.owner_editor():
            return None

        def change(state):
            holder = state['holder'] if self._live(state['holder'], now) else None
            state['holder'] = None
            return holder['bot'] if holder else None
        return self._locked(change)

    def status(self, now: float) -> dict:
        state = self._load()
        holder = state['holder'] if self._live(state['holder'], now) else None
        return {'holder': holder, 'expired': bool(state['holder']) and not holder,
                'queue': [q['bot'] for q in self._order(state['queue'])], 'owner_editor': self.owner_editor()}


def clock(stamp: float) -> str:
    return time.strftime('%H:%M', time.localtime(stamp))


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('action', choices=('take', 'renew', 'release', 'status', 'check'))
    parser.add_argument('--minutes', type=float, default=30)
    parser.add_argument('--purpose', default='')
    parser.add_argument('--as', dest='bot', default=caller())
    parser.add_argument('--state', default=str(default_state()))
    args = parser.parse_args()
    board, now = Board(Path(args.state)), time.time()
    if args.action == 'status':
        print(json.dumps(board.status(now), indent=1))
        return 0
    result = {'take': lambda: board.take(args.bot, args.minutes, args.purpose, now),
              'renew': lambda: board.renew(args.bot, args.minutes, now),
              'release': lambda: board.release(args.bot, now),
              'check': lambda: board.check(args.bot, now)}[args.action]()
    print(result.message)
    return 0 if result.ok else (3 if args.action == 'check' else 2)


if __name__ == '__main__':
    sys.exit(main())
