import argparse
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import label  # noqa: E402

STATES = {164: 'OPEN', 100: 'CLOSED'}


def args(to, add=(), remove=(), reason='r', self_check_file=None):
    return argparse.Namespace(number=433, to=to, add=list(add), remove=list(remove), reason=reason,
                              self_check_file=self_check_file, pr=None)


def state(number):
    return STATES.get(number, 'OPEN')


class SideLabels(unittest.TestCase):
    def test_only_question_and_on_hold_are_side_labels(self):
        problems = label.side_problems(args('in-progress', add=['waits-for-final-review']), state)
        self.assertTrue(any('question' in p and 'on-hold' in p for p in problems))

    def test_on_hold_goes_with_blocked_only(self):
        self.assertTrue(label.side_problems(args('in-progress', add=['on-hold']), state))

    def test_on_hold_names_an_open_item(self):
        self.assertTrue(label.side_problems(args('blocked', add=['on-hold'], reason='waiting on the build'), state))
        self.assertTrue(label.side_problems(args('blocked', add=['on-hold'], reason='Blocked by #100'), state))
        self.assertEqual(label.side_problems(args('blocked', add=['on-hold'], reason='Blocked by #164'), state), [])

    def test_a_hold_or_question_needs_no_self_check(self):
        self.assertFalse(label.needs_self_check(args('blocked', add=['on-hold'])))
        self.assertFalse(label.needs_self_check(args('blocked', add=['question'])))
        self.assertTrue(label.needs_self_check(args('blocked')))

    def test_leaving_blocked_drops_the_hold(self):
        self.assertEqual(label.side_edits(args('in-progress'), ['blocked', 'on-hold', 'worker:4']),
                         ['--remove-label', 'on-hold'])
        self.assertEqual(label.side_edits(args('blocked', add=['question']), ['in-progress']),
                         ['--add-label', 'question'])


if __name__ == '__main__':
    unittest.main()
