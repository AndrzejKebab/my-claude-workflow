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


class SemanticaRefresh(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp()) / 'game'
        (self.repo / 'Docs').mkdir(parents=True)
        self.doc = self.repo / 'Docs' / 'plan.md'
        self.doc.write_text('x', encoding='utf-8')
        self.graph = self.repo / 'semantica-graph.json'
        self.graph.write_text('{}', encoding='utf-8')
        config = dict(CONFIG, semantica={'python': 'venv/python.exe', 'extract': 'tools/extract.py',
                                          'import': 'tools/import.py', 'graph': 'semantica-graph.json',
                                          'sources': ['Docs', '.memory']})
        board.configure(self.repo, self.repo.parent / 'hermes', self.repo.parent / 'data', 'daily', config)
        board.DEADLINE = float('inf')
        self.calls = []
        patcher = mock.patch.object(board, 'run', lambda *args, cwd=None, timeout=120: self.calls.append(args) or 'ok')
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch.object(board, 'DRY_RUN', False)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_changed_doc_rebuilds_extract_then_import(self):
        old = time.time() - 3600
        os.utime(self.graph, (old, old))
        self.assertTrue(board.refresh_semantica())
        self.assertEqual([Path(args[1]).name for args in self.calls], ['extract.py', 'import.py'])

    def test_an_unchanged_set_is_left_alone(self):
        old = time.time() - 3600
        os.utime(self.doc, (old, old))
        self.assertFalse(board.refresh_semantica())
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
