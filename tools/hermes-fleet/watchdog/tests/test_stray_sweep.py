import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import board  # noqa: E402
import stray_sweep as ss  # noqa: E402

CONFIG = {'github_repo': 'owner/game', 'worker_worktree': '../game-worker-{n}',
          'alerts': {'profile': 'manager', 'channel': '42'}}


class Sweep(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        board.configure(self.root / 'repo', self.root / 'hermes', self.root / 'data', 'daily', CONFIG)
        board.DEADLINE = float('inf')
        self.drive, self.home, self.copy = self.root / 'drive', self.root / 'home', self.root / 'wrong' / 'Programowanie'
        for path in (self.drive / 'tmp', self.home):
            path.mkdir(parents=True)
        self.woken = []
        for name, value in (('DRY_RUN', False),
                            ('wake', lambda profile, text: self.woken.append((profile, text)) or True),
                            ('turn_running', lambda profile: False)):
            patcher = mock.patch.object(board, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(ss, 'places', lambda: ([self.drive], self.home, [self.copy]))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.state = {}

    def tearDown(self):
        log = board.LOG_FILE.read_text(encoding='utf-8') if board.LOG_FILE.exists() else ''
        self.assertNotIn('failed', log)

    def transcript(self, profile, text):
        path = board.HERMES_ROOT / 'profiles' / profile / 'state.db'
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path)
        db.execute('create table if not exists messages (id integer primary key, session_id text, role text, '
                   'content text, timestamp real)')
        db.execute("insert into messages (session_id, role, content, timestamp) values ('s', 'tool', ?, ?)",
                   (text, time.time()))
        db.commit()
        db.close()

    def sweep(self):
        return ss.stray_sweep(time.time(), self.state)

    def test_first_run_records_what_is_there_and_reports_nothing(self):
        (self.drive / 'tmp' / 'old_probe.py').write_text('x')
        self.assertEqual(self.sweep(), [])
        self.assertEqual(self.woken, [])

    def test_new_attributed_file_gives_one_line_and_one_wake(self):
        self.sweep()
        stray = self.drive / 'tmp' / 'chunk_dump_431.txt'
        stray.write_text('x')
        self.transcript('worker-3', 'wrote /tmp/chunk_dump_431.txt')
        lines = self.sweep()
        self.assertEqual(len(lines), 1)
        self.assertIn('worker-3', lines[0])
        self.assertEqual([p for p, _ in self.woken], ['worker-3'])
        self.assertIn(str(stray), self.woken[0][1])
        self.assertIn('lesson.py add', self.woken[0][1])
        self.assertEqual(self.sweep(), [])
        self.assertTrue(stray.exists())

    def test_a_folder_in_tmp_is_one_entry_named_by_its_path(self):
        self.sweep()
        clone = self.drive / 'tmp' / 'fn2master'
        (clone / '.git').mkdir(parents=True)
        (clone / '.git' / 'config').write_text('x')
        (clone / 'main.cpp').write_text('x')
        self.transcript('manager', 'git status in .git/config is fine')
        self.transcript('worker-3', 'git clone https://x F:/tmp/fn2master')
        lines = self.sweep()
        self.assertEqual(len(lines), 1)
        self.assertIn('fn2master (2 files)', lines[0])
        self.assertIn('worker-3', lines[0])

    def test_unattributed_file_in_home_is_the_owners(self):
        self.sweep()
        (self.home / 'notes_for_me.txt').write_text('x')
        self.assertEqual(self.sweep(), [])

    def test_unattributed_file_on_a_drive_root_is_still_reported(self):
        self.sweep()
        (self.drive / 'tmp' / 'mystery_output.log').write_text('x')
        lines = self.sweep()
        self.assertEqual(len(lines), 1)
        self.assertIn('no bot', lines[0])
        self.assertEqual(self.woken, [])

    def test_copy_of_a_known_tree_is_one_line_with_a_count(self):
        self.sweep()
        (self.copy / 'KebabAI OS' / 'x').mkdir(parents=True)
        for name in ('a.txt', 'b.txt'):
            (self.copy / 'KebabAI OS' / 'x' / name).write_text('x')
        lines = self.sweep()
        self.assertEqual(len(lines), 1)
        self.assertIn('2 files', lines[0])


class WakeGuard(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        board.configure(self.root / 'repo', self.root / 'hermes', self.root / 'data', 'board-audit', CONFIG)

    def test_no_live_gateway_means_no_wake(self):
        with mock.patch.object(board, 'DRY_RUN', False), mock.patch.object(board.subprocess, 'Popen') as popen:
            self.assertFalse(board.wake('worker-1', 'x'))
        popen.assert_not_called()

    def test_wake_runs_in_the_bots_workspace(self):
        with mock.patch.object(board, 'DRY_RUN', False), mock.patch.object(board, 'gateway_live', lambda: True), \
                mock.patch.object(board.subprocess, 'Popen') as popen:
            board.wake('worker-2', 'x')
            board.wake('manager', 'x')
        worker, manager = (call.args[0] for call in popen.call_args_list)
        self.assertEqual(worker[worker.index('--in') + 1], str((board.REPO / '../game-worker-2').resolve()))
        self.assertEqual(manager[manager.index('--in') + 1], str(board.HERMES_ROOT / 'profiles' / 'manager'))


if __name__ == '__main__':
    unittest.main()
