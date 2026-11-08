import datetime
import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import board  # noqa: E402

CONFIG = {'github_repo': 'owner/game', 'worker_worktree': 'X:/nowhere/game-worker-{n}',
          'alerts': {'profile': 'manager', 'channel': '42'}, 'kept_branches': ['keep/me']}


def iso(minutes_ago: float) -> str:
    moment = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=minutes_ago)
    return moment.strftime('%Y-%m-%dT%H:%M:%SZ')


def pr(number, **fields):
    entry = dict(number=number, title='t', url=f'u{number}', is_pr=True, kind='PR', labelled_at=iso(60),
                 reviewer_at='', reviewer_answered=False, worker='', author_at='', other_at='',
                 head_committed_at='2026-11-08T08:00:00Z')
    entry.update(fields)
    return entry


class BoardCase(unittest.TestCase):
    """Runs board_audit against a fake board: no GitHub, no git, no wakes leave the process."""

    board_items: dict = {}

    def setUp(self):
        self.data = Path(tempfile.mkdtemp())
        board.configure(Path('X:/repo'), Path('X:/hermes'), self.data, 'board-audit', CONFIG)
        board.DEADLINE = float('inf')
        self.woken = []
        patches = {
            'DRY_RUN': False,
            'labelled_items': lambda label: [dict(item) for item in self.board_items.get(label, [])],
            'wake': lambda profile, text: self.woken.append((profile, text)) or True,
            'turn_running': lambda profile: False,
            'in_progress_items': lambda: [],
            'owner_replies': lambda: [],
            'worktrees': lambda: {},
            'run': lambda *args, **kwargs: '',
            'numbered_copies': lambda now, state: ([], [], []),
        }
        for name, value in patches.items():
            patcher = mock.patch.object(board, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(board.comment_signing, 'repair', lambda watermark, apply: ([], watermark))
        patcher.start()
        self.addCleanup(patcher.stop)

    def audit(self, state, now=None):
        alerts = board.board_audit(now or time.time(), state)
        log = board.LOG_FILE.read_text(encoding='utf-8') if board.LOG_FILE.exists() else ''
        self.assertNotIn('failed', log)
        return alerts


class AdvisorHandoff(BoardCase):
    board_items = {'waits-for-final-review': [pr(1)], 'waits-for-eye-review': [pr(2)]}

    def test_final_review_wakes_advisor_once_eye_review_pings_owner(self):
        state = {}
        alerts = self.audit(state)
        self.assertEqual([p for p, _ in self.woken], ['advisor'])
        self.assertIn('#1', self.woken[0][1])
        self.assertEqual(len(alerts), 1)
        self.assertIn('#2', alerts[0])
        self.woken.clear()
        self.assertEqual(self.audit(state), [])
        self.assertEqual(self.woken, [])

    def test_responsible(self):
        self.assertEqual(board.responsible([], ['waits-for-final-review']), 'advisor')
        self.assertEqual(board.responsible([], ['waits-for-eye-review']), 'advisor')
        self.assertEqual(board.responsible([], ['worker:3', 'blocked']), 'worker-3')


class OnePingPerState(BoardCase):
    board_items = {'waits-for-eye-review': [pr(999)]}

    def test_a_push_makes_a_new_state(self):
        state = {}
        self.assertEqual(len(self.audit(state)), 1)
        self.assertEqual(self.audit(state), [])
        self.board_items['waits-for-eye-review'][0]['head_committed_at'] = '2026-11-08T09:00:00Z'
        self.assertEqual(len(self.audit(state)), 1)
        self.assertEqual(self.audit(state), [])


class ReviewerStall(BoardCase):
    board_items = {
        'waits-for-review': [pr(901, labelled_at=iso(40)),
                             pr(902, labelled_at=iso(50), reviewer_at=iso(10), reviewer_answered=True)],
        'in-review': [pr(903, labelled_at=iso(20))],
    }

    def test_woken_once_oldest_first(self):
        state = {}
        self.audit(state)
        reviewer = [text for profile, text in self.woken if profile == 'reviewer' and 'your turn' in text]
        self.assertEqual(len(reviewer), 1)
        self.assertIn('#901', reviewer[0])
        self.assertIn('#903', reviewer[0])
        self.assertNotIn('#902', reviewer[0])
        self.assertIn('Start with #901', reviewer[0])
        self.woken.clear()
        self.audit(state)
        self.assertFalse([t for p, t in self.woken if p == 'reviewer' and 'your turn' in t])


class CarriedState(BoardCase):
    """The first run on the new jobs must not repeat what the single-file watchdog already sent."""

    board_items = {'waits-for-eye-review': [pr(7)]}

    def test_seeded_state_sends_nothing_new(self):
        first = {}
        self.audit(first)
        self.woken.clear()
        reply = {'number': 7, 'labels': ['waits-for-eye-review'], 'comment_id': 55, 'comment_url': 'c55',
                 'body': 'ok'}
        legacy = self.data / 'legacy.json'
        legacy.write_text(json.dumps({**first, 'ownerreply#55': 1.0, 'deadbranch#x#reported': 1.0}),
                          encoding='utf-8')
        state = board.load_state('board-audit', legacy)
        self.assertNotIn('deadbranch#x#reported', state)
        with mock.patch.object(board, 'owner_replies', lambda: [reply]):
            self.assertEqual(self.audit(state), [])
        self.assertEqual(self.woken, [])
        self.assertEqual(board.load_state('daily', legacy), {'deadbranch#x#reported': 1.0})


STRAY = pr(256, worker='5', labelled_at=iso(35), author_at=iso(43), other_at=iso(32), head_committed_at=iso(43))
STRAY_KEY = f'stray#in-progress#256#{STRAY["labelled_at"]}'


class NoManagerCopies(BoardCase):
    board_items = {
        'waits-for-review': [dict(pr(245, worker='5', labelled_at=iso(40)), is_pr=False, kind='Issue')],
        'in-progress': [STRAY],
    }

    def test_only_the_bot_holding_the_next_step_hears(self):
        alerts = self.audit({})
        profiles = [profile for profile, _ in self.woken]
        self.assertNotIn('manager', profiles)
        self.assertIn('worker-5', profiles)
        self.assertEqual(alerts, [])  # the owner hears only after two ignored wakes


class StrayNudging(BoardCase):
    board_items = {'in-progress': [STRAY]}

    def test_two_wakes_then_one_owner_alert_then_silence(self):
        state, start = {}, time.time()
        runs = [(0, 1, 0), (16, 0, 0), (31, 1, 0), (62, 0, 1), (93, 0, 0), (124, 0, 0)]
        told = []
        for minutes, wakes, alerts in runs:
            self.woken.clear()
            sent = self.audit(state, start + minutes * 60)
            told += sent
            self.assertEqual([p for p, _ in self.woken], ['worker-5'] * wakes, f'wakes at +{minutes} min')
            self.assertEqual(len(sent), alerts, f'alerts at +{minutes} min')
        self.assertIn('#256', told[0])

    def test_state_from_the_old_watchdog_repeats_nothing(self):
        state = {f'{STRAY_KEY}#dm#worker-5': time.time() - 600, f'{STRAY_KEY}#reported': 'told'}
        self.assertEqual(self.audit(state), [])
        self.assertEqual(self.woken, [])


REVIEW_FIXES = '# Reviewer\n\n### Issues to Fix\n\n- [ ] off by one (breakage: test X fails)\n'
REVIEW_CLEAN = '# Reviewer\n\n### Issues to Fix\n\nNone.\n'
REVIEW_OLD = '# Reviewer\n\n### Blocking\n\n- [ ] off by one\n'


def reviewed(number, label_age, body):
    return pr(number, worker='2', labelled_at=iso(label_age), head_committed_at=iso(90), author_at=iso(90),
              reviewer_at=iso(40), reviewer_answered=True, review_last_at=iso(40), review_last_body=body)


class LabelFix(BoardCase):
    def setUp(self):
        super().setUp()
        self.calls = []
        self.label_result = 'labels now: [x]'

        def run(*args, **kwargs):
            if any(str(arg).endswith('label.py') for arg in args):
                self.calls.append(args)
                return self.label_result
            return ''
        patcher = mock.patch.object(board, 'run', run)
        patcher.start()
        self.addCleanup(patcher.stop)

    def target(self, call):
        return call[call.index('--to') + 1]

    def test_open_issue_moves_to_in_progress(self):
        self.board_items = {'waits-for-review': [reviewed(301, 60, REVIEW_FIXES)]}
        self.audit({})
        self.assertEqual([self.target(c) for c in self.calls], ['in-progress'])
        self.assertIn('Watchdog', self.calls[0])

    def test_clean_review_moves_to_final_review(self):
        self.board_items = {'in-review': [reviewed(302, 60, REVIEW_CLEAN)]}
        self.audit({})
        self.assertEqual([self.target(c) for c in self.calls], ['waits-for-final-review'])

    def test_in_progress_with_open_issue_is_already_right(self):
        self.board_items = {'in-progress': [reviewed(303, 60, REVIEW_FIXES)]}
        self.audit({})
        self.assertEqual(self.calls, [])

    def test_old_format_review_is_not_guessed(self):
        self.board_items = {'waits-for-review': [reviewed(304, 60, REVIEW_OLD)]}
        self.audit({})
        self.assertEqual(self.calls, [])
        self.assertTrue(any('#304' in text for profile, text in self.woken if profile == 'reviewer'))

    def test_one_attempt_per_state_and_a_failure_falls_back_to_a_wake(self):
        self.label_result = ''
        self.board_items = {'waits-for-review': [reviewed(305, 60, REVIEW_FIXES)]}
        state = {}
        self.audit(state)
        self.audit(state, time.time() + 16 * 60)
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(any('#305' in text for profile, text in self.woken if profile == 'reviewer'))


class Plumbing(unittest.TestCase):
    def setUp(self):
        board.configure(Path('X:/repo'), Path('X:/hermes'), Path(tempfile.mkdtemp()), 'daily', CONFIG)

    def tearDown(self):
        board.DEADLINE = float('inf')

    def test_run_refuses_past_deadline(self):
        board.DEADLINE = time.time() - 1
        with self.assertRaises(board.OverBudget):
            board.run('git', 'status')

    def test_unsent_alert_stays_in_output(self):
        failed = subprocess.CompletedProcess([], 1, 'no token', '')
        with mock.patch.object(board, 'DRY_RUN', False), \
                mock.patch.object(board.subprocess, 'run', lambda *a, **k: failed), \
                redirect_stdout(io.StringIO()) as out:
            board.send_alerts(['PR #5 waits for eye review'])
        self.assertIn('PR #5 waits for eye review', out.getvalue())

    def test_config_read_from_main_whatever_is_checked_out(self):
        repo = Path(tempfile.mkdtemp())
        git = ['git', '-c', 'user.name=t', '-c', 'user.email=t@t']
        subprocess.run([*git, 'init', '-q', '-b', 'main'], cwd=repo, check=True)
        (repo / '.agents').mkdir()
        (repo / board.CONFIG_PATH).write_text(json.dumps(CONFIG), encoding='utf-8')
        subprocess.run([*git, 'add', '.'], cwd=repo, check=True)
        subprocess.run([*git, 'commit', '-q', '-m', 'c'], cwd=repo, check=True)
        subprocess.run([*git, 'switch', '-q', '--orphan', 'other'], cwd=repo, check=True)
        self.assertEqual(board.read_config(repo), CONFIG)


if __name__ == '__main__':
    unittest.main()
