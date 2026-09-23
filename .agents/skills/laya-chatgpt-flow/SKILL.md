---
name: laya-chatgpt-flow
description: Create product clips in Google Flow from ChatGPT Desktop Work locally, with optional local Laya browser decisions and evidence-based comparison. Use for Laya + ChatGPT Flow video tasks; never for auto-posting or hosted inference.
---

# Laya + ChatGPT → Flow

Use **ChatGPT Desktop / Work locally** as the thinker. This skill calls Python locally; it does not connect a plain ChatGPT web chat to the computer. For development in another host, label runs `codex-development` or `human`; never count them as ChatGPT Work results.

Find the repository root containing `flow.py` (three parents above this skill directory). Run all commands from that root. Read `docs/INSTALL.md` for Windows/Linux/macOS setup, `docs/WORKFLOW.md` for the exact CLI and `docs/BENCHMARK.md` before comparison runs. Use the user's native shell; Bash environment assignments and line continuations do not work in PowerShell. Write task/action JSON as UTF-8 (the `flow.write_json` helper does this). Keep Chrome and Python in the same OS environment.

## Work

1. Read the user's brief. If no product is supplied, use `examples/product.md`, clearly a fictional mug. Write two 8-second prompts and exact Thai dialogue; never invent product specifications. In benchmark mode freeze the same prompts before the user-requested runs. The published one-pair demonstration is complete; do not resume its old six-run plan.
2. Confirm local tools with `uv sync --locked` and `uv run python flow.py doctor`. Open the dedicated Chrome profile with `uv run python flow.py open-browser`; user signs in to Flow. Do not reuse/copy everyday cookies or expose the debugger outside loopback. Use the current visible Flow project URL. CPU is the cross-platform default; no GPU is required.
3. Start a run with the actual host/model label and shared budget before planning/execution being measured. Read the Flow UI with native browser tools or `observe`. Verify Veo 3.1 Lite, 720p, 8s, 9:16, x1, Agent off, and displayed credits. Prices are live; do not infer them from the example file. Configure the UI with ordinary visible controls. If native setup was needed, retain those calls in the transcript and elapsed time.
4. Prepare a task JSON from **observed exact control names**. Laya is a choice model; supply literal field values. Allow only controls needed for the subgoal, with an observable done condition. Put the full prompt in `type`, not the short English goal. Use one compound task for fill + submit when it works; a split fill/submit is a recovery and must be reported consistently. Both arms have the same primitives and prerequisite guards.
5. Hybrid: call `uv run python flow.py delegate RUN --task TASK.json`. Laya loads once per delegation and chooses several operations locally. Do not read its per-step local log back into ChatGPT unless diagnosing a failure. Baseline: call `observe`, choose the next operation yourself, write its snapshot/target/operation to an action JSON, and call `step`; **never call Laya**. Routine waiting/downloading/assembly can use the same deterministic commands in both arms.
6. `needs_reasoning` means inspect the returned observation, fix the task or make one `step`, then delegate again. Two invalid/no-progress actions stop the worker. Do not retry submission with a new ID unless the earlier attempt is verified failed, the retry is recorded, and the remaining budget permits it. Never delete the spending ledger to retry. Never bypass a blocked submit by clicking it natively.
7. After submission stop the Laya loop and use bounded `wait-video --after N` calls (N = completed video tile count before this shot, returned as `video_tiles_before_submit`). Stay on All media without changing filters. `result_visible` means a new thumbnail appeared; open the named tile and inspect/download the output to verify a file. A waiting worker is not useful Laya reasoning. Use `download` for the unique original/720p choice. Do not choose paid upscaling. If a new Flow UI is unsupported, return the concrete blocker; do not claim a download succeeded.
8. Repeat for shot 2. Run `assemble`; watch and listen to the entire final clip. Fill the QC JSON truthfully, then `finish`. If the run failed, finish as failed and retain evidence. End with the actual local video link; do not post or attach a TikTok basket.

## Measurement

Read the benchmark protocol. Capture observable conversation text with provenance; incomplete captures remain `complete:false`. Tool outputs are input-side visible text; assistant text/tool-call arguments are output-side visible text. Do not fabricate hidden tokens or reconstruct unobserved tool payloads. Only `report` creates the sanitized aggregate. Use null when unavailable. Laya's tokenizer totals stay separate. Every fallback, failed attempt, cold model load and Flow wait stays in the measured run.
