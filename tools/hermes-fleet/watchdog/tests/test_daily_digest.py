import datetime as dt
import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import board  # noqa: E402
import daily_digest as dd  # noqa: E402
import fleet_metrics as fm  # noqa: E402
import lesson_detect as ld  # noqa: E402

CONFIG = {'github_repo': 'owner/game', 'worker_worktree': '../game-worker-{n}',
          'alerts': {'profile': 'manager', 'channel': '42'}}


def noon(days_ago: int) -> float:
    day = dt.date.today() - dt.timedelta(days=days_ago)
    return dt.datetime.combine(day, dt.time(12)).timestamp()


def history_with(event_days: list[int], bot: str = 'worker-1', days: int = 30):
    """Ten turns a day for every bot over `days` days; one false "cannot" for `bot` on each of `event_days`."""
    def history(profile):
        turns = [noon(d) + i for d in range(1, days + 1) for i in range(10)]
        events = {kind: [] for kind in ('false_cannot', 'headless_block', 'cannot_claim')}
        if profile == bot:
            events['false_cannot'] = [fm.Event('false_cannot', 's', d, noon(d) + 99, 'c', 't') for d in event_days]
        return turns, events
    return history


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        board.configure(self.root / 'repo', self.root / 'hermes', self.root / 'data', 'daily', CONFIG)
        board.DEADLINE = float('inf')
        self.general = self.root / 'general'
        self.general.mkdir()
        self.sent, self.woken = [], []
        for target, name, value in (
                (board, 'DRY_RUN', False),
                (board, 'send_text', lambda text, profile, to: self.sent.append((profile, to, text)) or True),
                (board, 'wake', lambda profile, text: self.woken.append((profile, text)) or True),
                (ld, 'GENERAL_HOME', self.general)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        log = board.LOG_FILE.read_text(encoding='utf-8') if board.LOG_FILE.exists() else ''
        self.assertNotIn('failed', log)


class Trigger(Base):
    def test_fires_when_a_bot_gets_worse(self):
        with mock.patch.object(dd, 'history', history_with([1, 2, 3, 4])):
            _, fired, _ = dd.trends(time.time())
        self.assertTrue(any(line.startswith('worker-1 false "cannot"') for line in fired), fired)

    def test_quiet_on_a_flat_rate(self):
        with mock.patch.object(dd, 'history', history_with(list(range(1, 31)))):
            _, fired, _ = dd.trends(time.time())
        self.assertEqual(fired, [])


class Digest(Base):
    def setUp(self):
        super().setUp()
        for name, value in (('trends', lambda now: (['fleet: false "cannot" 0'], [], False)),
                            ('long_prs', lambda now, state: ([], []))):
            patcher = mock.patch.object(dd, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_no_work_sends_at_once_and_wakes_nobody(self):
        dd.digest(time.time(), {})
        self.assertEqual(self.woken, [])
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0][:2], ('advisor', 'discord'))
        self.assertIn('Fleet digest', self.sent[0][2])

    def draft(self):
        (self.general / 'drafts').mkdir()
        path = self.general / 'drafts' / 'gateway-restart.md'
        path.write_text('# x\n\nSymptom: y\n', encoding='utf-8')
        return path

    def test_work_wakes_the_advisor_and_waits_for_its_notes(self):
        draft = self.draft()
        now = time.time()
        dd.digest(now, {})
        self.assertEqual([p for p, _ in self.woken], ['advisor'])
        self.assertIn(str(draft), self.woken[0][1])
        self.assertEqual(self.sent, [])
        dd.send_pending(now + 600)
        self.assertEqual(self.sent, [])
        notes = Path(json.loads(next(board.STATE_FILE.parent.glob('*.pending.json')).read_text())['notes'])
        notes.write_text('accepted: gateway-restart', encoding='utf-8')
        dd.send_pending(now + 1200)
        dd.send_pending(now + 1800)
        self.assertEqual(len(self.sent), 1)
        self.assertIn('accepted: gateway-restart', self.sent[0][2])

    def test_no_notes_in_time_sends_the_facts_once(self):
        self.draft()
        now = time.time()
        dd.digest(now, {})
        dd.send_pending(now + dd.NOTES_HOURS * 3600)
        dd.send_pending(now + dd.NOTES_HOURS * 3600 + 900)
        self.assertEqual(len(self.sent), 1)
        self.assertIn('did not finish', self.sent[0][2])


