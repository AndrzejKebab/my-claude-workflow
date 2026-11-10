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
GOOD = ('2026-11-06 17:00:00,000 INFO [s] agent.conversation_loop: Turn ended: reason=text_response(finish_reason=stop) '
        'model=deepseek-flash api_calls=1\n')
BROKE = ("2026-11-06 18:22:05,000 ERROR [s] agent.conversation_loop: Non-retryable client error: Error code: 402 - "
         "{'error': {'message': 'Insufficient Balance (request_id: x)', 'type': 'insufficient_balance_error'}}\n")
AGAIN = BROKE.replace('2026-11-06 18:22:05', '2026-11-10 01:49:07')


class Outage(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        board.configure(self.root / 'repo', self.root / 'hermes', self.root / 'data', 'board-audit', CONFIG)
        board.DEADLINE = float('inf')

    def log(self, profile, *lines):
        path = board.HERMES_ROOT / 'profiles' / profile / 'logs' / 'agent.log'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(''.join(lines), encoding='utf-8')

    def test_a_failure_after_the_last_good_turn_is_an_outage_since_the_first_failure(self):
        self.log('worker-1', GOOD, BROKE, AGAIN)
        down = board.provider_down('worker-1')
        self.assertIn('402', down)
        self.assertIn('Insufficient Balance', down)
        self.assertIn('2026-11-06 18:22', down)

    def test_a_good_turn_after_the_failure_ends_it(self):
        self.log('worker-1', BROKE, GOOD.replace('2026-11-06 17:00', '2026-11-07 09:00'))
        self.assertEqual(board.provider_down('worker-1'), '')

    def test_no_log_is_not_an_outage(self):
        self.assertEqual(board.provider_down('worker-2'), '')

    def test_a_down_bot_is_not_woken(self):
        self.log('worker-3', GOOD, BROKE)
        with mock.patch.object(board, 'DRY_RUN', False), mock.patch.object(board, 'gateway_live', lambda: True), \
                mock.patch.object(board.subprocess, 'Popen') as popen:
            self.assertFalse(board.wake('worker-3', 'x'))
        popen.assert_not_called()

    def test_the_owner_hears_once_per_outage(self):
        self.log('worker-1', GOOD, BROKE)
        self.log('manager', GOOD, BROKE)
        state = {}
        first = board.outage_alerts(state)
        self.assertEqual(len(first), 1)
        self.assertIn('manager', first[0])
        self.assertIn('worker-1', first[0])
        self.assertEqual(board.outage_alerts(state), [])


if __name__ == '__main__':
    unittest.main()
