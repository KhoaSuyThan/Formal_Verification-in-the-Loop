"""Script dòng lệnh (CLI) chạy thực nghiệm Ablation Study đối chuẩn với Stanford Clover (2024).

Sử dụng:
    python experiments/run_clover_baseline_comparison.py --preset sample --model gemini
    python experiments/run_clover_baseline_comparison.py --preset core --model qwen
    python experiments/run_clover_baseline_comparison.py --preset all --model gemini
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Đảm bảo đường dẫn gốc của dự án nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
load_dotenv()

from agents.llm_agent import LLMAgent
from core.dafny_engine import DafnyEngine
from core.pipeline_controller import PipelineController, PipelineResult
from core.latex_exporter import LaTeXExporter
from web_demo.helpers import get_flat_task_registry, load_task_spec


MODEL_MAP = {
    "qwen": "ollama/qwen2.5-coder:7b",
    "deepseek": "ollama/deepseek-r1:7b",
    "gemini": "gemini-2.5-flash",
    "gemini-2.5": "gemini-2.5-flash",
    "gemini-3.5": "gemini-3.5-flash",
    "llama": "ollama/llama3.1:8b"
}


def parse_args():
    parser = argparse.ArgumentParser(description="Chạy thực nghiệm đối chuẩn Ablation Study với Stanford Clover (2024)")
    parser.add_argument(
        "--model",
        default="gemini",
        help="Mô hình LLM sử dụng: qwen, gemini, deepseek, llama"
    )
    parser.add_argument(
        "--preset",
        choices=["sample", "core", "clover", "humaneval", "all"],
        default="sample",
        help="Tập bài toán: sample (5 bài), core (16 bài), clover (6 bài), humaneval (10 bài), all (30 bài)"
    )
    parser.add_argument(
        "--max-k",
        type=int,
        default=3,
        help="Số vòng lặp Pass@K tối đa (mặc định K=3)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Thời gian giới hạn cho Z3 SMT Solver (giây)"
    )
    return parser.parse_args()


def select_tasks(preset: str) -> List[str]:
    """Chọn danh sách key bài toán theo preset."""
    flat_registry = get_flat_task_registry()
    all_keys = list(flat_registry.keys())

    if preset == "all":
        return all_keys
    elif preset == "sample":
        # 5 bài tiêu biểu đa dạng hình thái
        sample_names = ["abs_val", "sum_to_n", "greatest_common_divisor", "is_palindrome", "sort_array"]
        return [k for k in all_keys if any(s in k for s in sample_names)][:5]
    elif preset == "clover":
        return [k for k in all_keys if "clover" in flat_registry[k].get("group", "").lower()]
    elif preset == "humaneval":
        return [k for k in all_keys if "humaneval" in flat_registry[k].get("group", "").lower()]
    elif preset == "core":
        return [k for k in all_keys if any(g in flat_registry[k].get("group", "").lower() for g in ["clover", "humaneval"])][:16]
    return all_keys[:5]


def run_single_method(
    controller: PipelineController,
    task_keys: List[str],
    flat_registry: Dict[str, Any],
    method_name: str,
    progress_callback=None,
    step_offset: int = 0,
    total_steps: int = 1,
) -> Dict[str, Any]:
    """Chạy toàn bộ tập bài toán cho một phương pháp cụ thể."""
    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU CHẠY PHƯƠNG PHÁP: {method_name}")
    print(f"=======================================================")

    results = []
    total_time = 0.0
    pass_at_1 = 0
    pass_at_k = 0
    tamper_count = 0
    cegar_count = 0
    total_loops = 0

    for idx, key in enumerate(task_keys):
        task_info = flat_registry[key]
        task_name = task_info["short_name"]
        raw_spec = load_task_spec(task_info["rel_path"])

        current_overall_step = step_offset + idx + 1
        if progress_callback:
            progress_callback(
                current_overall_step,
                total_steps,
                f"[{method_name}] Đang chạy bài ({idx + 1}/{len(task_keys)}): {task_name}..."
            )

        print(f"\n[{idx + 1}/{len(task_keys)}] Đang chạy {task_name}...")
        t0 = time.time()
        res: PipelineResult = controller.run_task(raw_spec=raw_spec, task_name=task_name)
        elapsed = time.time() - t0
        total_time += elapsed

        # Phân tích kết quả
        is_p1 = len(res.history) > 0 and res.history[0].is_verified
        is_pk = res.is_success
        has_tamper = any(not log.is_spec_valid for log in res.history)

        if is_p1:
            pass_at_1 += 1
        if is_pk:
            pass_at_k += 1
        if has_tamper:
            tamper_count += 1
        if getattr(res, "has_cegar_repaired", False):
            cegar_count += 1
        total_loops += res.total_iterations

        status_icon = "✅ PASS" if is_pk else "❌ FAIL"
        print(f"-> Kết quả: {status_icon} (Lượt {res.total_iterations}, {elapsed:.2f}s)")

        results.append({
            "task_name": task_name,
            "is_success": res.is_success,
            "total_iterations": res.total_iterations,
            "elapsed_sec": round(elapsed, 2),
            "pass_at_1": is_p1,
            "has_tamper": has_tamper,
        })

    n = len(task_keys)
    summary = {
        "method_name": method_name,
        "total_tasks": n,
        "passed_tasks": pass_at_k,
        "pass_at_1_count": pass_at_1,
        "pass_at_1_rate": round(pass_at_1 / n * 100, 1) if n > 0 else 0.0,
        "pass_at_k_count": pass_at_k,
        "pass_at_k_rate": round(pass_at_k / n * 100, 1) if n > 0 else 0.0,
        "spec_tampering_count": tamper_count,
        "spec_tampering_rate": round(tamper_count / n * 100, 1) if n > 0 else 0.0,
        "cegar_repaired_count": cegar_count,
        "avg_repair_loops": round(total_loops / n, 2) if n > 0 else 0.0,
        "avg_duration_sec": round(total_time / n, 1) if n > 0 else 0.0,
        "total_duration_sec": round(total_time, 1),
        "details": results
    }
    return summary


def execute_clover_ablation_experiment(
    model_name: str,
    task_keys: List[str],
    max_k: int = 3,
    timeout_sec: int = 15,
    progress_callback=None,
    preset_name: str = "custom",
) -> Dict[str, Any]:
    """Hàm lõi chạy thực nghiệm đối chuẩn Stanford Clover vs. Our System (dùng chung cho CLI và Web UI)."""
    flat_registry = get_flat_task_registry()
    agent = LLMAgent(model_name=model_name, temperature=0.0)
    engine = DafnyEngine(timeout_sec=timeout_sec)
    total_steps = len(task_keys) * 2

    # 1. Chạy cấu hình 1: Stanford Clover Baseline (Tắt tất cả module bảo trợ)
    clover_controller = PipelineController(
        agent=agent,
        engine=engine,
        max_k=max_k,
        verbose=False,
        enable_topology=False,
        enable_normalizer=False,
        enable_spec_locker=False,
        enable_semantic_hints=False,
        enable_cegar=False,
    )
    clover_summary = run_single_method(
        controller=clover_controller,
        task_keys=task_keys,
        flat_registry=flat_registry,
        method_name="Stanford Clover Baseline (2024)",
        progress_callback=progress_callback,
        step_offset=0,
        total_steps=total_steps,
    )

    # 2. Chạy cấu hình 2: Hệ Thống Đề Xuất (Full Neuro-Symbolic 4 Trục)
    our_controller = PipelineController(
        agent=agent,
        engine=engine,
        max_k=max_k,
        verbose=False,
        enable_topology=True,
        enable_normalizer=True,
        enable_spec_locker=True,
        enable_semantic_hints=True,
        enable_cegar=True,
    )
    our_summary = run_single_method(
        controller=our_controller,
        task_keys=task_keys,
        flat_registry=flat_registry,
        method_name="Our System (Full Neuro-Symbolic)",
        progress_callback=progress_callback,
        step_offset=len(task_keys),
        total_steps=total_steps,
    )

    # 3. Tạo bảng LaTeX
    latex_code = LaTeXExporter.generate_clover_comparison_table(
        clover_stats=clover_summary,
        our_stats=our_summary,
        caption=f"Ablation Study: Stanford Clover vs. Our System ({len(task_keys)} Tasks, {model_name})",
        label="tab:clover_comparison"
    )

    final_payload = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_name": model_name,
        "preset": preset_name,
        "total_tasks": len(task_keys),
        "clover_baseline": clover_summary,
        "our_system": our_summary,
        "latex_table": latex_code
    }

    # Lưu kiên cố xuống đĩa
    out_dir = Path(PROJECT_ROOT) / "artifacts" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "clover_vs_our_system_baseline.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2, ensure_ascii=False)

    return final_payload


def main():
    args = parse_args()
    model_name = MODEL_MAP.get(args.model.lower(), args.model)
    task_keys = select_tasks(args.preset)

    print(f"\n==================================================================")
    print(f"📊 ĐỐI CHUẨN ABLATION STUDY: STANFORD CLOVER (2024) VS. OUR SYSTEM")
    print(f"==================================================================")
    print(f"Mô hình LLM: {model_name}")
    print(f"Tập bài toán: {args.preset} ({len(task_keys)} bài)")
    print(f"Pass@K: K={args.max_k} | Timeout Z3: {args.timeout}s\n")

    final_payload = execute_clover_ablation_experiment(
        model_name=model_name,
        task_keys=task_keys,
        max_k=args.max_k,
        timeout_sec=args.timeout,
        preset_name=args.preset,
    )

    clover_summary = final_payload["clover_baseline"]
    our_summary = final_payload["our_system"]
    out_file = Path(PROJECT_ROOT) / "artifacts" / "results" / "clover_vs_our_system_baseline.json"

    print(f"\n=======================================================")
    print(f"📊 BẢNG TỔNG HỢP SO SÁNH ĐỐI CHUẨN (ABLATION SUMMARY)")
    print(f"=======================================================")
    print(f"{'Chỉ số':<26} | {'Stanford Clover':<16} | {'Hệ Thống Đề Xuất':<16}")
    print(f"{'-'*26}-+-{'-'*16}-+-{'-'*16}")
    print(f"{'Pass@1 Rate (%)':<26} | {clover_summary['pass_at_1_rate']:<16} | {our_summary['pass_at_1_rate']:<16}")
    print(f"{'Pass@3 Rate (%)':<26} | {clover_summary['pass_at_k_rate']:<16} | {our_summary['pass_at_k_rate']:<16}")
    print(f"{'Spec-Tampering Rate (%)':<26} | {clover_summary['spec_tampering_rate']:<16} | {our_summary['spec_tampering_rate']:<16}")
    print(f"{'Vòng lặp sửa lỗi TB':<26} | {clover_summary['avg_repair_loops']:<16} | {our_summary['avg_repair_loops']:<16}")
    print(f"{'Thời gian TB (s)':<26} | {clover_summary['avg_duration_sec']:<16} | {our_summary['avg_duration_sec']:<16}")
    print(f"{'Cứu nhờ CEGAR (bài)':<26} | {'-':<16} | {our_summary['cegar_repaired_count']:<16}")
    print(f"=======================================================")
    print(f"💾 Đã lưu kết quả JSON kiên cố tại: {out_file}")

    print(f"\n📋 MÃ BẢNG LATEX CHO BÀI BÁO (OVERLEAF):\n")
    print(final_payload["latex_table"])


if __name__ == "__main__":
    main()

