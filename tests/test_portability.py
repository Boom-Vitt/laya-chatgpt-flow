"""Native OS checks for Thai files, process locks and isolated browser startup."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from flow import run_lock

ROOT = Path(__file__).resolve().parents[1]


class PortabilityChecks(unittest.TestCase):
    def test_thai_json_and_events_do_not_depend_on_system_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run(
                [
                    sys.executable,
                    "-W",
                    "error::EncodingWarning",
                    "-c",
                    """
import sys
from pathlib import Path
from flow import event, read_json, write_json
root = Path(sys.argv[1])
write_json(root / 'task.json', {'prompt': '\u0e41\u0e01\u0e49\u0e27'})
assert read_json(root / 'task.json')['prompt'] == '\u0e41\u0e01\u0e49\u0e27'
event(root, 'test', text='\u0e41\u0e01\u0e49\u0e27')
assert '\u0e41\u0e01\u0e49\u0e27' in (root / 'events.jsonl').read_bytes().decode('utf-8')
""",
                    folder,
                ],
                cwd=ROOT,
                capture_output=True,
                env={**os.environ, "PYTHONWARNDEFAULTENCODING": "1"},
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))

    def test_run_lock_blocks_another_process_and_releases_after_error(self):
        child = """
import sys
from flow import run_lock
try:
    with run_lock(sys.argv[1]):
        pass
except ValueError:
    sys.exit(3)
"""
        with tempfile.TemporaryDirectory() as folder:

            def attempt():
                return subprocess.run([sys.executable, "-c", child, folder], cwd=ROOT).returncode

            with self.assertRaisesRegex(RuntimeError, "release"):
                with run_lock(folder):
                    self.assertEqual(attempt(), 3)
                    raise RuntimeError("release")
            self.assertEqual(attempt(), 0)

    def test_launcher_keeps_paths_with_spaces_and_non_ascii_as_single_arguments(self):
        from chrome_launcher import chrome_command, find_chrome

        with tempfile.TemporaryDirectory() as folder:
            executable = Path(folder) / "Browser with spaces"
            executable.touch()
            executable.chmod(0o755)
            self.assertEqual(find_chrome(str(executable)), str(executable.resolve()))
            profile = Path(folder) / "โปรไฟล์ ทดสอบ"
            command = chrome_command(str(executable), profile, 9321)
            self.assertEqual(command[0], str(executable))
            self.assertIn(f"--user-data-dir={profile.resolve()}", command)
            self.assertIn("--remote-debugging-address=127.0.0.1", command)
            self.assertIn("--remote-debugging-port=9321", command)
            with self.assertRaises(ValueError):
                chrome_command(str(executable), profile, 0)
            with self.assertRaises(FileNotFoundError):
                find_chrome(str(Path(folder) / "missing-browser"))
