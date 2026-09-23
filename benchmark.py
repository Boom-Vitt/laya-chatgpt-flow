"""Visible-text estimates are not OpenAI usage or billing metrics."""

import json
import statistics
from pathlib import Path

from flow import read_json


def transcript_metrics(path):
    empty = {
        "visible_input_tokens_est": None,
        "visible_output_tokens_est": None,
        "visible_total_tokens_est": None,
        "comparable": False,
        "transcript_source": None,
    }
    if not Path(path).is_file():
        return empty
    import tiktoken

    doc = read_json(path)
    if not isinstance(doc.get("source"), str) or not isinstance(doc.get("messages"), list):
        raise ValueError("transcript needs source and messages")
    enc = tiktoken.get_encoding("o200k_base")
    inp = out = 0
    for msg in doc["messages"]:
        if msg.get("role") not in ("user", "assistant", "tool") or not isinstance(
            msg.get("text"), str
        ):
            raise ValueError("transcript contains invalid message")
        n = len(enc.encode(msg["text"], disallowed_special=()))
        if msg["role"] == "assistant":
            out += n
        else:
            inp += n
    return {
        "visible_input_tokens_est": inp,
        "visible_output_tokens_est": out,
        "visible_total_tokens_est": inp + out,
        "comparable": doc.get("complete") is True and bool(doc["messages"]),
        "transcript_source": doc["source"],
    }


def comparison(rows):
    result = {
        "token_reduction_pct": None,
        "time_reduction_pct": None,
        "reason": "requires three comparable successful ChatGPT Work pairs",
    }
    attempts = [
        r
        for r in rows
        if r.get("brain") == "chatgpt-work-local" and r.get("arm") in ("baseline", "hybrid")
    ]
    if len(attempts) != 6:
        result["reason"] = (
            "requires exactly six registered attempts; do not drop failures or retries"
        )
        return result
    if any(
        (r.get("laya_decision_count") or 0) < 1 for r in attempts if r["arm"] == "hybrid"
    ) or any(r.get("laya_decision_count") != 0 for r in attempts if r["arm"] == "baseline"):
        result["reason"] = (
            "execution evidence must show Laya decisions in hybrid and none in baseline"
        )
        return result
    eligible = [
        r
        for r in rows
        if r.get("brain") == "chatgpt-work-local"
        and r.get("status") == "passed"
        and r.get("comparable")
    ]
    arms = {a: [r for r in eligible if r["arm"] == a] for a in ("baseline", "hybrid")}
    if any(len(v) != 3 for v in arms.values()):
        return result
    if any({r.get("pair") for r in v} != {1, 2, 3} for v in arms.values()):
        return result
    if len({(r.get("protocol"), r.get("model_label")) for r in eligible}) != 1:
        result["reason"] = "protocol or ChatGPT model labels differ"
        return result
    for key, metric in [
        ("token_reduction_pct", "visible_total_tokens_est"),
        ("time_reduction_pct", "elapsed_s"),
    ]:
        if any(r.get(metric) is None for r in eligible):
            continue
        base = statistics.median(r[metric] for r in arms["baseline"])
        hybrid = statistics.median(r[metric] for r in arms["hybrid"])
        if base > 0:
            result[key] = round((base - hybrid) / base * 100, 2)
    result["reason"] = "descriptive median comparison only; n=3 per arm, not a causal claim"
    return result


def report_runs(paths):
    rows = []
    for path in paths:
        root = Path(path)
        cfg = read_json(root / "run.json")
        events = [
            json.loads(line)
            for line in (root / "events.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        row = {
            k: cfg.get(k)
            for k in (
                "arm",
                "brain",
                "pair",
                "status",
                "model_label",
                "protocol",
                "elapsed_s",
                "execution_status_at_finish",
                "post_execution_qc",
                "qc_received_at",
                "qc_received_elapsed_s",
                "qc_wait_s",
            )
        }
        row["run"] = root.name
        row.update(transcript_metrics(root / "transcript.json"))
        for kind, name in [
            ("laya_decision", "laya_inference_s"),
            ("model_load", "model_load_s"),
            ("flow_wait", "flow_wait_s"),
            ("download", "download_s"),
            ("assemble", "assembly_s"),
        ]:
            matches = [e for e in events if e["kind"] == kind]
            field = "inference_s" if kind == "laya_decision" else "seconds"
            row[name] = sum(e[field] for e in matches) if matches else None
        row["laya_input_tokens"] = (
            sum(e["laya_input_tokens"] for e in events if e["kind"] == "laya_decision") or None
        )
        for kind in (
            "needs_reasoning",
            "action_error",
            "model_error",
            "credit_reserved",
            "chatgpt_step",
            "laya_decision",
            "native_setup",
            "native_navigation",
            "native_download_navigation",
        ):
            row[kind + "_count"] = sum(e["kind"] == kind for e in events)
        row["credits_reserved"] = sum(
            e["credits"] for e in events if e["kind"] == "credit_reserved"
        )
        rows.append(row)
    summary = {}
    for arm in ("baseline", "hybrid"):
        group = [r for r in rows if r["arm"] == arm and r["brain"] == "chatgpt-work-local"]
        times = [r["elapsed_s"] for r in group if r["elapsed_s"] is not None]
        summary[arm] = {
            "attempts": len(group),
            "passed": sum(r["status"] == "passed" for r in group),
            "elapsed_median_s": statistics.median(times) if times else None,
            "elapsed_min_s": min(times) if times else None,
            "elapsed_max_s": max(times) if times else None,
        }
    return {
        "schema": 1,
        "tokenizer": "o200k_base",
        "metric": "visible text counted once",
        "limitations": [
            "Not actual OpenAI input/output, reasoning, cached or billed usage.",
            "Excludes hidden prompts, images, internal reasoning and context replay.",
            "Laya tokens use a different tokenizer and are reported separately.",
            "Elapsed is init through original execution finish, including pauses and cold model load. "
            "Later human QC wait is reported separately when recorded.",
            "Only sanitized aggregates are exported; raw local logs remain private.",
        ],
        "runs": rows,
        "summary": summary,
        "comparison": comparison(rows),
    }
