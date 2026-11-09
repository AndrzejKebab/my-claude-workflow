import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seat  # noqa: E402

T0 = 1_000_000.0


class Seat(unittest.TestCase):
    def setUp(self):
        self.board = seat.Board(Path(tempfile.mkdtemp()) / 'seat.json')
        self.owner_editor = False
        self.board.owner_editor = lambda: self.owner_editor

    def take(self, bot, now=T0, minutes=30):
        return self.board.take(bot, minutes, 'run', now)

    def test_a_free_seat_is_taken_and_checked(self):
        self.assertTrue(self.take('worker-1').ok)
        self.assertTrue(self.board.check('worker-1', T0 + 60).ok)
        self.assertFalse(self.board.check('worker-2', T0 + 60).ok)

    def test_a_busy_seat_queues_in_arrival_order(self):
        self.take('worker-1')
        second, third = self.take('worker-2'), self.take('worker-3')
        self.assertFalse(second.ok)
        self.assertIn('queue 1', second.message)
        self.assertIn('queue 2', third.message)
        self.board.release('worker-1', T0 + 60)
        self.assertFalse(self.take('worker-3', T0 + 61).ok)  # worker-2 is first in line
        self.assertTrue(self.take('worker-2', T0 + 62).ok)

    def test_the_advisor_goes_ahead_of_the_queue(self):
        self.take('worker-1')
        self.take('worker-2')
        self.take('advisor')
        self.board.release('worker-1', T0 + 60)
        self.assertFalse(self.take('worker-2', T0 + 61).ok)
        self.assertTrue(self.take('advisor', T0 + 62).ok)

    def test_a_lease_lasts_its_minutes_plus_grace(self):
        self.take('worker-1', minutes=10)
        self.assertFalse(self.take('worker-2', T0 + 15 * 60).ok)
        self.assertTrue(self.take('worker-2', T0 + 21 * 60).ok)

    def test_renew_extends_only_your_own_lease(self):
        self.take('worker-1', minutes=10)
        self.assertTrue(self.board.renew('worker-1', 30, T0 + 9 * 60).ok)
        self.assertFalse(self.board.renew('worker-2', 30, T0 + 9 * 60).ok)
        self.assertTrue(self.board.check('worker-1', T0 + 45 * 60).ok)

    def test_the_owners_editor_takes_precedence(self):
        self.take('worker-1')
        self.owner_editor = True
        self.assertFalse(self.board.check('worker-1', T0 + 60).ok)
        refused = self.take('worker-2', T0 + 60)
        self.assertFalse(refused.ok)
        self.assertIn("owner's Editor", refused.message)
        self.assertEqual(self.board.preempted(T0 + 60), 'worker-1')


if __name__ == '__main__':
    unittest.main()
