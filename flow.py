"""Local workflow boundaries, spending ledger and CLI. No hosted model calls."""

import argparse
import errno
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def event(run, kind, **data):
    with (Path(run) / "events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(
            json.dumps(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "mono_s": time.monotonic(),
                    "kind": kind,
                    **data,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        stream.flush()
        os.fsync(stream.fileno())


def reserve_credit(path, cap, key, cost):
    """Reserve BEFORE a submit. A crash/uncertain click must never silently refund it."""
    if type(cost) is not int or cost <= 0 or type(cap) is not int or cap < cost:
        raise ValueError("credits must be positive integers within the cap")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("CREATE TABLE IF NOT EXISTS budget (cap INTEGER NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS spend (id TEXT PRIMARY KEY, credits INTEGER)")
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute("SELECT cap FROM budget").fetchone()
        if existing and existing[0] != cap:
            raise ValueError("existing budget cap cannot be reset")
        if not existing:
            db.execute("INSERT INTO budget VALUES (?)", (cap,))
        if db.execute("SELECT 1 FROM spend WHERE id=?", (key,)).fetchone():
            raise ValueError("submission already reserved; inspect Flow before retrying")
        total = db.execute("SELECT COALESCE(SUM(credits),0) FROM spend").fetchone()[0]
        if total + cost > cap:
            raise ValueError("credit cap reached")
        db.execute("INSERT INTO spend VALUES (?,?)", (key, cost))
        return total + cost


DENIED = re.compile(
    r"\b(delete|remove|bin|trash|publish|share|buy|upgrade|subscribe|purchase|billing|"
    r"sign.?out|log.?out)\b|ลบ|เผยแพร่|ซื้อ|ชำระ",
    re.I,
)
GENERATE = re.compile(
    r"\b(create|generate|generation|retry|regenerate|extend|upscale)\b|สร้าง|ลองอีก", re.I
)


def validate_task(task):
    if not isinstance(task, dict) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", task.get("id", "")):
        raise ValueError("task.id must be a short safe identifier")
    if not isinstance(task.get("goal"), str) or not 1 <= len(task["goal"]) <= 800:
        raise ValueError("goal must contain 1–800 characters")
    click, fields = task.get("click", []), task.get("type", {})
    if not isinstance(click, list) or not isinstance(fields, dict):
        raise ValueError("click must be an exact-name list; type must map field names to values")
    if len(click) + len(fields) > 48:
        raise ValueError("split large tasks into bounded subgoals")
    for name in [*click, *fields]:
        if not isinstance(name, str) or not name or len(name) > 200 or DENIED.search(name):
            raise ValueError("unsafe or invalid control name")
    if any(not isinstance(v, str) or not 1 <= len(v) <= 6000 for v in fields.values()):
        raise ValueError("provide literal field text, at most 6000 characters")
    submit = task.get("submit")
    if submit:
        if (
            not isinstance(submit, dict)
            or submit.get("name") not in click
            or type(submit.get("credits")) is not int
            or submit["credits"] < 1
            or not isinstance(submit.get("evidence"), str)
            or not submit["evidence"]
        ):
            raise ValueError("submit needs an allowed exact name, positive credits and UI evidence")
    for name in click:
        if GENERATE.search(name) and (not submit or name != submit["name"]):
            raise ValueError("generation control must be the accounted submit action")
    if not task.get("done_text") and not task.get("done_field") and not task.get("done_video"):
        raise ValueError("task needs an observable completion condition")
    if "done_field" in task and task["done_field"] not in fields:
        raise ValueError("done_field must reference a supplied text field")
    if "done_text" in task and (
        not isinstance(task["done_text"], str) or not 1 <= len(task["done_text"]) <= 500
    ):
        raise ValueError("done_text must be a short visible literal")
    if "done_video" in task and (type(task["done_video"]) is not int or task["done_video"] < 1):
        raise ValueError("done_video must be a positive count")


def validate_action(action, obs, task):
    if action.get("snapshot") != obs["snapshot"]:
        raise ValueError("stale snapshot; observe again")
    op = action.get("operation")
    if op in ("WAIT", "DONE", "BLOCKED"):
        return None
    if op not in ("CLICK", "TYPE_TEXT"):
        raise ValueError("unsupported operation")
    elements = [e for e in obs["elements"] if e["id"] == action.get("target")]
    if len(elements) != 1:
        raise ValueError("target not in current observation")
    el = elements[0]
    allowed = task.get("click", []) if op == "CLICK" else task.get("type", {})
    if el["name"] not in allowed or DENIED.search(el["name"]):
        raise ValueError("target outside the task allowlist")
    if op == "TYPE_TEXT" and not el["editable"]:
        raise ValueError("target is not editable")
    return el


def project_url(url):
    p = urlparse(url)
    if (
        p.scheme != "https"
        or p.hostname != "flow.google.com"
        or not re.fullmatch(r"/project/[A-Za-z0-9-]+/?", p.path)
        or p.username
        or p.password
        or p.port
    ):
        raise ValueError("use the exact https://flow.google.com/project/... URL")
    return url.split("?")[0].split("#")[0].rstrip("/")


@contextmanager
def run_lock(run):
    with (Path(run) / ".lock").open("a+b") as lock:
        if sys.platform == "win32":
            import msvcrt

            def acquire():
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)

            def release():
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire():
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release():
                fcntl.flock(lock, fcntl.LOCK_UN)

        lock.seek(0)
        try:
            acquire()
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise ValueError("another command is operating this run") from None
            raise
        try:
            yield
        finally:
            release()


def init_run(args):
    run = Path(args.run)
    url = project_url(args.url)
    if args.cap <= 0:
        raise ValueError("cap must be positive")
    run.mkdir(parents=True, exist_ok=False)
    write_json(
        run / "run.json",
        {
            "arm": args.arm,
            "brain": args.brain,
            "model_label": args.model_label,
            "pair": args.pair,
            "url": url,
            "budget": str(Path(args.budget).resolve()),
            "cap": args.cap,
            "started_mono_s": time.monotonic(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "running",
            "protocol": args.protocol,
        },
    )
    event(run, "start")
    return {"run": str(run), "status": "running"}


def probe(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    data = json.loads(result.stdout)
    video = next(s for s in data["streams"] if s["codec_type"] == "video")
    return {
        "duration_s": float(data["format"]["duration"]),
        "width": video["width"],
        "height": video["height"],
        "audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }


def assemble(run, shots):
    if len(shots) != 2:
        raise ValueError("exactly two 8-second shots are required")
    files = [Path(p).resolve() for p in shots]
    info = [probe(p) for p in files]
    for s in info:
        if not (
            7.8 <= s["duration_s"] <= 8.3 and s["width"] * 16 == s["height"] * 9 and s["audio"]
        ):
            raise ValueError("each shot must be approximately 8 seconds, 9:16, with audio")
    if (info[0]["width"], info[0]["height"]) != (info[1]["width"], info[1]["height"]):
        raise ValueError("shot resolutions must match")
    output = Path(run) / "final.mp4"
    if output.exists():
        raise ValueError("final.mp4 already exists; do not overwrite reviewed output")
    start = time.perf_counter()
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-n",
            "-i",
            str(files[0]),
            "-i",
            str(files[1]),
            "-filter_complex",
            "[0:v]setpts=PTS-STARTPTS[v0];[1:v]setpts=PTS-STARTPTS[v1];"
            "[0:a]asetpts=PTS-STARTPTS[a0];[1:a]asetpts=PTS-STARTPTS[a1];"
            "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
    )
    result = probe(output)
    if not 15.6 <= result["duration_s"] <= 16.6:
        raise ValueError("assembled clip has unexpected duration")
    event(run, "assemble", seconds=time.perf_counter() - start, media=result)
    return {"file": str(output.resolve()), **result, "visual_audio_review": "required"}


def finish(run, status, qc):
    cfg = read_json(Path(run) / "run.json")
    if status not in ("passed", "failed", "blocked", "pilot_downloaded"):
        raise ValueError("invalid final status")
    if cfg["status"] != "running":
        raise ValueError("run already finalized")
    if status == "pilot_downloaded":
        if cfg["arm"] != "pilot":
            raise ValueError("pilot_downloaded is only valid for the pilot arm")
        media = probe(Path(run) / "shot-1.mp4")
        if not (
            7.8 <= media["duration_s"] <= 8.3
            and media["audio"]
            and media["width"] * 16 == media["height"] * 9
        ):
            raise ValueError("pilot must contain an 8-second vertical video with audio")
        event(run, "pilot_download_verified", media=media, audiovisual_qc="not_verified")
    if status == "passed":
        if not qc or not Path(qc).is_file():
            raise ValueError("passed requires a completed human/ChatGPT audiovisual QC file")
        review = read_json(qc)
        required = ("product_matches", "no_false_claims", "thai_audio_correct", "no_broken_visuals")
        if any(review.get(k) is not True for k in required) or not review.get("reviewer"):
            raise ValueError("all audiovisual quality checks must pass")
        media = probe(Path(run) / "final.mp4")
        if not (
            15.6 <= media["duration_s"] <= 16.6
            and media["audio"]
            and media["width"] * 16 == media["height"] * 9
        ):
            raise ValueError("final video must be 16 seconds, vertical, with audio")
        write_json(Path(run) / "qc.json", review)
    cfg.update(status=status, elapsed_s=time.monotonic() - cfg["started_mono_s"])
    if cfg["elapsed_s"] < 0:
        raise ValueError("monotonic clock changed; timing unavailable")
    write_json(Path(run) / "run.json", cfg)
    event(run, "finish", status=status, elapsed_s=cfg["elapsed_s"])
    return {"status": status, "elapsed_s": cfg["elapsed_s"]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    browser = sub.add_parser("open-browser", help="open isolated Chrome on this operating system")
    browser.add_argument("--chrome", help="override the detected Chrome executable")
    browser.add_argument("--port", type=int, default=9223)
    m = sub.add_parser("model-check")
    m.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    m.add_argument("--output", default="runs/model-check.json")
    start = sub.add_parser("init")
    start.add_argument("run")
    start.add_argument("--url", required=True)
    start.add_argument("--arm", choices=["baseline", "hybrid", "pilot"], required=True)
    start.add_argument(
        "--brain", choices=["chatgpt-work-local", "codex-development", "human"], required=True
    )
    start.add_argument("--model-label", required=True)
    start.add_argument("--pair", type=int, default=0)
    start.add_argument("--protocol", default="mug-v1")
    start.add_argument("--cap", type=int, default=120)
    start.add_argument("--budget", default="runs/benchmark-budget.sqlite")
    for name in ["open-project", "observe", "step", "delegate", "wait-video", "download"]:
        cmd = sub.add_parser(name)
        cmd.add_argument("run")
        cmd.add_argument("--cdp", default="http://127.0.0.1:9223")
        if name in ("step", "delegate"):
            cmd.add_argument("--task", required=True)
        if name == "step":
            cmd.add_argument(
                "--action", required=True, help="JSON action file from current snapshot"
            )
        if name == "delegate":
            cmd.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
            cmd.add_argument("--steps", type=int, default=12)
        if name == "wait-video":
            cmd.add_argument("--seconds", type=int, default=45)
            cmd.add_argument(
                "--after", type=int, default=0, help="completed video tile count BEFORE submission"
            )
        if name == "download":
            cmd.add_argument("--name", required=True, help="exact visible download control name")
            cmd.add_argument("--output", required=True, help="basename inside the run directory")
    join = sub.add_parser("assemble")
    join.add_argument("run")
    join.add_argument("shots", nargs=2)
    end = sub.add_parser("finish")
    end.add_argument("run")
    end.add_argument(
        "--status", choices=["passed", "failed", "blocked", "pilot_downloaded"], required=True
    )
    end.add_argument("--qc")
    report = sub.add_parser("report")
    report.add_argument("runs", nargs="+")
    report.add_argument("--output", default="results/benchmark.json")
    args = p.parse_args()
    if args.command == "doctor":
        import importlib.metadata
        import platform

        from chrome_launcher import find_chrome

        try:
            chrome = find_chrome()
        except FileNotFoundError:
            chrome = None
        result = {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "chrome": chrome,
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "ffprobe": bool(shutil.which("ffprobe")),
            "packages": {
                n: importlib.metadata.version(n)
                for n in ["laya", "torch", "transformers", "playwright", "tiktoken"]
            },
        }
    elif args.command == "open-browser":
        from chrome_launcher import open_browser

        result = open_browser(args.chrome, args.port)
    elif args.command == "init":
        result = init_run(args)
    elif args.command == "model-check":
        from local_model import smoke

        result = smoke(args.device)
        write_json(args.output, result)
    elif args.command == "report":
        from benchmark import report_runs

        result = report_runs(args.runs)
        write_json(args.output, result)
    else:
        with run_lock(args.run):
            if args.command == "assemble":
                result = assemble(args.run, args.shots)
            elif args.command == "finish":
                result = finish(args.run, args.status, args.qc)
            else:
                from browser_worker import command

                result = command(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(
            json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(2)