def iso(seconds: float) -> str:
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(seconds))


class LongPrs(Base):
    def setUp(self):
        super().setUp()
        self.now = time.time()
        self.prs = []
        self.labels = {}
        self.advisor_comment = {}
        for name, value in (('open_prs', lambda: self.prs),
                            ('pr_labels', lambda number: self.labels.get(number, [])),
                            ('advisor_view', lambda number: self.advisor_comment.get(number, ''))):
            patcher = mock.patch.object(dd, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def pr(self, number, days_old, current=('in-progress',)):
        self.prs.append({'number': number, 'createdAt': iso(self.now - days_old * 86400), 'url': f'u{number}',
                         'title': 't', 'labels': [{'name': name} for name in current]})

    def rounds(self, number, *labels):
        self.labels[number] = [(iso(self.now - 3600 * (len(labels) - i)), name) for i, name in enumerate(labels)]

    def test_seven_days_open_goes_to_the_advisor(self):
        self.pr(1, 8)
        first, second = dd.long_prs(self.now, {})
        self.assertEqual([p['number'] for p in first], [1])
        self.assertEqual(second, [])

    def test_five_rounds_without_final_review(self):
        self.pr(2, 2)
        self.rounds(2, *['waits-for-review', 'in-progress'] * 5)
        first, _ = dd.long_prs(self.now, {})
        self.assertEqual([p['number'] for p in first], [2])

    def test_reaching_final_review_restarts_the_rounds(self):
        self.pr(3, 2)
        self.rounds(3, 'waits-for-review', 'waits-for-review', 'waits-for-review', 'waits-for-final-review',
                    'in-progress', 'waits-for-review', 'waits-for-review')
        self.assertEqual(dd.long_prs(self.now, {}), ([], []))

    def test_counter_restarts_then_a_second_trigger_goes_to_the_owner(self):
        self.pr(4, 8)
        self.advisor_comment[4] = 'https://github.com/x/pull/4#issuecomment-9'
        state = {}
        self.assertEqual(len(dd.long_prs(self.now, state)[0]), 1)
        self.assertEqual(dd.long_prs(self.now + 86400, state), ([], []))
        first, second = dd.long_prs(self.now + 8 * 86400, state)
        self.assertEqual(first, [])
        self.assertEqual(len(second), 1)
        self.assertIn('#4', second[0])
        self.assertIn('issuecomment-9', second[0])

    def test_items_with_the_advisor_or_owner_are_not_counted(self):
        self.pr(5, 9, current=('waits-for-final-review',))
        self.pr(6, 9, current=('waits-for-eye-review',))
        self.assertEqual(dd.long_prs(self.now, {}), ([], []))

    def test_digest_puts_long_prs_in_the_advisor_batch(self):
        self.pr(7, 8)
        with mock.patch.object(dd, 'trends', lambda now: ([], [], False)):
            dd.digest(self.now, {})
        self.assertEqual([p for p, _ in self.woken], ['advisor'])
        self.assertIn('#7', self.woken[0][1])
        self.assertIn('history comment', self.woken[0][1])


class AdvisorUsage(Base):
    def test_weekly_figure_is_the_difference_between_snapshots(self):
        path = board.HERMES_ROOT / 'profiles' / 'advisor' / 'state.db'
        path.parent.mkdir(parents=True)
        db = sqlite3.connect(path)
        db.execute('create table messages (id integer primary key, session_id text, role text, content text, '
                   'timestamp real)')
        db.execute('create table session_model_usage (api_call_count int, input_tokens int, output_tokens int, '
                   'cache_read_tokens int, cache_write_tokens int)')
        db.execute('insert into session_model_usage values (15, 600, 400, 300, 300)')
        db.commit()
        db.close()
        week_ago = (dt.date.today() - dt.timedelta(days=8)).isoformat()
        state = {f'advtokens#{week_ago}': [10, 1000]}
        line = dd.advisor_usage(time.time(), state)
        self.assertIn(f'5 calls, 600 tokens since {week_ago}', line)


if __name__ == '__main__':
    unittest.main()
