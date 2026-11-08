import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import supervision as s  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / 'supervision.py'


def checks(*outcomes):
    return [{'bot': 'reviewer', 'category': 'issues', 'outcome': o} for o in outcomes]


class Mode(unittest.TestCase):
    def test_starts_in_full_checking(self):
        self.assertEqual(s.mode(checks()), 'full')

    def test_earns_spot_checks_at_90_percent_of_20(self):
        self.assertEqual(s.mode(checks(*['agree'] * 18, 'disagree', 'agree')), 'spot')
        self.assertEqual(s.mode(checks(*['agree'] * 17, 'disagree', 'disagree', 'disagree')), 'full')

    def test_needs_20_checks_first(self):
        self.assertEqual(s.mode(checks(*['agree'] * 19)), 'full')

    def test_spot_disagreement_restores_full_and_restarts_the_count(self):
        history = checks(*['agree'] * 20, 'disagree', *['agree'] * 19)
        self.assertEqual(s.mode(history), 'full')
        self.assertEqual(s.mode(history + checks('agree')), 'spot')

    def test_skips_do_not_count_as_checks(self):
        self.assertEqual(s.mode(checks(*['agree'] * 20, 'skipped', 'skipped')), 'spot')


class ShouldCheck(unittest.TestCase):
    def test_full_mode_checks_everything(self):
        self.assertTrue(s.should_check(checks('agree')))

    def test_spot_mode_checks_one_in_five(self):
        base = checks(*['agree'] * 20)
        self.assertFalse(s.should_check(base))
        self.assertTrue(s.should_check(base + checks(*['skipped'] * 4)))


class Cli(unittest.TestCase):
    def test_record_then_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / 'ledger.jsonl'
            for _ in range(20):
                subprocess.run([sys.executable, '-I', str(SCRIPT), 'record', '--ledger', str(ledger), '--bot', 'manager',
                                '--category', 'answers', '--outcome', 'agree', '--item', '#1', '--why', 'ok'], check=True)
            out = subprocess.run([sys.executable, '-I', str(SCRIPT), 'status', '--ledger', str(ledger)],
                                 capture_output=True, text=True, check=True).stdout
            self.assertIn('manager', out)
            self.assertIn('spot', out)

    def test_disagree_needs_a_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run([sys.executable, '-I', str(SCRIPT), 'record', '--ledger', str(Path(tmp) / 'l'),
                                     '--bot', 'manager', '--category', 'answers', '--outcome', 'disagree',
                                     '--item', '#1', '--why', ''], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
