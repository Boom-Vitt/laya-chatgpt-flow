"""Open an isolated, loopback-only Chrome profile on Windows, macOS or Linux."""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def find_chrome(explicit=None):
    override = explicit or os.environ.get("CHROME_BIN")
    if override:
        path = Path(override).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path.resolve())
        found = shutil.which(override)
        if found:
            return found
        raise FileNotFoundError("Chrome executable not found; check --chrome or CHROME_BIN")
    candidates = []
    if sys.platform == "darwin":
        candidates = [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif sys.platform == "win32":
        candidates = [
            Path(os.environ[key]) / "Google/Chrome/Application/chrome.exe"
            for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")
            if os.environ.get(key)
        ]
    for path in candidates:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError("Install Google Chrome or set CHROME_BIN to its executable")


def chrome_command(executable, profile, port=9223):
    if not 1 <= port <= 65535:
        raise ValueError("debugging port must be between 1 and 65535")
    return [
        executable,
        f"--user-data-dir={Path(profile).resolve()}",
        "--remote-debugging-address=127.0.0.1",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://flow.google.com/",
    ]


def open_browser(explicit=None, port=9223):
    profile = Path(__file__).resolve().parent / "runs/browser-profile"
    command = chrome_command(find_chrome(explicit), profile, port)
    with socket.socket() as check:
        try:
            check.bind(("127.0.0.1", port))
        except OSError:
            raise ValueError(
                f"Port {port} is already in use. Keep using your existing test Chrome if it "
                "is the correct profile; otherwise close that test window before relaunching."
            ) from None
    profile.mkdir(parents=True, exist_ok=True)
    log_path = profile.parent / "chrome-launch.log"
    options = (
        {"creationflags": subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
        if sys.platform == "win32"
        else {"start_new_session": True}
    )
    with log_path.open("ab") as log:
        process = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, **options
        )
    cdp = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            with urlopen(cdp + "/json/version", timeout=1) as response:
                version = json.load(response)
            if version.get("webSocketDebuggerUrl"):
                return {"status": "ready", "cdp": cdp, "profile": str(profile)}
        except (URLError, OSError, ValueError):
            pass
        if process.poll() not in (None, 0):
            break
        time.sleep(0.2)
    raise ValueError(f"Chrome DevTools did not become ready; inspect {log_path}")
