"""One project tab, observed controls only, identical browser primitives for both arms."""

import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from flow import event, project_url, read_json, reserve_credit, validate_action, validate_task

CONTROLS = 'button,a[href],input,textarea,select,[contenteditable="true"],[role="button"],[role="tab"],[role="radio"],[role="menuitem"],[role="option"],[role="checkbox"],[role="switch"],flow-grid-tile-container[aria-label]'
DESCRIBE = """e => {
 const r=e.getBoundingClientRect(), s=getComputedStyle(e);
 if (!r.width || !r.height || s.visibility==='hidden' || s.display==='none' ||
     e.closest('[inert],[aria-hidden="true"]') || e.type==='password' || e.type==='hidden') return null;
 const name=e.getAttribute('aria-label') || [...(e.labels||[])].map(x=>x.innerText).join(' ') ||
   e.getAttribute('placeholder') || e.getAttribute('data-placeholder') ||
   e.getAttribute('title') || (e.isContentEditable ? 'Video prompt' : e.innerText) || '';
 return {name:name.trim().replace(/\\s+/g,' ').slice(0,200),
 role:e.getAttribute('role') || ({BUTTON:'button',A:'link',INPUT:'textbox',TEXTAREA:'textbox',
 SELECT:'combobox'}[e.tagName]) || (e.isContentEditable?'textbox':'control'),
 editable:e.isContentEditable || ['TEXTAREA','INPUT'].includes(e.tagName),
 value: e.isContentEditable ? e.innerText : (e.value || ''),
 disabled:e.disabled || e.getAttribute('aria-disabled')==='true',
 checked:e.getAttribute('aria-checked'), selected:e.getAttribute('aria-selected'),
 expanded:e.getAttribute('aria-expanded')};
}"""


def same_project(url, root):
    p, base = urlparse(url), urlparse(root)
    return (
        p.scheme == base.scheme
        and p.netloc == base.netloc
        and bool(
            re.fullmatch(re.escape(base.path.rstrip("/")) + r"(?:/edit/[A-Za-z0-9-]+)?/?", p.path)
        )
    )


