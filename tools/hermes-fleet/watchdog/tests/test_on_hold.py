import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import board  # noqa: E402
from test_board import BoardCase, iso, pr  # noqa: E402

OPEN = {433: 'OPEN', 164: 'OPEN', 100: 'CLOSED', 101: 'MERGED'}


def state(number):
    return OPEN.get(number, 'OPEN')


class HoldOf(unittest.TestCase):
    def test_no_on_hold_is_no_hold(self):
        self.assertEqual(board.hold_of(['in-progress'], ['Blocked by #433'], state), ('', []))

    def test_an_open_dependency_holds(self):
        self.assertEqual(board.hold_of(['blocked', 'on-hold'], ['## Dependencies\nBlocked by #433, #100'], state),
                         ('held', [100, 433]))

    def test_closed_dependencies_release(self):
        self.assertEqual(board.hold_of(['on-hold'], ['Label: in-progress → blocked — Blocked by #100 and #101'],
                                       state), ('released', [100, 101]))

    def test_no_named_dependency_is_unnamed(self):
        self.assertEqual(board.hold_of(['on-hold'], ['waiting on the measurement issue'], state), ('unnamed', []))

    def test_a_held_item_is_parked(self):
        self.assertTrue(board.parked({'hold': 'held'}, 0.0))


class HeldItemsAreQuiet(BoardCase):
    board_items = {
        'blocked': [pr(1, labels=['blocked', 'on-hold'], hold='held', worker='4', labelled_at=iso(600))],
        'in-progress': [pr(2, labels=['in-progress', 'on-hold'], hold='held', worker='3', labelled_at=iso(600),
                           head_committed_at=iso(600))],
        'on-hold': [pr(1, labels=['blocked', 'on-hold'], hold='held', worker='4', labelled_at=iso(600)),
                    pr(2, labels=['in-progress', 'on-hold'], hold='held', worker='3', labelled_at=iso(600))],
        'waits-for-review': [pr(3, labels=['waits-for-review', 'on-hold'], hold='held', labelled_at=iso(600))],
    }

    def test_nobody_is_woken_for_a_held_item(self):
        self.audit({})
        self.assertEqual(self.woken, [])


class ReleasedHold(BoardCase):
    board_items = {
        'in-progress': [pr(5, labels=['in-progress', 'on-hold'], hold='released', held_by=[100], worker='2',
                           labelled_at=iso(600), head_committed_at=iso(600))],
        'on-hold': [pr(5, labels=['in-progress', 'on-hold'], hold='released', held_by=[100], worker='2',
                       labelled_at=iso(600), head_committed_at=iso(600))],
    }

    def test_the_author_is_told_to_drop_the_hold_once(self):
        self.audit({})
        texts = [text for profile, text in self.woken if profile == 'worker-2']
        self.assertEqual(len(texts), 1)
        self.assertIn('#100', texts[0])
        self.assertIn('--remove on-hold', texts[0])


class BlockedOnAQuestion(BoardCase):
    board_items = {'blocked': [pr(7, labels=['blocked', 'question'], hold='', worker='1', labelled_at=iso(600))]}

    def test_manager_is_told_a_question_waits(self):
        self.audit({})
        texts = [text for profile, text in self.woken if profile == 'manager']
        self.assertEqual(len(texts), 1)
        self.assertIn('question', texts[0])


if __name__ == '__main__':
    unittest.main()
