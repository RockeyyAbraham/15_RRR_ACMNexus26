"""Deterministic unit tests for decision policy and async job state helpers."""

import os
import sys
import unittest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

from api import main as api_main


class TestDecisionPolicy(unittest.TestCase):
    def test_auto_action_tier(self):
        score = api_main.AUTO_ACTION_THRESHOLD + 0.5
        tier, reason = api_main.classify_detection_tier(score)
        self.assertEqual(tier, "auto_action")
        self.assertEqual(reason, "score_above_auto_threshold")

    def test_manual_review_tier(self):
        score = (api_main.MANUAL_REVIEW_THRESHOLD + api_main.AUTO_ACTION_THRESHOLD) / 2.0
        tier, reason = api_main.classify_detection_tier(score)
        self.assertEqual(tier, "manual_review")
        self.assertEqual(reason, "score_above_review_threshold")

    def test_no_match_tier(self):
        score = api_main.MANUAL_REVIEW_THRESHOLD - 0.1
        tier, reason = api_main.classify_detection_tier(score)
        self.assertEqual(tier, "no_match")
        self.assertEqual(reason, "score_below_review_threshold")


class TestAsyncJobState(unittest.TestCase):
    def test_create_and_update_job(self):
        job_id = api_main.create_job("unit_test", {"k": "v"})
        created = api_main.get_job(job_id)
        self.assertIsNotNone(created)
        self.assertEqual(created["status"], "queued")
        self.assertEqual(created["job_type"], "unit_test")

        api_main.update_job(job_id, status="running")
        running = api_main.get_job(job_id)
        self.assertEqual(running["status"], "running")

        api_main.update_job(job_id, status="completed", result={"ok": True})
        completed = api_main.get_job(job_id)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["result"], {"ok": True})


if __name__ == "__main__":
    unittest.main()
