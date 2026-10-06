"""Bộ kiểm thử đơn vị cho Bước 4: Song song hóa Benchmark và SMT Verification Cache.

Kiểm tra tính tất định của SHA-256 key, cơ chế lưu/nạp cache, an toàn đa luồng,
và tích hợp ThreadPoolExecutor trong CrossModelEvaluator.
"""

import os
import json
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from core.dafny_engine import VerifyResult, DafnyEngine
from core.verification_cache import VerificationCache
from core.cross_model_evaluator import CrossModelEvaluator, ModelBenchmarkSummary


def test_verification_cache_put_get(tmp_path):
    """Kiểm tra chức năng lưu và truy xuất cơ bản của SMT VerificationCache."""
    cache_file = tmp_path / "test_cache.json"
    cache = VerificationCache(cache_file=str(cache_file))

    code = "method Abs(x: int) returns (y: int) ensures y >= 0 { if x < 0 { return -x; } else { return x; } }"
    res = VerifyResult(is_verified=True, return_code=0, output="Dafny program verifier finished with 1 verified, 0 errors")

    # Trước khi lưu -> cache miss
    assert cache.get(code, extract_counterexample=True) is None

    # Lưu vào cache
    cache.set(code, extract_counterexample=True, result=res)

    # Sau khi lưu -> cache hit
    cached = cache.get(code, extract_counterexample=True)
    assert cached is not None
    assert cached.is_verified is True
    assert cached.return_code == 0
    assert "0 errors" in cached.output

    # Cờ khác -> cache miss (vì khác cờ extract_counterexample)
    assert cache.get(code, extract_counterexample=False) is None

    # Thống kê
    st = cache.stats()
    assert st["hits"] == 1
    assert st["misses"] == 2
    assert st["cached_items"] == 1


def test_verification_cache_persistence(tmp_path):
    """Kiểm tra khả năng lưu trữ kiên cố ra file JSON và nạp lại khi khởi động."""
    cache_file = tmp_path / "persistent_cache.json"
    cache1 = VerificationCache(cache_file=str(cache_file))

    code = "method Add(a: int, b: int) returns (c: int) ensures c == a + b { return a + b; }"
    res = VerifyResult(is_verified=True, return_code=0, output="0 errors")
    cache1.set(code, extract_counterexample=True, result=res)
    assert cache_file.exists()

    # Khởi tạo instance mới cùng đường dẫn
    cache2 = VerificationCache(cache_file=str(cache_file))
    cached = cache2.get(code, extract_counterexample=True)
    assert cached is not None
    assert cached.is_verified is True


