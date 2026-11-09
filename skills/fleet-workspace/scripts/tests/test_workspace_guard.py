import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import workspace_guard as wg  # noqa: E402

HOME = 'C:/Users/me'
RULES = wg.Rules(roots=['F:/Programowanie', 'F:/Unity'], home=HOME, scratch='F:/Unity/Projects/Game-worker-1/.scratch',
                 read_only=[f'{HOME}/AppData/Local/Unity', 'C:/Program Files'], drives={'C', 'D', 'E', 'F'})


def check(tool, **args):
    return wg.verdict(tool, args, RULES)


class Terminal(unittest.TestCase):
    def blocked(self, command, **extra):
        result = check('terminal', command=command, workdir='F:/Unity/Projects/Game', **extra)
        return bool(result) and result['action'] == 'block'

    def test_work_folders_pass(self):
        self.assertFalse(self.blocked('cd F:/Unity/Projects/Game && git status > .scratch/s.txt'))
        self.assertFalse(self.blocked('python "F:\\Programowanie\\tool.py" --out F:/Unity/x/.scratch/r.json'))
        self.assertFalse(self.blocked('cd /f/Unity/Projects/Game && ls'))

    def test_other_drives_are_refused(self):
        self.assertTrue(self.blocked('python x.py > C:/Users/me/AppData/Local/Temp/out.txt'))
        self.assertTrue(self.blocked('ls "E:/SteamLibrary/steamapps/common"'))
        self.assertTrue(self.blocked('cp a D:\\backup\\a'))
        self.assertTrue(self.blocked('cat /c/Users/me/Desktop/notes.txt'))

    def test_f_outside_the_work_folders_is_refused(self):
        self.assertTrue(self.blocked('python probe.py > F:/tmp/probe.txt'))

    def test_posix_tmp_is_refused(self):
        self.assertTrue(self.blocked('python probe.py --out /tmp/probe.txt'))
        self.assertFalse(self.blocked('python probe.py --out "$TMPDIR/probe.txt"'))

    def test_home_shortcuts_are_expanded(self):
        self.assertTrue(self.blocked('ls ~/Downloads'))
        self.assertTrue(self.blocked('ls "$USERPROFILE/Pictures"'))
        self.assertFalse(self.blocked('"$LOCALAPPDATA/Unity/bin/unity.exe" --version'))

    def test_read_only_tools_and_logs_pass(self):
        self.assertFalse(self.blocked('tail -50 "C:/Users/me/AppData/Local/Unity/Editor/Editor.log"'))
        self.assertFalse(self.blocked('"C:/Program Files/Unity/Hub/Editor/7000/Editor/Unity.exe" -batchmode'))

    def test_urls_and_device_paths_are_not_paths(self):
        self.assertFalse(self.blocked('gh api https://api.github.com/repos/x/c/y && ls 2>/dev/null'))

    def test_sed_and_awk_syntax_is_not_a_path(self):
        self.assertFalse(self.blocked("sed 's/\\n:/g' f.txt; ps -W | awk '$NF ~ /Unity.exe$/'"))
        self.assertFalse(self.blocked("ls x | sed 's/^/-r:/'; echo s:/n/n"))

    def test_escaped_spaces_stay_in_the_path(self):
        self.assertFalse(self.blocked('C:/Program\\ Files/Git/bin/git.exe --version'))
        self.assertTrue(self.blocked('ls C:/Users/me/My\\ Documents'))

    def test_no_workdir_runs_in_scratch(self):
        result = check('terminal', command='python F:/Programowanie/tool.py')
        self.assertEqual(result, {'action': 'modify', 'args': {'workdir': RULES.scratch}})

    def test_workdir_outside_is_refused(self):
        result = check('terminal', command='ls', workdir='C:/Users/me')
        self.assertEqual(result['action'], 'block')


class Files(unittest.TestCase):
    def test_writes_only_in_work_folders(self):
        self.assertIsNone(check('write_file', path='F:/Unity/Projects/Game/Assets/A.cs', content='x'))
        self.assertEqual(check('write_file', path='C:/Users/me/AppData/Local/Temp/p.py', content='x')['action'], 'block')
        self.assertEqual(check('patch', path='C:/Users/me/AppData/Local/Unity/Editor/x.txt', old_string='a',
                               new_string='b')['action'], 'block')

    def test_v4a_patch_files_are_checked(self):
        patch = '*** Begin Patch\n*** Add File: C:/tmp/x.py\n+print(1)\n*** End Patch'
        self.assertEqual(check('patch', mode='patch', patch=patch)['action'], 'block')

    def test_reads_allow_the_read_only_list(self):
        self.assertIsNone(check('read_file', path='C:/Users/me/AppData/Local/Unity/Editor/Editor.log'))
        self.assertEqual(check('read_file', path='C:/Users/me/Desktop/a.txt')['action'], 'block')
        self.assertEqual(check('vision_analyze', image_url='E:/shots/a.png', question='?')['action'], 'block')
        self.assertIsNone(check('vision_analyze', image_url='https://example.com/a.png', question='?'))

    def test_relative_paths_resolve_against_the_session_folder(self):
        inside = wg.Rules(**{**RULES.__dict__, 'cwd': 'F:/Unity/Projects/Game'})
        self.assertIsNone(wg.verdict('write_file', {'path': '.scratch/out.txt', 'content': 'x'}, inside))
        outside = wg.Rules(**{**RULES.__dict__, 'cwd': HOME})
        self.assertEqual(wg.verdict('write_file', {'path': 'notes.md', 'content': 'x'}, outside)['action'], 'block')
        self.assertEqual(wg.verdict('read_file', {'path': 'Desktop/a.txt'}, outside)['action'], 'block')


class SessionFolder(unittest.TestCase):
    def test_a_continuation_takes_its_parent_sessions_folder(self):
        import sqlite3
        db_path = Path(tempfile.mkdtemp()) / 'state.db'
        db = sqlite3.connect(db_path)
        db.execute('create table sessions (id text, cwd text, parent_session_id text)')
        db.executemany('insert into sessions values (?,?,?)', [('a', 'C:\\Users\\me', None), ('b', None, 'a')])
        db.commit()
        db.close()
        self.assertEqual(wg.session_cwd(db_path, 'b'), 'C:/Users/me')
        self.assertEqual(wg.session_cwd(db_path, 'missing'), '')


class Hook(unittest.TestCase):
    def test_stdin_protocol_and_log(self):
        log = Path(tempfile.mkdtemp()) / 'guard.jsonl'
        payload = {'hook_event_name': 'pre_tool_call', 'tool_name': 'write_file',
                   'tool_input': {'path': 'D:/x.txt', 'content': 'x'}, 'cwd': 'F:/Unity'}
        out = subprocess.run([sys.executable, str(HERE / 'workspace_guard.py'), '--root', 'F:/Programowanie',
                              '--root', 'F:/Unity', '--scratch', 'F:/Unity/s', '--home', HOME, '--log', str(log)],
                             input=json.dumps(payload), capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(out.stdout)['action'], 'block')
        self.assertEqual(json.loads(log.read_text())['tool'], 'write_file')


if __name__ == '__main__':
    unittest.main()
