"""Opt-in FFmpeg pipeline check; generated test signals are never benchmark clips."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from flow import assemble


@unittest.skipUnless(os.environ.get("RUN_MEDIA_CHECKS") == "1", "opt-in FFmpeg check")
class MediaCheck(unittest.TestCase):
    def test_two_audio_shots_join_to_sixteen_seconds_without_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "คลิป ทดสอบ"
            root.mkdir()
            shots = []
            for index, color in enumerate(("red", "blue")):
                path = root / f"shot-{index}.mp4"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-nostdin",
                        "-v",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        f"color={color}:s=90x160:r=10:d=8",
                        "-f",
                        "lavfi",
                        "-i",
                        "sine=frequency=440:duration=8",
                        "-c:v",
                        "libx264",
                        "-c:a",
                        "aac",
                        "-shortest",
                        str(path),
                    ],
                    check=True,
                )
                shots.append(path)
            result = assemble(root, shots)
            self.assertAlmostEqual(result["duration_s"], 16, delta=0.1)
            self.assertEqual((result["width"], result["height"]), (90, 160))
            self.assertTrue(result["audio"])
            with self.assertRaisesRegex(ValueError, "already exists"):
                assemble(root, shots)


if __name__ == "__main__":
    unittest.main()
