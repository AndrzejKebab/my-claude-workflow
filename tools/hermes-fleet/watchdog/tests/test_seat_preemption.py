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


class SeatPreemption(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp())
        board.configure(root / 'repo', root / 'hermes', root / 'data', 'board-audit', CONFIG)
        board.DEADLINE = float('inf')
        self.woken, self.stopped = [], []
        for name, value in (('DRY_RUN', False),
                            ('wake', lambda profile, text: self.woken.append((profile, text)) or True),
                            ('stop_runs', lambda bot: self.stopped.append(bot))):
            patcher = mock.patch.object(board, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.seat = board.seat_board()
        self.seat.take('worker-2', 30, 'client build', time.time())

    def test_the_owners_editor_frees_the_seat_and_stops_the_holder(self):
        with mock.patch.object(type(self.seat), 'owner_editor', lambda self: True):
            board.seat_preemption(time.time())
        self.assertEqual(self.stopped, ['worker-2'])
        self.assertEqual([p for p, _ in self.woken], ['worker-2'])
        self.assertIn("owner's Editor", self.woken[0][1])
        self.assertIsNone(self.seat.status(time.time())['holder'])

    def test_no_owner_editor_changes_nothing(self):
        with mock.patch.object(type(self.seat), 'owner_editor', lambda self: False):
            board.seat_preemption(time.time())
        self.assertEqual((self.stopped, self.woken), ([], []))


if __name__ == '__main__':
    unittest.main()
