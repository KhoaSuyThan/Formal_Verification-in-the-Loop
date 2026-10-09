import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

# Đảm bảo đường dẫn thư mục gốc nằm trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.token_tracker import (
    get_gemini_token_usage, record_gemini_tokens, reset_gemini_tokens, TRACKER_FILE,
    get_groq_token_usage, record_groq_tokens, reset_groq_tokens, GROQ_TRACKER_FILE
)


class TestTokenTracker(unittest.TestCase):
    """Kiểm thử tính năng đếm và lưu trữ token Gemini và Groq."""

    def setUp(self):
        self.test_file = os.path.join("artifacts", "results", "gemini_token_usage_test.json")
        self.groq_test_file = os.path.join("artifacts", "results", "groq_token_usage_test.json")

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

    @patch("core.token_tracker.GROQ_TRACKER_FILE", new="artifacts/results/groq_token_usage_test.json")
    def test_record_and_get_groq_tokens(self):
        # Reset trước
        reset_groq_tokens()
        initial = get_groq_token_usage()
        self.assertEqual(initial["total_tokens"], 0)

        # Ghi nhận lần 1
        record_groq_tokens(prompt_count=350, completion_count=120, total_count=470)
        data = get_groq_token_usage()
        self.assertEqual(data["prompt_tokens"], 350)
        self.assertEqual(data["completion_tokens"], 120)
        self.assertEqual(data["total_tokens"], 470)
        self.assertEqual(data["total_requests"], 1)

        # Ghi nhận lần 2
        record_groq_tokens(prompt_count=150, completion_count=80, total_count=230)
        data2 = get_groq_token_usage()
        self.assertEqual(data2["prompt_tokens"], 500)
        self.assertEqual(data2["completion_tokens"], 200)
        self.assertEqual(data2["total_tokens"], 700)
        self.assertEqual(data2["total_requests"], 2)

        # Dọn dẹp file test
        if os.path.exists("artifacts/results/groq_token_usage_test.json"):
            os.remove("artifacts/results/groq_token_usage_test.json")


if __name__ == "__main__":
    unittest.main()
