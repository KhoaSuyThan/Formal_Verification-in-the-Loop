"""Unit tests cho tính năng lưu trữ kiên cố lịch sử chạy (Persistent Run History)."""

import json
from pathlib import Path
from core.pipeline_controller import PipelineResult, IterationLog
from web_demo.helpers import (
    save_last_single_run,
    load_last_single_run,
    clear_last_single_run,
    dict_to_pipeline_result,
    save_last_batch_run,
    load_last_batch_run,
    clear_last_batch_run,
)


def test_single_run_persistence(tmp_path, monkeypatch):
    """Kiểm tra lưu, đọc và xóa kết quả chạy đơn lẻ."""
    test_results_dir = tmp_path / "artifacts" / "results"
    monkeypatch.setattr("web_demo.helpers.PROJECT_ROOT", tmp_path)

    # 1. Ban đầu chưa có dữ liệu
    assert load_last_single_run() is None
    assert clear_last_single_run() is False

    # 2. Tạo đối tượng giả lập PipelineResult
    log1 = IterationLog(
        iteration=1,
        code="method Abs(x: int) ...",
        is_spec_valid=True,
        is_verified=True,
        error_message="",
        error_taxonomy="",
    )
    dummy_res = PipelineResult(
        task_name="abs_val",
        is_success=True,
        total_iterations=1,
        final_code="method Abs(x: int) ...",
        history=[log1],
    )

    # 3. Lưu xuống đĩa
    save_last_single_run(
        task_name="abs_val",
        task_label="abs_val - Tìm giá trị tuyệt đối",
        spec_content="method Abs(x: int) returns (y: int)",
        model_name="ollama/qwen2.5-coder:7b",
        max_k=3,
        timeout_sec=15,
        result_obj=dummy_res,
        elapsed=1.25,
    )

    # 4. Đọc lại từ đĩa
    loaded = load_last_single_run()
    assert loaded is not None
    assert loaded["task_name"] == "abs_val"
    assert loaded["is_success"] is True
    assert loaded["elapsed"] == 1.25
    assert len(loaded["history"]) == 1

    # 5. Khôi phục lại đối tượng PipelineResult
    restored_res, meta = dict_to_pipeline_result(loaded)
    assert restored_res.task_name == "abs_val"
    assert restored_res.is_success is True
    assert len(restored_res.history) == 1
    assert restored_res.history[0].is_verified is True

    # 6. Xóa và xác nhận đã xóa
    assert clear_last_single_run() is True
    assert load_last_single_run() is None


def test_batch_run_persistence(tmp_path, monkeypatch):
    """Kiểm tra lưu, đọc và xóa kết quả đợt chạy hàng loạt."""
    monkeypatch.setattr("web_demo.helpers.PROJECT_ROOT", tmp_path)

    # 1. Ban đầu chưa có dữ liệu
    assert load_last_batch_run() is None
    assert clear_last_batch_run() is False

    # 2. Dữ liệu đợt chạy mẫu
    sample_list = [
        {"STT": 1, "Bài Toán": "abs_val", "Kết Quả Z3": "✅ PASS", "Lượt Hội Tụ": "Pass@1"},
        {"STT": 2, "Bài Toán": "find_min", "Kết Quả Z3": "✅ PASS", "Lượt Hội Tụ": "Pass@1"},
    ]

    # 3. Lưu xuống đĩa
    save_last_batch_run(
        results_list=sample_list,
        total_batch_time=5.5,
        model_name="ollama/qwen2.5-coder:7b",
        max_k=3,
        timeout_sec=15,
    )

    # 4. Đọc lại
    loaded = load_last_batch_run()
    assert loaded is not None
    assert loaded["total_batch_time"] == 5.5
    assert len(loaded["results_list"]) == 2
    assert loaded["results_list"][0]["Bài Toán"] == "abs_val"

    # 5. Xóa
    assert clear_last_batch_run() is True
    assert load_last_batch_run() is None
