import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import board  # noqa: E402

CONFIG = {'github_repo': 'owner/game', 'worker_worktree': '../game-worker-{n}',
          'alerts': {'profile': 'manager', 'channel': '42'}}
STOP = '2026-11-10 02:31:43,859 INFO gateway.run: Stopping gateway...\n'
TURN = '2026-11-10 {t},000 INFO [s] agent.turn_context: conversation turn: session=s model=m\n'
ENDED = '2026-11-10 {t},000 INFO [s] agent.conversation_loop: Turn ended: reason={why} model=m\n'


def epoch(clock: str) -> float:
    return time.mktime(time.strptime(f'2026-11-10 {clock}', '%Y-%m-%d %H:%M:%S'))


class RestartLoss(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        board.configure(self.root / 'repo', self.root / 'hermes', self.root / 'data', 'board-audit', CONFIG)
        board.DEADLINE = float('inf')
        (board.HERMES_ROOT / 'logs').mkdir(parents=True)
        (board.HERMES_ROOT / 'logs' / 'gateway.log').write_text(STOP, encoding='utf-8')

    def log(self, profile, *lines):
        path = board.HERMES_ROOT / 'profiles' / profile / 'logs' / 'agent.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(lines), encoding='utf-8')

    def messages(self, profile, *rows):
        con = sqlite3.connect(board.HERMES_ROOT / 'profiles' / profile / 'state.db')
        con.execute('create table messages (session_id text, role text, content text, tool_name text, timestamp real)')
        con.executemany('insert into messages values (?, ?, ?, ?, ?)', rows)
        con.commit()
        con.close()

    def test_a_turn_the_shutdown_interrupted_is_lost(self):
        self.log('worker-1', TURN.format(t='02:30:00'),
                 ENDED.format(t='02:31:45', why='interrupted_by_system(gateway_shutdown)'))
        self.assertIn('interrupted', board.lost_turn('worker-1'))

    def test_a_turn_after_the_restart_means_nothing_is_lost(self):
        self.log('worker-1', ENDED.format(t='02:31:45', why='interrupted_by_system(gateway_shutdown)'),
                 TURN.format(t='02:33:20'))
        self.assertEqual(board.lost_turn('worker-1'), '')

    def test_a_background_notice_the_restart_dropped_is_lost(self):
        self.log('worker-3', TURN.format(t='02:28:57'), ENDED.format(t='02:30:31', why='text_response(stop)'))
        self.messages('worker-3', ('s', 'tool', '{"output": "Background process started", "session_id": '
                                   '"proc_a58ea487849c", "notify_on_complete": true}', 'terminal', epoch('02:30:27')))
        self.assertIn('proc_a58ea487849c', board.lost_turn('worker-3'))

    def test_a_delivered_notice_is_not_lost(self):
        self.log('worker-3', TURN.format(t='02:28:57'), ENDED.format(t='02:30:31', why='text_response(stop)'))
        self.messages('worker-3',
                      ('s', 'tool', '{"output": "Background process started", "session_id": "proc_x", '
                                    '"notify_on_complete": true}', 'terminal', epoch('02:20:00')),
                      ('s', 'user', '[IMPORTANT: Background process proc_x completed normally', None, epoch('02:25:00')))
        self.assertEqual(board.lost_turn('worker-3'), '')

    def test_each_lost_turn_is_woken_once(self):
        self.log('worker-1', ENDED.format(t='02:31:45', why='interrupted_by_system(gateway_shutdown)'))
        state = {}
        with mock.patch.object(board, 'wake', return_value=True) as wake:
            self.assertEqual(board.restart_wakes(state), ['worker-1'])
            self.assertEqual(board.restart_wakes(state), [])
        self.assertEqual(wake.call_count, 1)


if __name__ == '__main__':
    unittest.main()
