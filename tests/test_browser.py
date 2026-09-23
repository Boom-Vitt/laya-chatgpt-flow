"""Run with RUN_BROWSER_CHECKS=1; uses a fresh headless browser and local HTML only."""

import json
import os
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from browser_worker import Browser
from chrome_launcher import chrome_command, find_chrome


@unittest.skipUnless(os.environ.get("RUN_BROWSER_CHECKS") == "1", "opt-in real browser check")
class BrowserCheck(unittest.TestCase):
    def test_launcher_arguments_start_a_real_loopback_cdp_browser(self):
        from playwright.sync_api import sync_playwright

        with tempfile.TemporaryDirectory() as folder, socket.socket() as port_socket:
            port_socket.bind(("127.0.0.1", 0))
            port = port_socket.getsockname()[1]
            port_socket.close()
            profile = Path(folder) / "Chrome โปรไฟล์ทดสอบ"
            command = chrome_command(find_chrome(), profile, port)
            # A blank headless page keeps this check independent of Google and user accounts.
            command[-1:] = ["--headless=new", "about:blank"]
            process = subprocess.Popen(
                command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            try:
                endpoint = f"http://127.0.0.1:{port}"
                deadline = time.monotonic() + 15
                while True:
                    try:
                        with urlopen(endpoint + "/json/version", timeout=1) as response:
                            self.assertIn("webSocketDebuggerUrl", json.load(response))
                        break
                    except (URLError, OSError):
                        if time.monotonic() >= deadline or process.poll() is not None:
                            self.fail("Chrome did not expose its loopback DevTools endpoint")
                        time.sleep(0.1)
                with sync_playwright() as pw:
                    browser = pw.chromium.connect_over_cdp(endpoint)
                    page = browser.contexts[0].new_page()
                    page.set_content("<h1>พร้อมใช้งาน</h1>")
                    self.assertEqual(page.locator("h1").inner_text(), "พร้อมใช้งาน")
                    browser.new_browser_cdp_session().send("Browser.close")
                process.wait(timeout=10)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)

    def test_fill_then_submit_uses_real_dom_and_reserves_once(self):
        from playwright.sync_api import sync_playwright

        with tempfile.TemporaryDirectory() as folder, sync_playwright() as pw:
            chrome = find_chrome()
            native = pw.chromium.launch(executable_path=chrome, headless=True)
            page = native.new_page()
            url = "https://flow.google.com/project/local-fixture"
            page.route(
                "**/*",
                lambda route: route.fulfill(
                    body="""
              <title>Local fixture</title><textarea aria-label="Video prompt"
              oninput="document.querySelector('button').disabled=!this.value"></textarea>
              <button aria-label="Start generation" disabled
              onclick="document.querySelector('#status').textContent='Rendering requested';document.querySelector('#result').hidden=false">Create</button>
              <div id="status">Not started</div>
              <div id="result" hidden><flow-grid-tile-container aria-label="Mug clip">
                <img width="10" height="10" alt="Generated video thumbnail">
              </flow-grid-tile-container></div>""",
                    content_type="text/html",
                ),
            )
            page.goto(url)
            # Test utility: inject our local page without connecting to the user's browser.
            browser = object.__new__(Browser)
            browser.root, browser.page, browser.handles = url, page, {}
            run = Path(folder)
            cfg = {"budget": str(run / "budget.sqlite"), "cap": 10}
            task = {
                "id": "one",
                "goal": "Fill the prompt then create one video",
                "click": ["Start generation"],
                "type": {"Video prompt": "A ceramic mug."},
                "done_text": "Rendering requested",
                "submit": {"name": "Start generation", "credits": 10, "evidence": "10 credits"},
            }
            obs = browser.observe()
            self.assertEqual(obs["video_tiles"], 0)
            self.assertEqual([e["name"] for e in obs["elements"]], ["Video prompt"])
            after = browser.act(
                {"snapshot": obs["snapshot"], "operation": "TYPE_TEXT", "target": "0"},
                task,
                run,
                cfg,
            )
            self.assertEqual(after["elements"][0]["value"], "A ceramic mug.")
            after = browser.act(
                {"snapshot": after["snapshot"], "operation": "CLICK", "target": "1"}, task, run, cfg
            )
            self.assertIn("Rendering requested", after["text"])
            self.assertEqual(after["video_tiles"], 1)
            self.assertIn("Mug clip", [e["name"] for e in after["elements"]])
            self.assertFalse(browser.done(task, after))
            with self.assertRaisesRegex(ValueError, "already reserved"):
                browser.act(
                    {"snapshot": after["snapshot"], "operation": "CLICK", "target": "1"},
                    task,
                    run,
                    cfg,
                )
            events = [
                json.loads(line)
                for line in (run / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(sum(e["kind"] == "action_error" for e in events), 1)
            native.close()


if __name__ == "__main__":
    unittest.main()
