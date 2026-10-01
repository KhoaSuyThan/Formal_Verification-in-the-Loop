"""Unit test cho module Token Tracker Gemini."""

import os
import unittest
from unittest.mock import patch
from core.token_tracker import get_gemini_token_usage, record_gemini_tokens, reset_gemini_tokens, TRACKER_FILE


class TestTokenTracker(unittest.TestCase):
    """Kiểm thử tính năng đếm và lưu trữ token Gemini."""

    def setUp(self):
        self.test_file = os.path.join("artifacts", "results", "gemini_token_usage_test.json")

    @patch("core.token_tracker.TRACKER_FILE", new="artifacts/results/gemini_token_usage_test.json")
    def test_record_and_get_tokens(self):
        # Reset trước
        reset_gemini_tokens()
        initial = get_gemini_token_usage()
        self.assertEqual(initial["total_tokens"], 0)

        # Ghi nhận lần 1
        record_gemini_tokens(prompt_count=100, completion_count=50, total_count=150)
        data = get_gemini_token_usage()
        self.assertEqual(data["prompt_tokens"], 100)
        self.assertEqual(data["completion_tokens"], 50)
        self.assertEqual(data["total_tokens"], 150)
        self.assertEqual(data["total_requests"], 1)

        # Ghi nhận lần 2
        record_gemini_tokens(prompt_count=200, completion_count=100, total_count=300)
        data2 = get_gemini_token_usage()
        self.assertEqual(data2["prompt_tokens"], 300)
        self.assertEqual(data2["completion_tokens"], 150)
        self.assertEqual(data2["total_tokens"], 450)
        self.assertEqual(data2["total_requests"], 2)

        # Dọn dẹp file test
        if os.path.exists("artifacts/results/gemini_token_usage_test.json"):
            os.remove("artifacts/results/gemini_token_usage_test.json")


if __name__ == "__main__":
    unittest.main()
