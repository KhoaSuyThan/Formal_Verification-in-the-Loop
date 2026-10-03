"""Unit test cho module CrossModelEvaluator."""

import unittest
from unittest.mock import MagicMock, patch
from core.cross_model_evaluator import CrossModelEvaluator, ModelBenchmarkSummary
from core.pipeline_controller import PipelineResult


class TestCrossModelEvaluator(unittest.TestCase):
    """Kiểm thử tính năng đánh giá so sánh chéo đa mô hình."""

    def setUp(self):
        self.evaluator = CrossModelEvaluator()

    def test_get_model_info(self):
        """Kiểm tra việc lấy thông tin hiển thị của mô hình."""
        info = self.evaluator._get_model_info("ollama/qwen2.5-coder:7b")
        self.assertEqual(info["name"], "Qwen2.5-Coder-7B")
        self.assertIn("Alibaba", info["description"])

        info_gemini = self.evaluator._get_model_info("gemini-3.6-flash")
        self.assertEqual(info_gemini["name"], "Gemini 3.6 Flash")
        self.assertEqual(info_gemini["type"], "Cloud (Google AI)")

    def test_generate_latex_table(self):
        """Kiểm tra việc sinh bảng LaTeX hợp lệ từ tóm tắt."""
        summaries = [
            {
                "display_name": "Qwen2.5-Coder-7B",
                "model_type": "Local (Ollama)",
                "total_tasks": 10,
                "pass_at_1_rate": 90.0,
                "pass_at_k_rate": 100.0,
                "avg_duration_sec": 12.5,
                "avg_repair_loops": 0.2
            }
        ]
        latex = CrossModelEvaluator.generate_latex_table(summaries)
        self.assertIn(r"\begin{table}", latex)
        self.assertIn(r"\textbf{Model}", latex)
        self.assertIn("Qwen2.5-Coder-7B", latex)
        self.assertIn(r"90.0\%", latex)
        self.assertIn(r"\end{table}", latex)

    @patch("core.cross_model_evaluator.CrossModelEvaluator._save_results")
    @patch("core.cross_model_evaluator.CrossModelEvaluator._save_checkpoint")
    @patch("core.cross_model_evaluator.PipelineController")
    @patch("core.cross_model_evaluator.load_task_spec")
    @patch("core.cross_model_evaluator.get_flat_task_registry")
    def test_run_benchmark_mocked(self, mock_registry, mock_load_spec, mock_pipeline_cls, mock_save_chk, mock_save_res):
        """Kiểm tra luồng benchmark với pipeline được mock."""
        mock_registry.return_value = {
            "[Clover] abs_val - Tìm giá trị tuyệt đối": {
                "short_name": "abs_val",
                "rel_path": "data/benchmarks/clover/abs_val.dfy",
                "group": "Clover"
            }
        }
        mock_load_spec.return_value = "method abs_val() ..."

        mock_instance = MagicMock()
        mock_pipeline_cls.return_value = mock_instance

        mock_instance.run_task.return_value = PipelineResult(
            task_name="abs_val",
            is_success=True,
            total_iterations=1,
            final_code="code",
            history=[]
        )

        res = self.evaluator.run_benchmark(
            model_ids=["ollama/qwen2.5-coder:7b"],
            task_keys=["[Clover] abs_val - Tìm giá trị tuyệt đối"]
        )

        self.assertEqual(len(res["summaries"]), 1)
        summary = res["summaries"][0]
        self.assertEqual(summary["total_tasks"], 1)
        self.assertEqual(summary["passed_tasks"], 1)
        self.assertEqual(summary["pass_at_1_rate"], 100.0)
        self.assertIn("latex_table", res)

    @patch("core.cross_model_evaluator.CrossModelEvaluator._save_results")
    @patch("core.cross_model_evaluator.CrossModelEvaluator._save_checkpoint")
    @patch("core.cross_model_evaluator.PipelineController")
    @patch("core.cross_model_evaluator.load_task_spec")
    @patch("core.cross_model_evaluator.get_flat_task_registry")
    @patch("builtins.open")
    @patch("os.path.exists")
    def test_run_benchmark_resume(self, mock_exists, mock_open, mock_registry, mock_load_spec, mock_pipeline_cls, mock_save_chk, mock_save_res):
        """Kiểm tra tính năng tiếp tục chạy từ checkpoint (bỏ qua bài đã hoàn thành)."""
        import json
        mock_exists.return_value = True

        fake_checkpoint = {
            "timestamp": "2026-10-03T09:00:00",
            "detailed_results": {
                "ollama/qwen2.5-coder:7b": [
                    {
                        "task_key": "task1",
                        "task_name": "task1",
                        "group": "Clover",
                        "success": True,
                        "iterations": 1,
                        "duration_sec": 10.0,
                        "repair_loops": 0
                    }
                ]
            },
            "summaries": [
                {
                    "model_name": "ollama/qwen2.5-coder:7b",
                    "display_name": "Qwen2.5-Coder-7B",
                    "model_type": "Local (Ollama)",
                    "total_tasks": 1,
                    "passed_tasks": 1,
                    "pass_at_1_count": 1,
                    "pass_at_k_count": 1,
                    "pass_at_1_rate": 100.0,
                    "pass_at_k_rate": 100.0,
                    "avg_duration_sec": 10.0,
                    "avg_repair_loops": 0.0,
                    "total_duration_sec": 10.0
                }
            ]
        }
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(fake_checkpoint)

        mock_registry.return_value = {
            "task1": {"short_name": "task1", "rel_path": "task1.dfy", "group": "Clover"},
            "task2": {"short_name": "task2", "rel_path": "task2.dfy", "group": "Clover"}
        }
        mock_load_spec.return_value = "method task2() ..."

        mock_instance = MagicMock()
        mock_pipeline_cls.return_value = mock_instance
        mock_instance.run_task.return_value = PipelineResult(
            task_name="task2",
            is_success=True,
            total_iterations=1,
            final_code="code2",
            history=[]
        )

        res = self.evaluator.run_benchmark(
            model_ids=["ollama/qwen2.5-coder:7b"],
            task_keys=["task1", "task2"],
            resume_from_checkpoint=True
        )

        # Pipeline chỉ được gọi cho task2 vì task1 đã có trong checkpoint
        mock_instance.run_task.assert_called_once()
        self.assertEqual(res["summaries"][0]["total_tasks"], 2)


if __name__ == "__main__":
    unittest.main()
