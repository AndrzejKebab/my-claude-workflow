import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import skill_check as sc  # noqa: E402

GOOD = '''#!/usr/bin/env python3
"""Count lines. Programs started: none."""
import argparse
if __name__ == "__main__":
    argparse.ArgumentParser(description="count lines").parse_args()
'''
SPAWNS_UNDECLARED = '''#!/usr/bin/env python3
"""Build it."""
import argparse, subprocess
if __name__ == "__main__":
    argparse.ArgumentParser(description="build it").parse_args()
    subprocess.run(["git", "status"])
'''
FOREVER = '''#!/usr/bin/env python3
"""Wait. Programs started: none."""
import argparse
def wait():
    while True:
        pass
if __name__ == "__main__":
    argparse.ArgumentParser(description="wait").parse_args()
    wait()
'''
GUI = '''#!/usr/bin/env bash
# Open it. spawns: notepad
case "$1" in --help) echo "open it"; exit 0;; esac
notepad.exe report.txt
'''


class SkillCheck(unittest.TestCase):
    def skill(self, name, source, documented=True, example=True):
        root = Path(tempfile.mkdtemp())
        (root / 'scripts').mkdir()
        (root / 'scripts' / name).write_text(source, encoding='utf-8')
        body = f'# Skill\n\n`scripts/{name}` does it.\n' if documented else '# Skill\n'
        if example:
            body += f'\nExample run:\n\n```\n$ python {name}\nok\n```\n'
        (root / 'SKILL.md').write_text(body, encoding='utf-8')
        return root / 'scripts' / name

    def problems(self, path):
        return [problem.split(':')[0] for problem in sc.check(path, path.parent.parent / 'SKILL.md')]

    def test_a_good_tool_passes(self):
        self.assertEqual(self.problems(self.skill('count.py', GOOD)), [])

    def test_undeclared_process_starts_are_found(self):
        self.assertIn('spawns', self.problems(self.skill('build.py', SPAWNS_UNDECLARED)))

    def test_a_loop_that_can_run_forever_is_found(self):
        self.assertIn('loop', self.problems(self.skill('wait.py', FOREVER)))

    def test_a_gui_program_is_refused(self):
        self.assertIn('gui', self.problems(self.skill('open.sh', GUI)))

    def test_missing_index_and_example_are_found(self):
        found = self.problems(self.skill('count.py', GOOD, documented=False, example=False))
        self.assertIn('index', found)
        self.assertIn('example', found)


if __name__ == '__main__':
    unittest.main()
