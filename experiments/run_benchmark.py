"""Module thực nghiệm tự động chạy hàng loạt bài toán Benchmark (Batch Runner).

Duyệt qua các bài toán trong CloverBench / HumanEval-Dafny, điều phối quy trình Pass@K,
hiển thị tiến trình trực quan bằng Rich và xuất dữ liệu ra file CSV / log vết Z3.
"""

import sys
# Cấu hình UTF-8 chuẩn cho console Windows
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import yaml
# pyrefly: ignore [missing-import]
from rich.console import Console
# pyrefly: ignore [missing-import]
from rich.table import Table
# pyrefly: ignore [missing-import]
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from core.dafny_engine import DafnyEngine
from agents.llm_agent import LLMAgent
from core.pipeline_controller import PipelineController, PipelineResult


def parse_args():
    """Bóc tách tham số dòng lệnh phục vụ thực nghiệm NCKH."""
    parser = argparse.ArgumentParser(description="Chạy thực nghiệm tự động Formal Verification-in-the-Loop.")
    parser.add_argument(
        "--config",
        type=str,
        default="configs/experiment_config.yaml",
        help="Đường dẫn đến file cấu hình YAML"
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default=None,
        help="Tên thư mục benchmark (vd: clover, humaneval_dafny)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Tên mô hình LLM (mặc định đọc từ config)"
    )
    parser.add_argument(
        "--max_k",
        type=int,
        default=None,
        help="Số lượt lặp tự sửa lỗi tối đa Pass@K"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số lượng bài toán kiểm thử nhanh (mặc định: chạy hết)"
    )
    return parser.parse_args()


