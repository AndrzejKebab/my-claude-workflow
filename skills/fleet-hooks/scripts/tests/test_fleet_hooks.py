import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import fleet_hooks as fh  # noqa: E402

WALL = '# one\n# two\n# three\n# four\n'


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.state = self.dir / 'state.json'

    def pre(self, tool, session='s1', now=1000.0, **args):
        state = fh.State(self.state)  # a fresh load each call, as each hook run is its own process
        result = fh.pre_tool(tool, args, session, state, now)
        state.save(now)
        return result


class WholeFileReads(Base):
    def test_partial_read_of_agents_md_is_refused(self):
        self.assertEqual(self.pre('read_file', path='F:/x/AGENTS.md', offset=10)['action'], 'block')
        self.assertIsNone(self.pre('read_file', path='F:/x/AGENTS.md'))
        self.assertIsNone(self.pre('read_file', path='F:/x/README.md', limit=5))

    def test_head_of_context_md_is_refused(self):
        self.assertEqual(self.pre('terminal', command='head -40 Docs/CONTEXT.md')['action'], 'block')


class NoSpin(Base):
    def test_a_no_op_command_is_refused(self):
        self.assertEqual(self.pre('terminal', command='echo .')['action'], 'block')
        self.assertIsNone(self.pre('terminal', command='git status'))

    def test_the_same_command_seven_times_in_two_minutes_is_a_spin(self):
        results = [self.pre('terminal', command='git status', now=1000.0 + i) for i in range(7)]
        self.assertEqual([r and r['action'] for r in results], [None] * 6 + ['block'])
        self.assertIsNone(self.pre('terminal', command='git status', now=1500.0))


class CommentWall(Base):
    def test_a_new_wall_is_refused(self):
        target = self.dir / 'a.py'
        target.write_text('x = 1\n', encoding='utf-8')
        self.assertEqual(self.pre('write_file', path=str(target), content=WALL + 'x = 1\n')['action'], 'block')

    def test_a_wall_already_in_the_file_does_not_block_an_edit(self):
        target = self.dir / 'b.py'
        target.write_text(WALL + 'x = 1\n', encoding='utf-8')
        self.assertIsNone(self.pre('patch', path=str(target), old_string='x = 1', new_string='x = 2'))

    def test_a_patch_that_adds_a_wall_is_refused(self):
        target = self.dir / 'c.py'
        target.write_text('x = 1\n', encoding='utf-8')
        result = self.pre('patch', path=str(target), old_string='x = 1', new_string=WALL + 'x = 1')
        self.assertEqual(result['action'], 'block')

    def test_markdown_is_not_code(self):
        self.assertIsNone(self.pre('write_file', path=str(self.dir / 'n.md'), content=WALL))


class Fff(Base):
    def test_first_recursive_grep_points_at_fff_and_a_retry_passes(self):
        first = self.pre('terminal', command='grep -rn "ChunkMesh" Assets/')
        self.assertEqual(first['action'], 'block')
        self.assertIn('mcp_fff_grep', first['message'])
        self.assertIsNone(self.pre('terminal', command='grep -rn "ChunkMesh" Assets/', now=1010.0))

    def test_rg_and_search_files_are_nudged(self):
        self.assertEqual(self.pre('terminal', command='cd F:/x && rg Foo')['action'], 'block')
        self.assertEqual(self.pre('search_files', pattern='Foo', path='F:/x', session='s2')['action'], 'block')

    def test_a_repo_with_a_graph_is_pointed_at_graphify_first(self):
        repo = self.dir / 'game'
        (repo / 'graphify-out').mkdir(parents=True)
        (repo / 'graphify-out' / 'graph.json').write_text('{}', encoding='utf-8')
        message = self.pre('terminal', command='grep -rn Foo Assets/', workdir=str(repo / 'Assets'))['message']
        self.assertIn('graphify query', message)
        self.assertLess(message.index('graphify query'), message.index('mcp_fff_grep'))
        self.assertNotIn('graphify', self.pre('terminal', command='rg Foo', session='s3', workdir=str(self.dir))['message'])

    def test_grep_on_a_pipe_is_filtering_not_searching(self):
        self.assertIsNone(self.pre('terminal', command='git log --oneline | grep fix'))
        self.assertIsNone(self.pre('terminal', command='grep -c ok F:/x/build.log'))


class NewScript(Base):
    def test_a_new_script_in_scratch_is_sent_to_the_toolbox_first_then_passes(self):
        target = self.dir / '.scratch' / 'count_chunks.py'
        first = self.pre('write_file', path=str(target), content='print(1)\n')
        self.assertEqual(first['action'], 'block')
        self.assertIn('skill', first['message'])
        self.assertIsNone(self.pre('write_file', path=str(target), content='print(1)\n', now=1010.0))

    def test_an_existing_script_or_a_non_script_passes(self):
        (self.dir / '.scratch').mkdir()
        existing = self.dir / '.scratch' / 'old.py'
        existing.write_text('x = 1\n', encoding='utf-8')
        self.assertIsNone(self.pre('write_file', path=str(existing), content='x = 2\n'))
        self.assertIsNone(self.pre('write_file', path=str(self.dir / '.scratch' / 'notes.md'), content='x'))
        self.assertIsNone(self.pre('write_file', path=str(self.dir / 'Assets' / 'New.cs'), content='class A {}'))


class NoHedge(unittest.TestCase):
    def test_trailing_offer_keeps_the_bot_going(self):
        result = fh.pre_verify('Fixed the mesh seam. Want me to also run the tests?')
        self.assertEqual(result['action'], 'continue')
        self.assertIn('want me to', result['message'])

    def test_a_plain_report_finishes(self):
        self.assertIsNone(fh.pre_verify('Fixed the mesh seam; 42 tests pass.'))


class Wire(Base):
    def run_hook(self, event, payload):
        out = subprocess.run([sys.executable, str(HERE / 'fleet_hooks.py'), event, '--state', str(self.state)],
                             input=json.dumps(payload), capture_output=True, text=True, check=True)
        return json.loads(out.stdout) if out.stdout.strip() else None

    def test_pre_tool_call_payload(self):
        result = self.run_hook('pre-tool', {'tool_name': 'terminal', 'tool_input': {'command': 'echo .'},
                                            'session_id': 's'})
        self.assertEqual(result['action'], 'block')

    def test_pre_verify_payload(self):
        result = self.run_hook('pre-verify', {'extra': {'final_response': 'Done. Shall I push it?'}})
        self.assertEqual(result['action'], 'continue')


if __name__ == '__main__':
    unittest.main()
