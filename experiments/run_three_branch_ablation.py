"""Thực nghiệm Đối chứng 3 Nhánh Khoa học (Three-Branch Controlled Ablation Study).

Phục vụ Bảng 1 bài báo NCKH CYSG 2027 (HUTECH):
- Nhánh A: Zero-shot Baseline (K=1, sinh 1 lần, không lặp sửa)
- Nhánh B: Raw Verifier Feedback (K=3, chỉ nhận phản hồi lỗi thô từ Z3, tắt mọi module bảo trợ)
- Nhánh C: Hệ thống Đề xuất (Full FVIL: Topology Directive + Syntax Normalizer + SpecLocker + CEGAR)

Tập dữ liệu: 18 bài toán phân tầng đại diện 6 họ thuật toán (Số học, Mảng, Chuỗi, Lý thuyết số, Sắp xếp, Quy nạp Cây & DSLK).
Mô hình: ollama/qwen2.5-coder:7b (100% Local Offline).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Cấu hình UTF-8 chuẩn cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# pyrefly: ignore [missing-import]
from rich.console import Console
# pyrefly: ignore [missing-import]
from rich.table import Table

from agents.llm_agent import LLMAgent
from core.dafny_engine import DafnyEngine
from core.pipeline_controller import PipelineController, PipelineResult
from core.verification_cache import VerificationCache

STRATIFIED_18_TASKS = [
    # 1. Số học / Giải tích
    ("clover_abs_val", "data/benchmarks/clover/abs_val.dfy", "Số học"),
    ("clover_sum_to_n", "data/benchmarks/clover/sum_to_n.dfy", "Số học"),
    ("humaneval_002_truncate", "data/benchmarks/humaneval_dafny/002-truncate.dfy", "Số học"),
    # 2. Mảng 1D & Tìm kiếm
    ("clover_find_min", "data/benchmarks/clover/find_min.dfy", "Mảng & Tìm kiếm"),
    ("clover_linear_search", "data/benchmarks/clover/linear_search.dfy", "Mảng & Tìm kiếm"),
    ("advanced_binary_search", "data/benchmarks/advanced/binary_search.dfy", "Mảng & Tìm kiếm"),
    # 3. Chuỗi & Vòng lặp lồng
    ("humaneval_010_is_palindrome", "data/benchmarks/humaneval_dafny/010-is_palindrome.dfy", "Chuỗi & Vòng lặp lồng"),
    ("humaneval_000_has_close_elements", "data/benchmarks/humaneval_dafny/000-has_close_elements.dfy", "Chuỗi & Vòng lặp lồng"),
    # 4. Lý thuyết số & Bậc cao
    ("humaneval_013_gcd", "data/benchmarks/humaneval_dafny/013-greatest_common_divisor.dfy", "Lý thuyết số"),
    ("humaneval_031_is_prime", "data/benchmarks/humaneval_dafny/031-is-prime.dfy", "Lý thuyết số"),
    ("humaneval_077_iscube", "data/benchmarks/humaneval_dafny/077-iscube.dfy", "Lý thuyết số"),
    # 5. Sắp xếp & Biến đổi mảng
    ("humaneval_088_sort_array", "data/benchmarks/humaneval_dafny/088-sort_array.dfy", "Sắp xếp & Đa tập"),
    ("advanced_array_reverse", "data/benchmarks/advanced/array_reverse.dfy", "Sắp xếp & Đa tập"),
    ("advanced_sorted_insert", "data/benchmarks/advanced/sorted_insert.dfy", "Sắp xếp & Đa tập"),
    # 6. Quy nạp Cây & Danh sách
    ("inductive_bst_search", "data/benchmarks/advanced_inductive/bst_search.dfy", "Quy nạp Cấu trúc"),
    ("inductive_bst_insert", "data/benchmarks/advanced_inductive/bst_insert.dfy", "Quy nạp Cấu trúc"),
    ("inductive_tree_size_height", "data/benchmarks/advanced_inductive/tree_size_height.dfy", "Quy nạp Cấu trúc"),
    ("inductive_linked_list_stats", "data/benchmarks/advanced_inductive/linked_list_stats.dfy", "Quy nạp Cấu trúc"),
]


def run_experiment(model_name: str = "ollama/qwen2.5-coder:7b", max_k: int = 3, timeout_sec: int = 30):
    console = Console()
    console.print("\n[bold cyan]=====================================================================[/bold cyan]")
    console.print("[bold yellow] THỰC NGHIỆM ĐỐI CHỨNG 3 NHÁNH KHOA HỌC (CYSG 2027 ABLATION STUDY)[/bold yellow]")
    console.print("[bold cyan]=====================================================================[/bold cyan]")
    console.print(f"Mô hình: [bold green]{model_name}[/bold green] (Local Offline)")
    console.print(f"Số bài toán phân tầng: [bold green]{len(STRATIFIED_18_TASKS)} bài[/bold green] (6 họ thuật toán)")
    console.print(f"Giới hạn lặp: [bold green]K = {max_k}[/bold green] | Timeout Z3: [bold green]{timeout_sec}s[/bold green]\n")

    agent = LLMAgent(model_name=model_name, temperature=0.0)
    engine = DafnyEngine(timeout_sec=timeout_sec, cache=VerificationCache())

    # Controller cho Nhánh B (Raw Feedback: Tắt toàn bộ module bảo trợ)
    controller_branch_b = PipelineController(
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

    # Controller cho Nhánh C (Full FVIL System: Bật toàn bộ 4 trục bảo trợ)
    controller_branch_c = PipelineController(
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

    task_results = []

    for idx, (task_id, rel_path, category) in enumerate(STRATIFIED_18_TASKS, 1):
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            console.print(f"[red][BỎ QUA][/red] Không tìm thấy file: {rel_path}")
            continue

        raw_spec = full_path.read_text(encoding="utf-8")
        console.print(f"[bold cyan][{idx}/{len(STRATIFIED_18_TASKS)}][/bold cyan] Đang chạy bài: [bold]{task_id}[/bold] ({category})...")

        # 1. Chạy Nhánh B (Đồng thời trích xuất Nhánh A từ Lượt 1)
        t0_b = time.time()
        res_b = controller_branch_b.run_task(raw_spec=raw_spec, task_name=task_id)
        elapsed_b = round(time.time() - t0_b, 2)

        # Nhánh A: Kết quả Lượt 1 của Baseline (Zero-shot)
        branch_a_pass1 = len(res_b.history) > 0 and res_b.history[0].is_verified
        # Nhánh B: Kết quả sau tối đa K lượt của Raw Feedback
        branch_b_pass_k = res_b.is_success
        branch_b_loops = res_b.total_iterations
        branch_b_tamper = any(not log.is_spec_valid for log in res_b.history)

        # 2. Chạy Nhánh C (Hệ thống đề xuất Full Neuro-Symbolic)
        t0_c = time.time()
        res_c = controller_branch_c.run_task(raw_spec=raw_spec, task_name=task_id)
        elapsed_c = round(time.time() - t0_c, 2)

        branch_c_pass1 = len(res_c.history) > 0 and res_c.history[0].is_verified
        branch_c_pass_k = res_c.is_success
        branch_c_loops = res_c.total_iterations
        branch_c_tamper = any(not log.is_spec_valid for log in res_c.history)

        status_a = "✅" if branch_a_pass1 else "❌"
        status_b = "✅" if branch_b_pass_k else "❌"
        status_c = "✅" if branch_c_pass_k else "❌"

        console.print(f"   -> Nhánh A (Zero-shot): {status_a} | Nhánh B (Raw Feedback): {status_b} (K={branch_b_loops}) | Nhánh C (Full FVIL): {status_c} (K={branch_c_loops})")

        task_results.append({
            "task_id": task_id,
            "category": category,
            "rel_path": rel_path,
            "branch_a_pass1": branch_a_pass1,
            "branch_b_pass_k": branch_b_pass_k,
            "branch_b_loops": branch_b_loops,
            "branch_b_tamper": branch_b_tamper,
            "branch_b_elapsed_sec": elapsed_b,
            "branch_c_pass1": branch_c_pass1,
            "branch_c_pass_k": branch_c_pass_k,
            "branch_c_loops": branch_c_loops,
            "branch_c_tamper": branch_c_tamper,
            "branch_c_elapsed_sec": elapsed_c,
        })

    # Tổng kết số liệu khoa học
    total = len(task_results)
    if total == 0:
        console.print("[red]Không có kết quả nào được tạo ra![/red]")
        return

    n_a_pass1 = sum(1 for r in task_results if r["branch_a_pass1"])
    n_b_pass_k = sum(1 for r in task_results if r["branch_b_pass_k"])
    n_b_tamper = sum(1 for r in task_results if r["branch_b_tamper"])
    avg_b_loops = round(sum(r["branch_b_loops"] for r in task_results) / total, 2)

    n_c_pass1 = sum(1 for r in task_results if r["branch_c_pass1"])
    n_c_pass_k = sum(1 for r in task_results if r["branch_c_pass_k"])
    n_c_tamper = sum(1 for r in task_results if r["branch_c_tamper"])
    avg_c_loops = round(sum(r["branch_c_loops"] for r in task_results) / total, 2)

    # Hiển thị bảng tổng kết lên Console
    summary_table = Table(title="BẢNG ĐỐI CHỨNG KHOA HỌC 3 NHÁNH THỰC NGHIỆM (TABLE 1 - CYSG 2027)", show_header=True)
    summary_table.add_column("Cấu hình Thực nghiệm (Method)", style="bold cyan")
    summary_table.add_column("Pass@1", justify="center")
    summary_table.add_column("Pass@3 (Pass@K)", justify="center", style="bold green")
    summary_table.add_column("Spec Tampering", justify="center", style="yellow")
    summary_table.add_column("Số vòng sửa TB", justify="center")

    summary_table.add_row(
        "Nhánh A: Zero-shot Baseline (K=1)",
        f"{n_a_pass1}/{total} ({n_a_pass1/total*100:.1f}%)",
        "-",
        "-",
        "1.00"
    )
    summary_table.add_row(
        "Nhánh B: Raw Verifier Feedback (K=3)",
        f"{n_a_pass1}/{total} ({n_a_pass1/total*100:.1f}%)",
        f"{n_b_pass_k}/{total} ({n_b_pass_k/total*100:.1f}%)",
        f"{n_b_tamper}/{total} ({n_b_tamper/total*100:.1f}%)",
        str(avg_b_loops)
    )
    summary_table.add_row(
        "Nhánh C: Hệ Thống Đề Xuất Full FVIL (K=3)",
        f"{n_c_pass1}/{total} ({n_c_pass1/total*100:.1f}%)",
        f"{n_c_pass_k}/{total} ({n_c_pass_k/total*100:.1f}%)",
        f"{n_c_tamper}/{total} ({n_c_tamper/total*100:.1f}%)",
        str(avg_c_loops)
    )
    console.print("\n")
    console.print(summary_table)

    # Xuất dữ liệu ra file JSON & CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = PROJECT_ROOT / "artifacts" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"ablation_study_3branches_{timestamp}.json"
    csv_path = out_dir / f"ablation_study_3branches_{timestamp}.csv"

    output_payload = {
        "metadata": {
            "timestamp": timestamp,
            "model": model_name,
            "max_k": max_k,
            "timeout_sec": timeout_sec,
            "total_tasks": total,
        },
        "summary": {
            "branch_a_pass1_rate": round(n_a_pass1 / total * 100, 1),
            "branch_b_pass3_rate": round(n_b_pass_k / total * 100, 1),
            "branch_b_tamper_rate": round(n_b_tamper / total * 100, 1),
            "branch_b_avg_loops": avg_b_loops,
            "branch_c_pass1_rate": round(n_c_pass1 / total * 100, 1),
            "branch_c_pass3_rate": round(n_c_pass_k / total * 100, 1),
            "branch_c_tamper_rate": round(n_c_tamper / total * 100, 1),
            "branch_c_avg_loops": avg_c_loops,
        },
        "tasks": task_results
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(task_results[0].keys()))
        writer.writeheader()
        writer.writerows(task_results)

    console.print(f"\n[green]Đã lưu báo cáo JSON:[/green] {json_path}")
    console.print(f"[green]Đã lưu bảng CSV:[/green] {csv_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy thực nghiệm đối chứng 3 nhánh CYSG 2027.")
    parser.add_argument("--model", type=str, default="ollama/qwen2.5-coder:7b", help="Mô hình LLM")
    parser.add_argument("--max-k", type=int, default=3, help="Số lượt lặp tối đa")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout Z3 (giây)")
    args = parser.parse_args()

    run_experiment(model_name=args.model, max_k=args.max_k, timeout_sec=args.timeout)
