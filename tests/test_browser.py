"""Run with RUN_BROWSER_CHECKS=1; uses a fresh headless browser and local HTML only."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from browser_worker import Browser


@unittest.skipUnless(os.environ.get("RUN_BROWSER_CHECKS") == "1", "opt-in real browser check")
class BrowserCheck(unittest.TestCase):
    def test_fill_then_submit_uses_real_dom_and_reserves_once(self):
        from playwright.sync_api import sync_playwright

        with tempfile.TemporaryDirectory() as folder, sync_playwright() as pw:
            chrome = os.environ.get(
                "CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            )
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
            events = [json.loads(line) for line in (run / "events.jsonl").read_text().splitlines()]
            self.assertEqual(sum(e["kind"] == "action_error" for e in events), 1)
            native.close()


if __name__ == "__main__":
    unittest.main()
