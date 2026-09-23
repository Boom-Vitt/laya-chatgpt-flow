"""Boundary checks: overspending, stale actions and false benchmark wins must fail."""

import json
import tempfile
import unittest
from pathlib import Path


class WorkflowChecks(unittest.TestCase):
    def test_pilot_finish_cannot_finalize_a_benchmark_arm(self):
        from flow import finish, write_json

        with tempfile.TemporaryDirectory() as folder:
            write_json(
                Path(folder) / "run.json",
                {"arm": "hybrid", "status": "running", "started_mono_s": 0},
            )
            with self.assertRaises(ValueError):
                finish(folder, "pilot_downloaded", None)

    def test_project_scope_allows_its_editor_only(self):
        from browser_worker import same_project

        root = "https://flow.google.com/project/abc-123"
        self.assertTrue(same_project(root + "/edit/clip-456", root))
        for url in [
            root + "-other",
            root + "/bin",
            "https://evil.example/project/abc-123",
            "http://flow.google.com/project/abc-123",
            root + "/edit/../../other",
        ]:
            self.assertFalse(same_project(url, root))

    def test_budget_survives_restart_and_duplicate_submission(self):
        from flow import reserve_credit

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "budget.sqlite"
            self.assertEqual(reserve_credit(path, 20, "shot-1", 10), 10)
            with self.assertRaises(ValueError):
                reserve_credit(path, 20, "shot-1", 10)
            self.assertEqual(reserve_credit(path, 20, "shot-2", 10), 20)
            for key, cost, cap in [("shot-3", 10, 20), ("bad", -1, 20), ("reset", 10, 100)]:
                with self.assertRaises(ValueError):
                    reserve_credit(path, cap, key, cost)

    def test_task_rejects_unsafe_scope_and_unaccounted_create(self):
        from flow import validate_task

        task = {
            "id": "shot-1",
            "goal": "Fill prompt then create one video",
            "click": ["Create"],
            "type": {"Prompt": "A ceramic mug."},
            "done_text": "Generating",
            "submit": {"name": "Create", "credits": 10, "evidence": "10 credits"},
        }
        validate_task(task)
        for bad in [
            {**task, "click": ["Delete project"]},
            {**task, "submit": None},
            {**task, "goal": ""},
            {**task, "id": "../escape"},
            {**task, "click": ["Start generation"], "submit": None},
            {**task, "done_field": "Unknown"},
            {**task, "done_video": -1},
        ]:
            with self.assertRaises(ValueError):
                validate_task(bad)

    def test_action_cannot_use_stale_or_unlisted_control(self):
        from flow import validate_action

        obs = {
            "snapshot": "abc",
            "elements": [
                {"id": "0", "name": "Prompt", "role": "textbox", "editable": True},
                {"id": "1", "name": "Delete", "role": "button", "editable": False},
            ],
        }
        task = {"click": [], "type": {"Prompt": "test"}}
        validate_action({"operation": "TYPE_TEXT", "target": "0", "snapshot": "abc"}, obs, task)
        for action in [
            {"operation": "CLICK", "target": "1", "snapshot": "abc"},
            {"operation": "TYPE_TEXT", "target": "0", "snapshot": "old"},
            {"operation": "EVAL", "target": "0", "snapshot": "abc"},
        ]:
            with self.assertRaises(ValueError):
                validate_action(action, obs, task)

    def test_missing_or_partial_transcript_is_not_zero_tokens(self):
        from benchmark import transcript_metrics

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "transcript.json"
            self.assertIsNone(transcript_metrics(path)["visible_total_tokens_est"])
            path.write_text(
                json.dumps(
                    {
                        "source": "manually exported visible text",
                        "complete": False,
                        "messages": [{"role": "user", "text": "Hello"}],
                    }
                )
            )
            result = transcript_metrics(path)
            self.assertGreater(result["visible_total_tokens_est"], 0)
            self.assertFalse(result["comparable"])

    def test_non_chatgpt_and_failed_runs_cannot_produce_savings(self):
        from benchmark import comparison

        rows = [
            {
                "arm": "baseline",
                "status": "passed",
                "brain": "codex-development",
                "elapsed_s": 50,
                "visible_total_tokens_est": 200,
                "comparable": True,
            },
            {
                "arm": "hybrid",
                "status": "failed",
                "brain": "chatgpt-work-local",
                "elapsed_s": 10,
                "visible_total_tokens_est": 10,
                "comparable": True,
            },
        ]
        self.assertIsNone(comparison(rows)["token_reduction_pct"])
        self.assertIsNone(comparison(rows)["time_reduction_pct"])

    def test_failed_attempt_is_not_silently_excluded_from_comparison(self):
        from benchmark import comparison

        rows = [
            {
                "arm": arm,
                "pair": pair,
                "status": "passed",
                "brain": "chatgpt-work-local",
                "elapsed_s": 100 if arm == "baseline" else 80,
                "visible_total_tokens_est": 200 if arm == "baseline" else 100,
                "comparable": True,
                "protocol": "mug-v1",
                "model_label": "same",
                "laya_decision_count": 1 if arm == "hybrid" else 0,
            }
            for arm in ("baseline", "hybrid")
            for pair in (1, 2, 3)
        ]
        self.assertEqual(comparison(rows)["token_reduction_pct"], 50)
        self.assertEqual(comparison(rows)["time_reduction_pct"], 20)
        missing_evidence = [{**r, "laya_decision_count": 0} for r in rows]
        self.assertIsNone(comparison(missing_evidence)["token_reduction_pct"])
        rows.append({**rows[-1], "status": "failed"})
        self.assertIsNone(comparison(rows)["token_reduction_pct"])

    def test_old_video_never_completes_a_submission_task(self):
        from browser_worker import Browser

        browser = object.__new__(Browser)
        self.assertFalse(
            browser.done(
                {"submit": {"name": "Start generation"}, "done_video": 1},
                {"videos": [{"ready": True}]},
            )
        )


if __name__ == "__main__":
    unittest.main()