def test_verification_cache_thread_safety(tmp_path):
    """Kiểm tra an toàn đa luồng khi nhiều luồng cùng ghi và đọc cache đồng thời."""
    cache_file = tmp_path / "thread_safe_cache.json"
    cache = VerificationCache(cache_file=str(cache_file))

    def worker_task(worker_id: int):
        for i in range(10):
            code = f"method Test{worker_id}_{i}() {{ }}"
            res = VerifyResult(is_verified=True, return_code=0, output=f"worker_{worker_id}_{i}")
            cache.set(code, extract_counterexample=True, result=res)
            retrieved = cache.get(code, extract_counterexample=True)
            assert retrieved is not None
            assert retrieved.output == f"worker_{worker_id}_{i}"

    threads = [threading.Thread(target=worker_task, args=(w,)) for w in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    st = cache.stats()
    assert st["cached_items"] == 50
    assert st["hits"] == 50


def test_dafny_engine_uses_cache(monkeypatch, tmp_path):
    """Kiểm tra DafnyEngine bỏ qua gọi subprocess khi kết quả đã có trong cache."""
    cache_file = tmp_path / "engine_cache.json"
    cache = VerificationCache(cache_file=str(cache_file))

    code = "method Dummy() { }"
    mock_res = VerifyResult(is_verified=True, return_code=0, output="Cached result 0 errors")
    cache.set(code, extract_counterexample=True, result=mock_res)

    engine = DafnyEngine(cache=cache)
    # Không cần Dafny CLI thật trên máy vì kết quả nạp thẳng từ cache
    result = engine.verify(code, extract_counterexample=True)
    assert result.is_verified is True
    assert result.output == "Cached result 0 errors"
    assert cache.stats()["hits"] == 1


def test_cross_model_evaluator_parallel_execution(monkeypatch, tmp_path):
    """Kiểm tra CrossModelEvaluator chạy đa luồng với workers=2 thành công."""
    evaluator = CrossModelEvaluator()

    # Mock _run_single_task để không cần gọi mạng LLM thật trong bài test
    def mock_run_single(task_label, meta, model_id, controller, max_attempts):
        time.sleep(0.01)  # Giả lập thời gian chạy nhẹ
        return {
            "task_key": task_label,
            "task_name": meta["short_name"],
            "group": meta["group"],
            "success": True,
            "iterations": 1,
            "duration_sec": 0.05,
            "repair_loops": 0,
            "h_code": "H0",
            "h_badge": "🟢 Chuẩn",
            "h_name": "Zero-Hallucination",
            "has_cot": False,
            "cot_tokens": 0,
            "cot_preview": "",
            "cot_trace": "",
            "has_cegar": False,
            "has_cegar_repaired": False,
            "counterexample_desc": ""
        }

    monkeypatch.setattr(CrossModelEvaluator, "_run_single_task", staticmethod(mock_run_single))

    from web_demo.helpers import get_flat_task_registry
    all_reg_keys = list(get_flat_task_registry().keys())
    task_keys = all_reg_keys[:4]
    
    # Mock checkpoint save để không ảnh hưởng artifacts thực
    mock_save = MagicMock()
    monkeypatch.setattr(evaluator, "_save_checkpoint", mock_save)
    monkeypatch.setattr(evaluator, "_save_results", MagicMock())

    progress_events = []
    def on_progress(model_id, cur, tot, msg, data=None):
        progress_events.append((cur, tot))

    results = evaluator.run_benchmark(
        model_ids=["ollama/qwen2.5-coder:7b"],
        task_keys=task_keys,
        max_attempts=3,
        progress_callback=on_progress,
        workers=2,
        use_cache=False
    )

    assert results["workers"] == 2
    assert results["task_count"] == 4
    detailed = results["detailed_results"]["ollama/qwen2.5-coder:7b"]
    assert len(detailed) == 4
    assert all(r["success"] is True for r in detailed)

    # Đảm bảo summary được tính toán chính xác
    summary = next(s for s in results["summaries"] if s["model_name"] == "ollama/qwen2.5-coder:7b")
    assert summary["passed_tasks"] == 4
    assert summary["pass_at_1_count"] == 4
    assert summary["pass_at_1_rate"] == 100.0


def test_cross_model_evaluator_stop_check_in_parallel(monkeypatch):
    """Kiểm tra tín hiệu dừng an toàn ngắt luồng đa worker sớm."""
    evaluator = CrossModelEvaluator()

    call_count = 0
    def mock_run_single(task_label, meta, model_id, controller, max_attempts):
        nonlocal call_count
        call_count += 1
        time.sleep(0.05)
        return {
            "task_key": task_label,
            "task_name": meta["short_name"],
            "group": meta["group"],
            "success": True,
            "iterations": 1,
            "duration_sec": 0.05,
            "repair_loops": 0,
            "h_code": "H0",
            "h_badge": "🟢 Chuẩn",
            "h_name": "Zero-Hallucination",
            "has_cot": False,
            "cot_tokens": 0,
            "cot_preview": "",
            "cot_trace": "",
            "has_cegar": False,
            "has_cegar_repaired": False,
            "counterexample_desc": ""
        }

    monkeypatch.setattr(CrossModelEvaluator, "_run_single_task", staticmethod(mock_run_single))
    monkeypatch.setattr(evaluator, "_save_checkpoint", MagicMock())
    monkeypatch.setattr(evaluator, "_save_results", MagicMock())

    stop_triggered = False
    def stop_checker():
        nonlocal stop_triggered
        return stop_triggered

    # Kích hoạt dừng ngay từ đầu
    from web_demo.helpers import get_flat_task_registry
    task_keys = list(get_flat_task_registry().keys())[:3]
    stop_triggered = True

    results = evaluator.run_benchmark(
        model_ids=["ollama/qwen2.5-coder:7b"],
        task_keys=task_keys,
        max_attempts=3,
        stop_check=stop_checker,
        workers=2,
        use_cache=False
    )

    # Không chạy bài nào vì đã dừng ngay từ đầu
    assert len(results["detailed_results"]["ollama/qwen2.5-coder:7b"]) == 0