class Browser:
    def __init__(self, playwright, cdp, url, open_tab=False):
        endpoint = urlparse(cdp)
        if endpoint.scheme != "http" or endpoint.hostname not in ("127.0.0.1", "localhost"):
            raise ValueError("CDP must be HTTP on loopback; never expose it to the network")
        self.root = project_url(url)
        self.browser = playwright.chromium.connect_over_cdp(cdp)
        matches = [
            p for c in self.browser.contexts for p in c.pages if same_project(p.url, self.root)
        ]
        if not matches and open_tab:
            page = self.browser.contexts[0].new_page()
            page.goto(self.root, wait_until="domcontentloaded")
            matches = [page]
        if len(matches) != 1:
            raise ValueError("open exactly one matching Flow project tab in this Chrome profile")
        self.page = matches[0]
        self.page.set_default_timeout(5000)
        self.handles = {}

    def observe(self):
        if not same_project(self.page.url, self.root):
            raise ValueError("tab left the selected project; human/ChatGPT recovery required")
        elements = []
        self.handles = {}
        for handle in self.page.locator(CONTROLS).element_handles():
            data = handle.evaluate(DESCRIBE)
            if data and data["name"] and not data["disabled"]:
                key = str(len(elements))
                data["id"] = key
                elements.append(data)
                self.handles[key] = handle
        text = self.page.locator("body").inner_text()
        # Account menus are never needed. Keep observations local; do not publish raw screenshots/logs.
        obs = {
            "url": self.page.url,
            "title": self.page.title(),
            "text": text[:6000],
            "elements": elements,
            "video_tiles": self.page.locator(
                'flow-grid-tile-container img[alt="Generated video thumbnail"]'
            ).evaluate_all(
                "es => es.filter(e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden').length"
            ),
            "videos": self.page.locator("video").evaluate_all(
                "vs => vs.map(v=>({ready:v.readyState>=2,duration:Number.isFinite(v.duration)?v.duration:null}))"
            ),
        }
        obs["snapshot"] = hashlib.sha256(json.dumps(obs, sort_keys=True).encode()).hexdigest()[:16]
        return obs

    def done(self, task, obs):
        # Submission tasks only return 'submitted' after the actual click.
        # Existing text/media must never skip a new submission.
        if task.get("submit"):
            return False
        conditions = []
        if task.get("done_text"):
            conditions.append(task["done_text"] in obs["text"])
        if task.get("done_field"):
            name = task["done_field"]
            conditions.append(
                any(
                    e["name"] == name
                    and e.get("value", "").strip() == task["type"].get(name, "").strip()
                    for e in obs["elements"]
                )
            )
        if task.get("done_video"):
            conditions.append(sum(v["ready"] for v in obs["videos"]) >= task["done_video"])
        return bool(conditions) and all(conditions)

    def act(self, action, task, run, cfg):
        try:
            return self._act(action, task, run, cfg)
        except Exception as error:
            event(run, "action_error", task=task["id"], error=str(error))
            raise

    def _act(self, action, task, run, cfg):
        obs = self.observe()
        target = validate_action(action, obs, task)
        op = action["operation"]
        start = time.perf_counter()
        if op == "DONE":
            if not self.done(task, obs):
                raise ValueError("Laya claimed DONE without observable evidence")
        elif op == "BLOCKED":
            raise ValueError("decision maker requested reasoning")
        elif op == "WAIT":
            self.page.wait_for_timeout(1500)
        elif op == "TYPE_TEXT":
            self.handles[target["id"]].fill(task["type"][target["name"]])
        elif op == "CLICK":
            submit = task.get("submit")
            if submit and target["name"] == submit["name"]:
                for name, value in task.get("type", {}).items():
                    if not any(
                        e["name"] == name and e.get("value", "").strip() == value.strip()
                        for e in obs["elements"]
                    ):
                        raise ValueError("submit blocked: required field is not filled")
                total = reserve_credit(
                    cfg["budget"],
                    cfg["cap"],
                    str(Path(run).resolve()) + "/" + task["id"],
                    submit["credits"],
                )
                event(
                    run,
                    "credit_reserved",
                    task=task["id"],
                    credits=submit["credits"],
                    total=total,
                    price_evidence=submit["evidence"],
                )
            self.handles[target["id"]].click()
        event(
            run,
            "action",
            task=task["id"],
            operation=op,
            name=target["name"] if target else None,
            seconds=time.perf_counter() - start,
        )
        self.page.wait_for_timeout(400)
        return self.observe()


def delegate(browser, task, run, cfg, device, steps):
    from local_model import MODEL, REVISION, LocalLaya

    if not 1 <= steps <= 30:
        raise ValueError("steps must be between 1 and 30")
    if cfg["arm"] == "baseline":
        raise ValueError("baseline must not call Laya")
    model = LocalLaya(device)
    event(
        run, "model_load", seconds=model.load_s, device=model.device, model=MODEL, revision=REVISION
    )
    recent, failures, stagnant = [], 0, 0
    obs = browser.observe()
    for _ in range(steps):
        if browser.done(task, obs):
            event(run, "task_complete", task=task["id"])
            return {"status": "task_complete", "task": task["id"], "actions": recent}
        try:
            stage = "model"
            decision = model.choose(obs, task, recent)
            event(run, "laya_decision", task=task["id"], **decision)
            before = obs["snapshot"]
            stage = "action"
            after = browser.act(decision, task, run, cfg)
            recent.append({"operation": decision["operation"], "target": decision["target"]})
            submitted_target = next(
                (e for e in obs["elements"] if e["id"] == decision["target"]), {}
            )
            if decision["operation"] == "CLICK" and submitted_target.get("name") == (
                task.get("submit") or {}
            ).get("name"):
                return {
                    "status": "submitted",
                    "task": task["id"],
                    "actions": recent,
                    "video_tiles_before_submit": obs["video_tiles"],
                    "next": "Use wait-video; submission is not render completion.",
                }
            stagnant = stagnant + 1 if after["snapshot"] == before else 0
            obs, failures = after, 0
            if stagnant >= 2:
                raise ValueError("two consecutive actions made no observable progress")
        except Exception as error:
            failures += 1
            if stage == "model":
                event(run, "model_error", task=task["id"], error=str(error))
            recent.append({"error": str(error)[:200]})
            obs = browser.observe()
            if failures >= 2 or stagnant >= 2:
                break
    if browser.done(task, obs):
        event(run, "task_complete", task=task["id"])
        return {"status": "task_complete", "task": task["id"], "actions": recent}
    event(run, "needs_reasoning", task=task["id"])
    return {
        "status": "needs_reasoning",
        "task": task["id"],
        "recent": recent[-4:],
        "observation": obs,
    }


