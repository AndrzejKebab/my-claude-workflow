import os
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


class GraphRefresh(unittest.TestCase):
    def setUp(self):
        root = Path(tempfile.mkdtemp())
        (root / 'game').mkdir()
        board.configure(root / 'game', root / 'hermes', root / 'data', 'daily', CONFIG)
        board.DEADLINE = float('inf')
        self.trees = {}
        for n in (1, 2, 3):
            tree = root / f'game-worker-{n}'
            (tree / 'graphify-out').mkdir(parents=True)
            graph = tree / 'graphify-out' / 'graph.json'
            graph.write_text('{}', encoding='utf-8')
            self.trees[n] = (tree, graph)
        old = time.time() - 86400
        os.utime(self.trees[1][1], (old, old))  # older than its last commit: stale
        self.calls = []

        def run(*args, cwd=None, timeout=120):
            if args[1:3] == ('log', '-1'):
                return str(int(time.time() - 3600))
            self.calls.append((args, cwd))
            return 'Code graph updated.'
        for name, value in (('DRY_RUN', False), ('run', run)):
            patcher = mock.patch.object(board, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = mock.patch.object(board.shutil, 'which', lambda name: f'X:/bin/{name}')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_only_a_graph_older_than_its_last_commit_is_rebuilt(self):
        rebuilt = board.refresh_graphs()
        self.assertEqual(rebuilt, [self.trees[1][0]])
        self.assertEqual(len(self.calls), 1)
        args, cwd = self.calls[0]
        self.assertEqual(args[1:], ('update', '.'))
        self.assertEqual(Path(cwd), self.trees[1][0])

    def test_a_worktree_without_a_graph_is_left_alone(self):
        (self.trees[2][1]).unlink()
        board.refresh_graphs()
        self.assertTrue(all(Path(cwd) != self.trees[2][0] for _, cwd in self.calls))


if __name__ == '__main__':
    unittest.main()
