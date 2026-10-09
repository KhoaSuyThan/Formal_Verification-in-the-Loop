"""Bộ kiểm thử tính toàn vẹn của mô-đun tích hợp Groq Cloud API.

Kiểm tra định danh mô hình, metadata phân loại và cơ chế retry khi gặp lỗi 429 Rate Limit.
"""

import os
import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Đảm bảo đường dẫn thư mục gốc nằm trong sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.llm_agent import LLMAgent
from core.cross_model_evaluator import CrossModelEvaluator


class TestGroqIntegration(unittest.TestCase):
    """Kiểm thử tích hợp Groq Cloud API cho Agent và Evaluator."""

    def setUp(self):
        """Khởi tạo các đối tượng kiểm thử."""
        self.evaluator = CrossModelEvaluator()

    def test_groq_models_registered_in_default_models(self):
        """Đảm bảo các mô hình Groq cốt lõi được đăng ký trong danh sách DEFAULT_MODELS."""
        registered_ids = [m["id"] for m in self.evaluator.DEFAULT_MODELS]
        self.assertIn("groq/qwen/qwen3.8-27b", registered_ids)
        self.assertIn("groq/openai/gpt-oss-120b", registered_ids)
        self.assertIn("groq/openai/gpt-oss-20b", registered_ids)

    def test_groq_model_info_classification(self):
        """Đảm bảo _get_model_info phân loại chuẩn xác loại 'Cloud (Groq LPU)'."""
        info = self.evaluator._get_model_info("groq/qwen/qwen3.8-27b")
        self.assertEqual(info["type"], "Cloud (Groq LPU)")
        self.assertEqual(info["name"], "Qwen-3.8-27B-Groq")

        # Kiểm tra fallback tự động cho mô hình groq bất kỳ
        custom_info = self.evaluator._get_model_info("groq/custom-model")
        self.assertEqual(custom_info["type"], "Cloud (Groq LPU)")

    def test_llm_agent_groq_initialization(self):
        """Đảm bảo LLMAgent khởi tạo chính xác cho mô hình Groq."""
        agent = LLMAgent(model_name="groq/qwen/qwen3.8-27b", temperature=0.0)
        self.assertEqual(agent.model, "groq/qwen/qwen3.8-27b")
        self.assertEqual(agent.temperature, 0.0)

    @patch("litellm.completion")
    def test_llm_agent_groq_cot_extraction(self, mock_completion):
        """Kiểm tra trích xuất chuỗi suy luận CoT cho mô hình Groq."""
        # Giả lập phản hồi có thẻ <think> từ Qwen trên Groq
        mock_choice = MagicMock()
        mock_choice.message.content = "<think>\nCần dùng invariant 0 <= i <= n\n</think>\n```dafny\nmethod Foo() {}\n```"
        mock_choice.message.reasoning_content = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_completion.return_value = mock_response

        agent = LLMAgent(model_name="groq/qwen/qwen3.8-27b")
        code = agent.generate_code("Hãy viết method Foo")

        self.assertIn("method Foo", code)
        self.assertIn("invariant 0 <= i <= n", agent.last_cot_trace)
        self.assertGreater(agent.last_cot_tokens, 0)

    @patch("time.sleep", return_value=None)
    @patch("litellm.completion")
    def test_llm_agent_groq_rate_limit_retry_success(self, mock_completion, mock_sleep):
        """Kiểm tra cơ chế tự động thử lại khi gặp lỗi HTTP 429 Rate Limit."""
        # Lần 1: Ném ngoại lệ 429 Rate Limit
        error_msg = "Rate limit reached for model `groq/qwen/qwen3.8-27b` in organization `org`: Please try again in 3.5s."
        mock_error = Exception(error_msg)

        # Lần 2: Thành công trả về mã Dafny
        mock_choice = MagicMock()
        mock_choice.message.content = "```dafny\nmethod Bar() {}\n```"
        mock_choice.message.reasoning_content = None
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_completion.side_effect = [mock_error, mock_response]

        agent = LLMAgent(model_name="groq/qwen/qwen3.8-27b")
        code = agent.generate_code("Viết method Bar")

        # Xác minh code được trả về thành công sau khi retry
        self.assertIn("method Bar", code)
        self.assertEqual(mock_completion.call_count, 2)
        mock_sleep.assert_called_once()

    def test_groq_api_key_loaded(self):
        """Xác nhận biến môi trường GROQ_API_KEY đã được nạp từ .env."""
        groq_key = os.getenv("GROQ_API_KEY")
        self.assertIsNotNone(groq_key, "GROQ_API_KEY phải được nạp từ .env")
        self.assertTrue(groq_key.startswith("gsk_"), "GROQ_API_KEY phải có tiền tố gsk_")


if __name__ == "__main__":
    unittest.main()