def command(args):
    from playwright.sync_api import sync_playwright

    run = Path(args.run)
    cfg = read_json(run / "run.json")
    if cfg["status"] != "running":
        raise ValueError("run already finalized")
    with sync_playwright() as pw:
        browser = Browser(pw, args.cdp, cfg["url"], open_tab=args.command == "open-project")
        # Exiting Playwright disconnects; never browser.close() the user's Chrome.
        if args.command in ("observe", "open-project"):
            obs = browser.observe()
            browser.page.screenshot(path=str(run / "latest.png"))
            event(run, "observation", snapshot=obs["snapshot"])
            return obs
        if args.command in ("step", "delegate"):
            task = read_json(args.task)
            validate_task(task)
            event(run, "task", task=task)
            if args.command == "delegate":
                return delegate(browser, task, run, cfg, args.device, args.steps)
            action = read_json(args.action)
            result = browser.act(action, task, run, cfg)
            event(
                run, "chatgpt_step" if cfg["brain"] == "chatgpt-work-local" else "development_step"
            )
            return result
        if args.command == "wait-video":
            if not 1 <= args.seconds <= 60 or args.after < 0:
                raise ValueError("wait between 1 and 60 seconds per call")
            start = time.perf_counter()
            while time.perf_counter() - start < args.seconds:
                obs = browser.observe()
                if obs["video_tiles"] > args.after:
                    event(run, "flow_wait", seconds=time.perf_counter() - start)
                    return {
                        "status": "result_visible",
                        "video_tiles": obs["video_tiles"],
                        "next": "Open the new tile and download it; a thumbnail is not file verification.",
                    }
                browser.page.wait_for_timeout(2000)
            event(run, "flow_wait", seconds=time.perf_counter() - start)
            return {"status": "still_waiting", "text": obs["text"][-2000:]}
        if args.command == "download":
            if not re.fullmatch(r"[A-Za-z0-9_-]+\.mp4", args.output):
                raise ValueError("output must be a simple .mp4 filename")
            output = run / args.output
            if output.exists():
                raise ValueError("download output already exists")
            obs = browser.observe()
            matches = [e for e in obs["elements"] if e["name"] == args.name]
            if len(matches) != 1 or not re.search(r"download|720p|original", args.name, re.I):
                raise ValueError("select one observed free/original download control")
            if re.search(r"upscale|1080|4k|credit", args.name, re.I):
                raise ValueError("paid upscaling is outside this download command")
            start = time.perf_counter()
            with browser.page.expect_download(timeout=60000) as info:
                browser.handles[matches[0]["id"]].click()
            info.value.save_as(output)
            from flow import probe

            media = probe(output)
            event(run, "download", seconds=time.perf_counter() - start, media=media)
            return {"file": str(output.resolve()), **media}
