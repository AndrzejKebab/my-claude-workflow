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
import lesson_detect as ld  # noqa: E402

APPROVED = '{"approval": "Command was flagged (script execution via heredoc) and auto-approved by smart approval."}'
BLOCKED = ('{"error": "BLOCKED: Command flagged as dangerous (script execution via heredoc) but single-query mode '
           '(-q) runs without a user present to approve it."}')
OTHER_BLOCKED = BLOCKED.replace('script execution via heredoc', 'script execution via -e/-c flag')
OTHER_APPROVED = APPROVED.replace('script execution via heredoc', 'script execution via -e/-c flag')
CONFIG = {'github_repo': 'owner/game', 'worker_worktree': '../game-worker-{n}',
          'alerts': {'profile': 'manager', 'channel': '42'}}
LESSON = ('# Run scripts from a file\n\nSymptom: BLOCKED: Command flagged as dangerous (script execution via heredoc) '
          'in a headless turn\n\n## What to do\n\nWrite the script to .scratch/ and run python <file>.\n\n'
          '## Evidence\n\nx\n')


class LessonDetect(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.repo = self.root / 'repo'
        self.general = self.root / 'general'
        (self.general / 'hermes').mkdir(parents=True)
        board.configure(self.repo, self.root / 'hermes', self.root / 'data', 'lesson-detect', CONFIG)
        board.DEADLINE = float('inf')
        self.woken = []
        self.running = set()
        self.dbs = {}
        for name, value in {
            'DRY_RUN': False,
            'wake': lambda profile, text: self.woken.append((profile, text)) or True,
            'turn_running': lambda profile: profile in self.running,
        }.items():
            patcher = mock.patch.object(board, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(ld, 'GENERAL_HOME', self.general)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.state = {}
        self.now = time.time()

    def db(self, profile):
        if profile not in self.dbs:
            path = board.HERMES_ROOT / 'profiles' / profile / 'state.db'
            path.parent.mkdir(parents=True)
            connection = sqlite3.connect(path)
            connection.execute('create table messages (id integer primary key, session_id text, role text, '
                               'content text, timestamp real)')
            connection.commit()
            self.dbs[profile] = connection
        return self.dbs[profile]

    def add(self, profile, *rows):
        connection = self.db(profile)
        connection.executemany('insert into messages (session_id, role, content, timestamp) values (?,?,?,?)',
                               [('s', role, text, self.now) for role, text in rows])
        connection.commit()

    def amnesia(self, profile, turn='Message from Manager: run it', blocked=BLOCKED, approved=APPROVED):
        self.add(profile, ('tool', approved), ('user', turn), ('tool', blocked),
                 ('assistant', f'I cannot run this script from here ({len(self.woken)}, {time.time()}).'))

    def run_job(self, minutes=0):
        ld.lesson_detect(self.now + minutes * 60, self.state)
        log = board.LOG_FILE.read_text(encoding='utf-8') if board.LOG_FILE.exists() else ''
        self.assertNotIn('failed', log)

    def events(self):
        path = board.STATE_FILE.parent / 'events.jsonl'
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []

    def start(self, *profiles):
        for profile in profiles:
            self.add(profile, ('user', 'hello'))
        self.run_job()

    def test_first_run_reads_history_and_wakes_nobody(self):
        self.amnesia('worker-1')
        self.run_job()
        self.assertEqual(self.woken, [])
        self.assertEqual(self.events(), [])

    def test_uncovered_claim_asks_for_a_draft(self):
        self.start('worker-1')
        self.amnesia('worker-1')
        self.run_job()
        self.assertEqual([p for p, _ in self.woken], ['worker-1'])
        text = self.woken[0][1]
        self.assertTrue(text.startswith(ld.MARK))
        self.assertIn('lesson.py add', text)
        self.assertIn('headless', text)

    def test_covered_claim_names_the_lesson_and_asks_no_draft(self):
        (self.general / 'hermes' / 'headless-heredoc.md').write_text(LESSON, encoding='utf-8')
        self.start('worker-1')
        self.amnesia('worker-1')
        self.run_job()
        text = self.woken[0][1]
        self.assertIn('`headless-heredoc`', text)
        self.assertIn('python <file>', text)
        self.assertNotIn('lesson.py add', text)
        self.assertEqual(self.events()[-1]['action'], 'woken, lesson headless-heredoc failed in use')

    def test_one_wake_per_bot_and_category_per_day(self):
        self.start('worker-1')
        self.amnesia('worker-1')
        self.run_job()
        self.amnesia('worker-1')
        self.run_job(60)
        self.amnesia('worker-1', blocked=OTHER_BLOCKED, approved=OTHER_APPROVED)
        self.run_job(120)
        self.assertEqual(len(self.woken), 2)
        self.assertEqual([e['action'] for e in self.events() if e['kind'] == 'false_cannot'][1], 'capped')

    def test_advisor_is_recorded_not_woken(self):
        self.start('advisor')
        self.amnesia('advisor')
        self.run_job()
        self.assertEqual(self.woken, [])
        self.assertIn('recorded', [e['action'] for e in self.events() if e['kind'] == 'false_cannot'])

    def test_claim_inside_a_lesson_check_turn_is_a_repeat(self):
        self.start('worker-2')
        self.amnesia('worker-2', turn=f'{ld.MARK} - at 10:00 you wrote: ...')
        self.run_job()
        self.assertEqual(self.woken, [])
        self.assertEqual([e['action'] for e in self.events() if e['kind'] == 'false_cannot'], ['repeat after teaching'])

    def test_mid_turn_bot_is_woken_next_run(self):
        self.start('worker-3')
        self.amnesia('worker-3')
        self.running.add('worker-3')
        self.run_job()
        self.assertEqual(self.woken, [])
        self.running.clear()
        self.run_job(60)
        self.assertEqual([p for p, _ in self.woken], ['worker-3'])

    def test_headless_blocks_are_recorded_only(self):
        self.start('worker-4')
        self.add('worker-4', ('user', 'Message from Manager: go'), ('tool', BLOCKED),
                 ('assistant', 'Wrote it to a file and ran it.'))
        self.run_job()
        self.assertEqual(self.woken, [])
        self.assertEqual([e['kind'] for e in self.events()], ['headless_block'])


class Ownership(unittest.TestCase):
    def test_lesson_detect_takes_no_legacy_keys(self):
        self.assertFalse(board.owns_key('lesson-detect', 'stray#x'))
        self.assertFalse(board.owns_key('lesson-detect', 'deadbranch#x'))
        self.assertTrue(board.owns_key('board-audit', 'stray#x'))
        self.assertTrue(board.owns_key('daily', 'deadbranch#x'))


if __name__ == '__main__':
    unittest.main()
