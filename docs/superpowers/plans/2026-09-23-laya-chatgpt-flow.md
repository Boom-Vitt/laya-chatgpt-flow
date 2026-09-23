# Laya + ChatGPT Work → Google Flow

Goal: Build a runnable Thai-first repository. ChatGPT Desktop Work locally supplies reasoning and video prompts; local Laya v10 chooses browser actions. Finish at downloaded clips, never publish them.

Architecture: one Python CLI, Playwright attached to loopback Chrome, pinned local Laya checkpoint, shared observations/actions for both arms, JSONL evidence, FFmpeg assembly. A project skill tells ChatGPT when to delegate and when to recover. No hosted inference, OpenAI API, Codex backend, ChatGPT-web scraping, scheduler, or posting integration.

Tech stack: Python 3.12/uv, Laya 0.3.6, PyTorch, Playwright, tiktoken, FFmpeg. CPU first on this Mac; report actual hardware/device.

Approved specification: user confirmed “ตามนั้น” after choosing ChatGPT Work locally as entry point, Laya `cklxx/laya-browser` v10 (421M), a one-shot pilot, then one product × 3 runs × 2 arms. Each final clip joins two 8-second vertical shots. Verify Flow's live model/settings/price; initial benchmark budget 120 credits. No purchases or automatic posting.

- [x] Core: validated tasks/actions, durable spending reservations, bounded delegation and append-only evidence. Check invalid actions, repeated/no-progress actions and exhausted budgets.
- [x] Local model: pinned snapshot, stock CPU inference, operation/target decisions, real-model smoke evidence.
- [x] Browser: current visible control IDs, strict tab/domain scope, text supplied by thinker, bounded waits, actual download; fixture check then real Flow pilot.
- [x] Workflow: ChatGPT Work skill, sample factual product brief, setup/doctor, video concatenation with duration/audio verification.
- [ ] Benchmark: counterbalanced 3 pairs, visible-text token estimate with completeness/provenance, real wall time, failures and model/Flow time separately. Missing telemetry stays null. Export only sanitized aggregates.
- [ ] Verification/review: runnable checks, skill validation, final fresh review, public GitHub repo, report actual results and remaining gaps.

Acceptance: a passing fixture is not a Flow success; a Codex run is not a ChatGPT Work run; a video render is not a final inspected 16-second clip. No comparative savings claim until both real arms complete with comparable evidence. If ChatGPT Work integration needs a user action, complete all independent work first and describe the exact remaining step.

Execution evidence: 11 checks passed including fresh Chrome/local HTML and actual FFmpeg assembly. Real local Laya filled Flow and submitted one shot after live settings/price verification; download verified: 8.0s, 720x1280, audio stream present; audiovisual QC not verified. Fresh reviewer findings fixed and re-reviewed. Actual ChatGPT Work benchmark is pending and cannot be substituted with this Codex development task.
