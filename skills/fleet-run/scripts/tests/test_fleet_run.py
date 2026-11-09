import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parents[1]
RUNNER = HERE / 'fleet_run.py'
PY = sys.executable

# A child that starts a grandchild sleeping long, prints the grandchild's pid, then does what argv[1] says.
CHILD = r'''
import subprocess, sys, time
grand = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
print("GRAND", grand.pid, flush=True)
mode = sys.argv[1]
if mode == "exit3":
    grand.kill(); sys.exit(3)
if mode == "sleep":
    time.sleep(60)
if mode == "eat":
    block = bytearray(300 * 2**20); time.sleep(60)
if mode == "storm":
    for _ in range(8):
        subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"]); time.sleep(0.3)
    time.sleep(60)
'''


class FleetRun(unittest.TestCase):
    def setUp(self):
        self.data = Path(tempfile.mkdtemp())
        self.child = self.data / 'child.py'
        self.child.write_text(CHILD, encoding='utf-8')

    def run_tool(self, mode, *flags, timeout=60):
        command = [PY, str(RUNNER), '--data', str(self.data), '--tool', 'child', *flags, '--', PY, str(self.child), mode]
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout)

    def grand_pid(self, out):
        return next(int(line.split()[1]) for line in out.splitlines() if line.startswith('GRAND'))

    def assert_no_orphan(self, out):
        pid = self.grand_pid(out)
        deadline = time.time() + 5
        while time.time() < deadline and psutil.pid_exists(pid):
            time.sleep(0.2)
        self.assertFalse(psutil.pid_exists(pid), 'the grandchild outlived the run')

    def last_log(self):
        return json.loads((self.data / 'runs.jsonl').read_text(encoding='utf-8').splitlines()[-1])

    def test_finished_passes_the_exit_code_through(self):
        result = self.run_tool('exit3')
        self.assertEqual(result.returncode, 3)
        self.assertIn('[fleet_run] finished: exit 3', result.stdout)
        self.assertEqual(self.last_log()['reason'], 'finished')

    def test_deadline_stops_the_whole_tree(self):
        result = self.run_tool('sleep', '--deadline', '3')
        self.assertEqual(result.returncode, 124)
        self.assertIn('[fleet_run] stopped: deadline', result.stdout)
        self.assert_no_orphan(result.stdout)

    def test_memory_cap_stops_the_whole_tree(self):
        result = self.run_tool('eat', '--tree-cap-gib', '0.2', '--interval', '0.3')
        self.assertEqual(result.returncode, 9)
        self.assertIn('[fleet_run] stopped: memory cap', result.stdout)
        self.assert_no_orphan(result.stdout)

    def test_spawn_storm_stops_the_whole_tree(self):
        result = self.run_tool('storm', '--storm-names', 'python.exe', '--storm-count', '5', '--interval', '0.2')
        self.assertEqual(result.returncode, 125)
        self.assertIn('[fleet_run] stopped: spawn storm', result.stdout)
        self.assert_no_orphan(result.stdout)

    def test_stop_ends_only_registered_runs(self):
        outcome = {}
        thread = threading.Thread(target=lambda: outcome.setdefault('r', self.run_tool('sleep')))
        thread.start()
        for _ in range(50):
            if list((self.data / 'runs').glob('*.json')):
                break
            time.sleep(0.2)
        stop = subprocess.run([PY, str(RUNNER), 'stop', '--data', str(self.data), '--all'], capture_output=True,
                              text=True, timeout=30)
        self.assertIn('stopping 1 run', stop.stdout)
        thread.join(60)
        result = outcome['r']
        self.assertEqual(result.returncode, 143)
        self.assertIn('[fleet_run] stopped: stopped by owner', result.stdout)
        self.assert_no_orphan(result.stdout)
        self.assertEqual(list((self.data / 'runs').glob('*.json')), [])


if __name__ == '__main__':
    unittest.main()
