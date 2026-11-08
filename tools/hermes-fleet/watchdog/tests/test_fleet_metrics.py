import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fleet_metrics as fm  # noqa: E402

APPROVED = '{"output": "", "exit_code": 0, "approval": "Command was flagged (script execution via heredoc) and auto-approved by smart approval."}'
BLOCKED = ('{"output": "", "error": "BLOCKED: Command flagged as dangerous (script execution via heredoc) but '
           'single-query mode (-q) runs without a user present to approve it."}')


def fake_db(rows):
    db = sqlite3.connect(':memory:')
    db.execute('create table messages (id integer primary key, session_id text, role text, content text, '
               'tool_name text, timestamp real)')
    db.executemany('insert into messages (session_id, role, content, tool_name, timestamp) values (?,?,?,?,?)', rows)
    return db


class FalseCannot(unittest.TestCase):
    def test_block_after_earlier_approval_then_cannot_is_counted(self):
        db = fake_db([
            ('s', 'tool', APPROVED, 'terminal', 100.0),
            ('s', 'user', 'Message from Manager: run it', None, 200.0),
            ('s', 'tool', BLOCKED, 'terminal', 210.0),
            ('s', 'assistant', 'I cannot run this script from here.', None, 220.0),
        ])
        events = fm.false_cannot(db)
        self.assertEqual([e.category for e in events], ['script execution via heredoc'])

    def test_block_without_earlier_approval_is_not_false(self):
        db = fake_db([
            ('s', 'tool', BLOCKED, 'terminal', 210.0),
            ('s', 'assistant', 'I cannot run this script from here.', None, 220.0),
        ])
        self.assertEqual(fm.false_cannot(db), [])

    def test_block_followed_by_workaround_is_not_a_claim(self):
        db = fake_db([
            ('s', 'tool', APPROVED, 'terminal', 100.0),
            ('s', 'tool', BLOCKED, 'terminal', 210.0),
            ('s', 'assistant', 'Wrote the script to a file and ran it.', None, 220.0),
        ])
        self.assertEqual(fm.false_cannot(db), [])

    def test_cannot_about_something_else_is_not_a_claim(self):
        db = fake_db([
            ('s', 'tool', APPROVED, 'terminal', 100.0),
            ('s', 'tool', BLOCKED, 'terminal', 210.0),
            ('s', 'assistant', 'Pushed. The old head cannot resolve that GUID, so the slot stays empty.', None, 220.0),
        ])
        self.assertEqual(fm.false_cannot(db), [])

    def test_replayed_rows_count_once(self):
        rows = [('s', 'tool', APPROVED, 'terminal', 100.0),
                ('s', 'tool', BLOCKED, 'terminal', 210.0),
                ('s', 'assistant', 'I cannot run this script from here.', None, 220.0)]
        replay = [(s, r, c, t, ts + 10_000) for s, r, c, t, ts in rows[1:]]
        self.assertEqual(len(fm.false_cannot(fake_db(rows + replay))), 1)


class HeadlessBlocks(unittest.TestCase):
    def test_counts_only_single_query_blocks(self):
        deny_rule = '{"error": "BLOCKED: this command matches the user-defined deny rule \'*multi-play.sh*\'"}'
        db = fake_db([('s', 'tool', BLOCKED, 'terminal', 1.0), ('s', 'tool', deny_rule, 'terminal', 2.0)])
        self.assertEqual(len(fm.headless_blocks(db)), 1)


class Turns(unittest.TestCase):
    def test_excludes_compaction_and_background_notices(self):
        db = fake_db([
            ('s', 'user', 'Message from Manager: go', None, 1.0),
            ('s', 'user', '[CONTEXT COMPACTION — REFERENCE ONLY] summary', None, 2.0),
            ('s', 'user', '[IMPORTANT: Background process proc_1 completed normally (exit code 0).', None, 3.0),
            ('s', 'user', 'owner text', None, 4.0),
        ])
        self.assertEqual(len(fm.turn_starts(db)), 2)


class Bounces(unittest.TestCase):
    def test_other_labels_between_do_not_hide_a_bounce(self):
        labels = ['waits-for-review', 'waits-for-final-review', 'worker:3', 'High', 'in-progress']
        self.assertEqual(fm.final_review_bounces(labels), 1)

    def test_old_status_prefix_counts(self):
        self.assertEqual(fm.final_review_bounces(['status:waits-for-final-review', 'status:in-progress']), 1)

    def test_clean_path_is_no_bounce(self):
        self.assertEqual(fm.final_review_bounces(['in-progress', 'waits-for-review', 'waits-for-final-review',
                                                  'ready-to-merge']), 0)


class Trigger(unittest.TestCase):
    def series(self, base_rate_events, recent_events, days_base=14, days_recent=9, turns=100):
        return ([(base_rate_events, turns)] * days_base) + ([(recent_events, turns)] * days_recent)

    def test_fires_when_worse_enough_often_enough_and_held(self):
        fires = fm.simulate_trigger(self.series(1, 3), base_days=14, window_days=7, factor=1.5, min_events=5,
                                    hold_days=2, cooldown_days=7)
        self.assertEqual(len(fires), 1)

    def test_quiet_when_too_few_events(self):
        fires = fm.simulate_trigger(self.series(0, 0) [:-1] + [(4, 100)], base_days=14, window_days=7, factor=1.5,
                                    min_events=5, hold_days=2, cooldown_days=7)
        self.assertEqual(fires, [])

    def test_quiet_when_not_worse(self):
        fires = fm.simulate_trigger(self.series(2, 2), base_days=14, window_days=7, factor=1.5, min_events=5,
                                    hold_days=2, cooldown_days=7)
        self.assertEqual(fires, [])

    def test_single_day_spike_does_not_fire(self):
        days = [(1, 100)] * 14 + [(1, 100)] * 6 + [(20, 100)] + [(0, 100)] * 7
        fires = fm.simulate_trigger(days, base_days=14, window_days=7, factor=1.5, min_events=5, hold_days=2,
                                    cooldown_days=7)
        self.assertLessEqual(len(fires), 1)

    def test_cooldown_blocks_repeat(self):
        fires = fm.simulate_trigger(self.series(1, 3, days_recent=14), base_days=14, window_days=7, factor=1.5,
                                    min_events=5, hold_days=2, cooldown_days=7)
        self.assertEqual(len(fires), 1)


if __name__ == '__main__':
    unittest.main()
