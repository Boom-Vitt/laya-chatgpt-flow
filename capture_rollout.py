"""Optional local log capture. No APIs, hidden prompt export, or billing claims."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from flow import read_json, write_json

COUNTERS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps need a timezone")
    return result


def visible_text(content):
    if isinstance(content, str):
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            return content
        if isinstance(decoded, dict) and isinstance(decoded.get("content"), list):
            return visible_text(decoded["content"])
        if isinstance(decoded, dict) and decoded.get("type") in (
            "input_image",
            "image",
            "input_audio",
            "audio",
        ):
            return ""
        if isinstance(decoded, list) and all(isinstance(p, dict) and "type" in p for p in decoded):
            return visible_text(decoded)
        return content
    if isinstance(content, list):
        return "\n".join(
            part["text"]
            for part in content
            if isinstance(part, dict)
            and part.get("type") in ("input_text", "output_text", "text")
            and isinstance(part.get("text"), str)
        )
    return ""


def capture(rows, start, end):
    start_at, end_at = timestamp(start), timestamp(end)
    if end_at < start_at:
        raise ValueError("finish precedes start")
    messages, responses = [], {}
    for row in rows:
        if not start_at <= timestamp(row["timestamp"]) <= end_at:
            continue
        payload = row.get("payload", {})
        if row.get("type") == "token_usage_record":
            response_id, usage = payload.get("response_id"), payload.get("usage", {})
            if not isinstance(response_id, str) or not response_id:
                raise ValueError("usage record has no response ID")
            if any(type(usage.get(k)) is not int or usage[k] < 0 for k in COUNTERS):
                raise ValueError("usage counters must be nonnegative integers")
            usage = {key: usage[key] for key in COUNTERS}
            if (
                usage["input_tokens"] + usage["output_tokens"] != usage["total_tokens"]
                or usage["cached_input_tokens"] > usage["input_tokens"]
                or usage["reasoning_output_tokens"] > usage["output_tokens"]
            ):
                raise ValueError("inconsistent usage counters")
            if response_id in responses and responses[response_id] != usage:
                raise ValueError("conflicting duplicate response usage")
            responses[response_id] = usage
        if row.get("type") != "response_item":
            continue
        kind, role, text = payload.get("type"), None, ""
        if kind == "message" and payload.get("role") in ("user", "assistant"):
            role = payload["role"]
            if role == "user" or payload.get("phase") in ("commentary", "final"):
                text = visible_text(payload.get("content"))
        elif kind in ("function_call", "custom_tool_call"):
            role = "assistant"
            text = (
                payload.get("name", "")
                + "\n"
                + visible_text(payload.get("arguments", payload.get("input", "")))
            )
        elif kind in ("function_call_output", "custom_tool_call_output"):
            role, text = "tool", visible_text(payload.get("output"))
        if text:
            messages.append({"role": role, "text": text})
    totals = None
    if responses:
        totals = {key: sum(usage[key] for usage in responses.values()) for key in COUNTERS}
        totals["uncached_input_tokens"] = totals["input_tokens"] - totals["cached_input_tokens"]
    return {
        "window": {"start": start, "end": end, "selection": "record timestamp, inclusive"},
        "transcript": {
            "source": "Local JSONL response items timestamped between run init and finish; "
            "user/assistant visible text and tool arguments/outputs only. Excludes system, "
            "developer, reasoning, images and event summaries. Log completeness is unverified.",
            "complete": False,
            "messages": messages,
        },
        "runtime_usage": {
            "source": "Local token_usage_record.usage, deduplicated by response_id",
            "response_count": len(responses),
            "totals": totals,
            "limitations": [
                "Host-reported telemetry; not verified against a provider bill or usage API.",
                "Records are selected by timestamp, not a provider request start/end interval.",
                "Input includes context replay; cached input is a subset, not extra tokens.",
                "Reasoning output is a subset of output; no reasoning content is exported.",
                "Setup context can be replayed during the run and confound comparisons.",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rollout", type=Path)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    output = args.run / "rollout-capture.json"
    if output.exists():
        parser.error("rollout-capture.json already exists; preserve earlier evidence")
    run = read_json(args.run / "run.json")
    events = [json.loads(line) for line in (args.run / "events.jsonl").read_text().splitlines()]
    finishes = [event["at"] for event in events if event.get("kind") == "finish"]
    if not finishes:
        parser.error("finish the run before capturing")
    with args.rollout.open() as stream:
        result = capture((json.loads(line) for line in stream), run["started_at"], finishes[-1])
    write_json(output, result)
    print(json.dumps({"output": str(output), "runtime_usage": result["runtime_usage"]}))


if __name__ == "__main__":
    main()
