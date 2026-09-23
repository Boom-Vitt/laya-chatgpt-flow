import json
import unittest

from capture_rollout import capture


class CaptureChecks(unittest.TestCase):
    def test_window_privacy_deduplication_and_missing_usage(self):
        def row(kind, payload, at="2026-09-23T10:00:05Z"):
            return {"timestamp": at, "type": kind, "payload": payload}

        usage = {
            "input_tokens": 100,
            "cached_input_tokens": 80,
            "cache_write_input_tokens": 0,
            "output_tokens": 20,
            "reasoning_output_tokens": 5,
            "total_tokens": 120,
        }
        record = row("token_usage_record", {"response_id": "r1", "usage": usage})
        rows = [
            row(
                "response_item",
                {
                    "type": "message",
                    "role": "developer",
                    "content": [{"type": "input_text", "text": "PRIVATE"}],
                },
            ),
            row("response_item", {"type": "reasoning", "summary": "PRIVATE"}),
            row("response_item", {"type": "custom_tool_call", "name": "exec", "input": "observe"}),
            row(
                "response_item",
                {
                    "type": "custom_tool_call_output",
                    "output": [
                        {"type": "input_text", "text": "visible"},
                        {"type": "input_image", "image_url": "PRIVATE"},
                    ],
                },
            ),
            row(
                "response_item",
                {
                    "type": "message",
                    "role": "assistant",
                    "phase": "commentary",
                    "content": [{"type": "output_text", "text": "outside"}],
                },
                "2026-09-23T10:00:11Z",
            ),
            record,
            record,
            row("event_msg", {"type": "token_count", "info": {"total_token_usage": usage}}),
        ]
        result = capture(rows, "2026-09-23T10:00:00Z", "2026-09-23T10:00:10Z")
        self.assertEqual(
            [m["role"] for m in result["transcript"]["messages"]], ["assistant", "tool"]
        )
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("outside", str(result))
        self.assertFalse(result["transcript"]["complete"])
        self.assertEqual(result["runtime_usage"]["response_count"], 1)
        self.assertEqual(result["runtime_usage"]["totals"]["total_tokens"], 120)
        self.assertEqual(result["runtime_usage"]["totals"]["uncached_input_tokens"], 20)
        self.assertIsNone(
            capture([], "2026-09-23T10:00:00Z", "2026-09-23T10:00:10Z")["runtime_usage"]["totals"]
        )
        encoded = row(
            "response_item",
            {
                "type": "function_call_output",
                "output": json.dumps(
                    {
                        "content": [
                            {"type": "text", "text": "public text"},
                            {"type": "image", "data": "PRIVATE_IMAGE_DATA"},
                        ]
                    }
                ),
            },
        )
        filtered = capture([encoded], "2026-09-23T10:00:00Z", "2026-09-23T10:00:10Z")
        self.assertEqual(
            filtered["transcript"]["messages"], [{"role": "tool", "text": "public text"}]
        )
        self.assertNotIn("PRIVATE_IMAGE_DATA", str(filtered))
        bad = row(
            "token_usage_record",
            {"response_id": "r2", "usage": {**usage, "cached_input_tokens": 101}},
        )
        with self.assertRaises(ValueError):
            capture([bad], "2026-09-23T10:00:00Z", "2026-09-23T10:00:10Z")
