# Product workflow

Read `.agents/skills/laya-chatgpt-flow/SKILL.md` when asked to make clips or run a comparison.
The intended thinker is **ChatGPT Desktop → Work locally**. Do not substitute Codex, a hosted model API, or automated ChatGPT web scraping. Development/debugging here is not a ChatGPT benchmark run.

Keep Google sign-in, raw browser logs, transcripts, model files and videos under ignored `runs/`. Never commit a browser profile, cookies, credentials, account screenshots or raw conversation exports.

The user ended this demonstration after one baseline/hybrid pair and declined quota monitoring or additional runs. Both approved final videos are explicitly authorized for public GitHub attachments; their URLs and hashes are in `assets/media.json`. Keep the original run files private and preserve the existing measurement limits. Do not restart the earlier three-pair plan without a new request.

Use `uv sync --locked`. Run `uv run python -m unittest discover -s tests -v` and `uv run ruff check .` after code changes. CI runs on Windows x64, Linux x64 and macOS ARM64. Set `RUN_BROWSER_CHECKS=1` and `RUN_MEDIA_CHECKS=1` using the current shell's syntax (see `docs/INSTALL.md`) to exercise a fresh Chrome/CDP session and FFmpeg with local test content. These checks never spend Flow credits and do not prove signed-in Flow compatibility on every OS. Keep UTF-8 file I/O and use `uv run python flow.py open-browser` on every platform.

Record unsuccessful attempts. A queued render is not a successful clip. A local test is not live Flow proof. Internal ChatGPT usage is unavailable here; never manufacture token/cost savings. No posting, basket linking, purchases or unbounded retrying.