def load_config(config_path: str) -> Dict[str, Any]:
    """Tải nội dung file cấu hình YAML."""
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    console = Console()
    args = parse_args()
    config = load_config(args.config)

    # Trích xuất tham số ưu tiên theo thứ tự: CLI -> Config YAML -> Mặc định
    exp_cfg = config.get("experiment", {})
    models_cfg = config.get("models", {})
    dataset_cfg = config.get("dataset", {})

    benchmark_name = args.benchmark or dataset_cfg.get("benchmark_suite", "clover")
    model_name = args.model or models_cfg.get("generator", "ollama/qwen2.5-coder:7b")
    max_k = args.max_k or exp_cfg.get("max_iterations_k", 3)
    limit = args.limit or dataset_cfg.get("sample_limit", None)
    timeout_sec = exp_cfg.get("dafny_timeout_seconds", 15)

    # Xác định thư mục dữ liệu bài toán
    benchmarks_dir = Path("data/benchmarks") / benchmark_name
    if not benchmarks_dir.exists():
        console.print(f"[bold red][LỖI][/bold red] Thư mục benchmark không tồn tại: {benchmarks_dir}")
        return

    task_files = sorted(list(benchmarks_dir.glob("*.dfy")))
    if not task_files:
        console.print(f"[bold red][LỖI][/bold red] Không tìm thấy file .dfy nào trong: {benchmarks_dir}")
        return

    if limit and limit > 0:
        task_files = task_files[:limit]

    # Khởi tạo engine & agent
    engine = DafnyEngine(timeout_sec=timeout_sec)
    if not engine.is_available():
        console.print("[bold red][LỖI MÔI TRƯỜNG][/bold red] Chưa tìm thấy Dafny binary trên máy!")
        return

    agent = LLMAgent(model_name=model_name)
    controller = PipelineController(agent=agent, engine=engine, max_k=max_k, verbose=False)

    # In thông tin thực nghiệm ban đầu
    info_table = Table(title="THÔNG SỐ THỰC NGHIỆM FORMAL VERIFICATION-IN-THE-LOOP", show_header=True)
    info_table.add_column("Tham số", style="cyan", no_wrap=True)
    info_table.add_column("Giá trị", style="magenta")
    info_table.add_row("Tập Benchmark", f"{benchmark_name} ({len(task_files)} bài toán)")
    info_table.add_row("Mô hình LLM", model_name)
    info_table.add_row("Số lượt lặp Pass@K", f"K = {max_k}")
    info_table.add_row("Timeout Solver Z3", f"{timeout_sec} giây/lượt")
    console.print(info_table)

    # Chuẩn bị thư mục xuất kết quả và log vết
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("artifacts/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_file = results_dir / f"benchmark_{benchmark_name}_{timestamp_str}.csv"

    logs_dir = Path("artifacts/logs") / f"run_{timestamp_str}"
    logs_dir.mkdir(parents=True, exist_ok=True)

    results_data: List[Dict[str, Any]] = []

    # Tiến hành chạy benchmark với thanh tiến trình trực quan
    console.print("\n[bold green]>>> BẮT ĐẦU CHẠY BENCHMARK TỰ ĐỘNG...[/bold green]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        bench_task = progress.add_task("[cyan]Đang kiểm định bài toán...", total=len(task_files))

        for task_file in task_files:
            task_name = task_file.stem
            progress.update(bench_task, description=f"[cyan]Đang xử lý: [bold]{task_name}[/bold]...")

            start_t = time.time()
            raw_spec = task_file.read_text(encoding="utf-8")
            res: PipelineResult = controller.run_task(raw_spec=raw_spec, task_name=task_name)
            elapsed_sec = round(time.time() - start_t, 2)

            # Lưu log vết chi tiết của từng bài toán
            task_log_file = logs_dir / f"{task_name}.log"
            with open(task_log_file, "w", encoding="utf-8") as lf:
                lf.write(f"=== BÀI TOÁN: {task_name} ===\n")
                lf.write(f"Mô hình: {model_name}\nThời gian chạy: {elapsed_sec}s\n")
                lf.write(f"Kết quả cuối: {'PASS' if res.is_success else 'FAIL'}\n\n")
                for item in res.history:
                    lf.write(f"--- LƯỢT {item.iteration} ---\n")
                    lf.write(f"Spec Valid: {item.is_spec_valid} | Verified: {item.is_verified}\n")
                    lf.write(f"Error Taxonomy: {item.error_taxonomy}\n")
                    lf.write(f"Error Message: {item.error_message}\n")
                    lf.write(f"Code:\n{item.code}\n\n")

            # Thu thập chỉ số thống kê
            pass_at_1 = 1 if (res.is_success and res.total_iterations == 1) else 0
            pass_at_k = 1 if res.is_success else 0
            last_err_tax = res.history[-1].error_taxonomy if (res.history and not res.is_success) else "None"

            results_data.append({
                "task_name": task_name,
                "model": model_name,
                "is_success": res.is_success,
                "total_iterations": res.total_iterations,
                "pass_at_1": pass_at_1,
                "pass_at_k": pass_at_k,
                "error_taxonomy": last_err_tax,
                "execution_time_sec": elapsed_sec,
                "timestamp": timestamp_str
            })

            progress.advance(bench_task)

    # Ghi toàn bộ kết quả ra file CSV
    if results_data:
        fieldnames = list(results_data[0].keys())
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results_data)

    # Hiển thị bảng tổng hợp kết quả lên Terminal
    summary_table = Table(title="KẾT QUẢ THỰC NGHIỆM ĐÁNH GIÁ (BENCHMARK SUMMARY)", show_header=True)
    summary_table.add_column("STT", justify="center", style="dim")
    summary_table.add_column("Bài toán", style="bold")
    summary_table.add_column("Trạng thái", justify="center")
    summary_table.add_column("Lượt thử (K)", justify="center")
    summary_table.add_column("Pass@1", justify="center")
    summary_table.add_column("Lỗi Z3 phát hiện", style="yellow")
    summary_table.add_column("Thời gian (s)", justify="right")

    total_tasks = len(results_data)
    total_pass_1 = sum(r["pass_at_1"] for r in results_data)
    total_pass_k = sum(r["pass_at_k"] for r in results_data)

    for idx, r in enumerate(results_data, 1):
        status_str = "[bold green]PASS[/bold green]" if r["is_success"] else "[bold red]FAIL[/bold red]"
        p1_str = "✅" if r["pass_at_1"] else "❌"
        summary_table.add_row(
            str(idx),
            r["task_name"],
            status_str,
            str(r["total_iterations"]),
            p1_str,
            r["error_taxonomy"],
            str(r["execution_time_sec"])
        )

    console.print("\n")
    console.print(summary_table)

    # In các chỉ số tổng quát
    p1_rate = round(total_pass_1 / total_tasks * 100, 2) if total_tasks else 0
    pk_rate = round(total_pass_k / total_tasks * 100, 2) if total_tasks else 0
    console.print(f"\n[bold]TỔNG KẾT ĐÁNH GIÁ:[/bold]")
    console.print(f"- Tổng số bài toán kiểm thử: [bold]{total_tasks}[/bold]")
    console.print(f"- Tỷ lệ đạt ngay lần đầu (Pass@1): [bold green]{p1_rate}%[/bold green] ({total_pass_1}/{total_tasks})")
    console.print(f"- Tỷ lệ đạt sau K vòng lặp (Pass@{max_k}): [bold green]{pk_rate}%[/bold green] ({total_pass_k}/{total_tasks})")
    console.print(f"- File CSV kết quả đã lưu tại: [cyan]{csv_file}[/cyan]")
    console.print(f"- Thư mục log chi tiết tại: [cyan]{logs_dir}[/cyan]\n")


if __name__ == "__main__":
    main()
