import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import docs_push as d  # noqa: E402

ALLOW = ['Docs/**', '.project-state/**', '.memory/**']


class PushProblems(unittest.TestCase):
    def test_markdown_on_allowed_paths_passes(self):
        self.assertEqual(d.push_problems(['Docs/TODO.md', '.project-state/snow-state.md'], ALLOW, []), [])

    def test_code_is_refused(self):
        self.assertTrue(d.push_problems(['Assets/_Project/Scripts/Snow.cs'], ALLOW, []))

    def test_markdown_outside_allowed_paths_is_refused(self):
        self.assertTrue(d.push_problems(['README.md'], ALLOW, []))

    def test_non_markdown_inside_allowed_paths_is_refused(self):
        self.assertTrue(d.push_problems(['Docs/diagram.png'], ALLOW, []))

    def test_local_paths_in_added_lines_are_refused(self):
        self.assertTrue(d.push_problems(['Docs/TODO.md'], ALLOW, ['see F:/Unity/Projects/VoxelGame/x']))

    def test_nothing_to_push_is_refused(self):
        self.assertTrue(d.push_problems([], ALLOW, []))


if __name__ == '__main__':
    unittest.main()
