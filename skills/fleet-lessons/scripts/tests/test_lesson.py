import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'lesson.py'


def run(*args, ok=True):
    result = subprocess.run([sys.executable, '-I', str(SCRIPT), *map(str, args)], capture_output=True, text=True,
                            encoding='utf-8')
    if ok and result.returncode != 0:
        raise AssertionError(f'exit {result.returncode}: {result.stderr}{result.stdout}')
    return result


def add(home, slug='heredoc-blocked', symptom='heredoc BLOCKED in a headless turn', evidence='BLOCKED: ... heredoc'):
    return run('add', '--home', home, '--domain', 'hermes', '--slug', slug, '--title', 'Use a script file',
               '--symptom', symptom, '--evidence', evidence, '--body', 'Write the script with write_file, run it.',
               ok=False)


class Lessons(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_without_evidence_is_refused(self):
        self.assertNotEqual(add(self.home, evidence='').returncode, 0)

    def test_draft_is_not_found_until_accepted(self):
        self.assertEqual(add(self.home).returncode, 0)
        self.assertNotIn('heredoc-blocked', run('search', '--home', self.home, 'heredoc').stdout)
        run('accept', '--home', self.home, 'heredoc-blocked', '--sha', 'abc1234')
        self.assertIn('heredoc-blocked', run('search', '--home', self.home, 'heredoc').stdout)

    def test_accept_writes_index_line_and_verified(self):
        add(self.home)
        run('accept', '--home', self.home, 'heredoc-blocked', '--sha', 'abc1234')
        index = (self.home / 'INDEX.md').read_text(encoding='utf-8')
        self.assertIn('heredoc BLOCKED in a headless turn', index)
        self.assertIn('hermes/heredoc-blocked.md', index)
        self.assertIn('Verified: ', (self.home / 'hermes' / 'heredoc-blocked.md').read_text(encoding='utf-8'))

    def test_duplicate_slug_is_refused(self):
        add(self.home)
        run('accept', '--home', self.home, 'heredoc-blocked', '--sha', 'abc1234')
        self.assertNotEqual(add(self.home).returncode, 0)

    def test_retire_moves_file_and_drops_index_line(self):
        add(self.home)
        run('accept', '--home', self.home, 'heredoc-blocked', '--sha', 'abc1234')
        run('retire', '--home', self.home, 'heredoc-blocked', '--reason', 'guard fixed upstream')
        self.assertFalse((self.home / 'hermes' / 'heredoc-blocked.md').exists())
        retired = (self.home / 'retired' / 'heredoc-blocked.md').read_text(encoding='utf-8')
        self.assertIn('guard fixed upstream', retired)
        self.assertNotIn('heredoc-blocked', (self.home / 'INDEX.md').read_text(encoding='utf-8'))

    def test_index_uses_symptom_section_of_existing_lessons(self):
        (self.home / 'old.md').write_text('# Title of old\n\n## What happens\n\nx\n\n## Symptom\n\nCompiles in one '
                                          'assembly, fails in another.\n\n## Origin\n\ny\n', encoding='utf-8')
        run('index', '--home', self.home)
        self.assertIn('Compiles in one assembly, fails in another.', (self.home / 'INDEX.md').read_text(encoding='utf-8'))

    def test_index_falls_back_to_title(self):
        (self.home / 'plain.md').write_text('# A rule with no symptom section\n\n## The rule\n\nz\n', encoding='utf-8')
        run('index', '--home', self.home)
        self.assertIn('A rule with no symptom section', (self.home / 'INDEX.md').read_text(encoding='utf-8'))

    def test_check_flags_lesson_missing_from_index(self):
        add(self.home)
        run('accept', '--home', self.home, 'heredoc-blocked', '--sha', 'abc1234')
        (self.home / 'INDEX.md').write_text('# Lessons\n', encoding='utf-8')
        self.assertNotEqual(run('check', '--home', self.home, ok=False).returncode, 0)

    def test_index_embeds_into_skill_between_markers(self):
        skill = self.home / 'SKILL.md'
        skill.write_text('# skill\n\n<!-- lessons-index:start -->\nold\n<!-- lessons-index:end -->\n', encoding='utf-8')
        add(self.home)
        run('accept', '--home', self.home, 'heredoc-blocked', '--sha', 'abc1234', '--skill', skill)
        text = skill.read_text(encoding='utf-8')
        self.assertIn('heredoc BLOCKED in a headless turn', text)
        self.assertNotIn('\nold\n', text)

    def test_search_spans_several_homes(self):
        other = self.home / 'project'
        other.mkdir()
        (other / 'snow.md').write_text('# Snow under trees\n\n## Symptom\n\nSnow appears under trunks.\n',
                                       encoding='utf-8')
        out = run('search', '--home', self.home, '--home', other, 'snow trunks').stdout
        self.assertIn('snow.md', out)


if __name__ == '__main__':
    unittest.main()
