"""Module tính toán và kết xuất các chỉ số Nghiên cứu Khoa học (Evaluation Metrics Engine).

Đọc dữ liệu từ file CSV kết quả của Batch Runner, tính toán:
1. Pass@1 (Zero-shot Mathematical Accuracy)
2. Pass@K (Multi-turn Convergence Rate)
3. Repair Success Rate (RSR - Tỷ lệ tự sửa thành công)
4. Error Taxonomy Distribution (Ma trận phân loại lỗi logic Z3)
5. Thống kê độ trễ thời gian (Latency Statistics)
"""

import sys
# Cấu hình UTF-8 chuẩn cho console Windows
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# pyrefly: ignore [missing-import]
from rich.console import Console
# pyrefly: ignore [missing-import]
from rich.table import Table
# pyrefly: ignore [missing-import]
from rich.panel import Panel


def parse_args():
    """Bóc tách tham số dòng lệnh."""
    parser = argparse.ArgumentParser(description="Tính toán chỉ số NCKH từ kết quả kiểm định.")
    parser.add_argument(
        "--results_file",
        type=str,
        default=None,
        help="Đường dẫn đến file CSV kết quả (mặc định: lấy file mới nhất trong artifacts/results/)"
    )
    parser.add_argument(
        "--results_dir",
        type=str,
        default="artifacts/results",
        help="Thư mục chứa kết quả CSV (mặc định: artifacts/results)"
    )
    return parser.parse_args()


def find_latest_results_file(results_dir: str) -> Optional[Path]:
    """Tìm file CSV kết quả thực nghiệm mới nhất trong thư mục."""
    dir_path = Path(results_dir)
    if not dir_path.exists():
        return None
    csv_files = sorted(dir_path.glob("benchmark_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return csv_files[0] if csv_files else None


def load_benchmark_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Đọc dữ liệu từ file CSV kết quả."""
    rows: List[Dict[str, Any]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "task_name": r.get("task_name", ""),
                "model": r.get("model", ""),
                "is_success": r.get("is_success", "").lower() == "true",
                "total_iterations": int(r.get("total_iterations", 1)),
                "pass_at_1": int(r.get("pass_at_1", 0)),
                "pass_at_k": int(r.get("pass_at_k", 0)),
                "error_taxonomy": r.get("error_taxonomy", "None"),
                "execution_time_sec": float(r.get("execution_time_sec", 0.0)),
                "timestamp": r.get("timestamp", "")
            })
    return rows


def calculate_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tính toán toàn diện các chỉ số NCKH chuẩn hóa."""
    total_tasks = len(rows)
    if total_tasks == 0:
        return {}

    pass_1_count = sum(r["pass_at_1"] for r in rows)
    pass_k_count = sum(r["pass_at_k"] for r in rows)
    failed_at_1 = total_tasks - pass_1_count
    # Số bài sửa thành công = bài đạt ở K lượt nhưng không đạt ở lượt 1
    repaired_count = sum(1 for r in rows if r["pass_at_k"] == 1 and r["pass_at_1"] == 0)

    pass_1_rate = round(pass_1_count / total_tasks * 100, 2)
    pass_k_rate = round(pass_k_count / total_tasks * 100, 2)
    # Tỷ lệ sửa lỗi thành công tính trên tập bài bị fail ở lượt 1
    rsr_rate = round(repaired_count / failed_at_1 * 100, 2) if failed_at_1 > 0 else 100.0

    # Phân loại ma trận lỗi Z3 (chỉ tính trên các bài thất bại)
    failed_taxonomies = [r["error_taxonomy"] for r in rows if not r["is_success"]]
    error_counts = Counter(failed_taxonomies)

    # Thống kê thời gian thực thi
    total_time = sum(r["execution_time_sec"] for r in rows)
    avg_time = round(total_time / total_tasks, 2)
    pass_times = [r["execution_time_sec"] for r in rows if r["is_success"]]
    fail_times = [r["execution_time_sec"] for r in rows if not r["is_success"]]

    avg_pass_time = round(sum(pass_times) / len(pass_times), 2) if pass_times else 0.0
    avg_fail_time = round(sum(fail_times) / len(fail_times), 2) if fail_times else 0.0

    model_name = rows[0]["model"] if rows else "Unknown"

    return {
        "model": model_name,
        "total_tasks": total_tasks,
        "pass_at_1_count": pass_1_count,
        "pass_at_1_rate": pass_1_rate,
        "pass_at_k_count": pass_k_count,
        "pass_at_k_rate": pass_k_rate,
        "failed_at_1_count": failed_at_1,
        "repaired_count": repaired_count,
        "repair_success_rate": rsr_rate,
        "error_distribution": dict(error_counts),
        "total_execution_time_sec": round(total_time, 2),
        "avg_time_per_task_sec": avg_time,
        "avg_pass_time_sec": avg_pass_time,
        "avg_fail_time_sec": avg_fail_time,
    }


def export_markdown_report(metrics: Dict[str, Any], output_path: Path, raw_rows: List[Dict[str, Any]]):
    """Xuất file báo cáo Markdown chuẩn mực để copy vào bài báo NCKH."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"""# Báo Cáo Đánh Giá Thực Nghiệm (Scientific Evaluation Report)
**Đề tài**: Nghiên cứu khung sinh mã nguồn và tự sửa lỗi tự động loại bỏ ảo giác dựa trên kiểm định logic hình thức (Formal Verification-in-the-Loop)
**Thời gian kết xuất**: `{now_str}`
**Mô hình đánh giá**: `{metrics['model']}`

---

## 1. Bảng Chỉ Số Hiệu Năng Cốt Lõi (Core Metrics)

| Chỉ số nghiên cứu khoa học | Ký hiệu | Giá trị thực nghiệm | Ý nghĩa học thuật |
| :--- | :---: | :---: | :--- |
| **Quy mô tập bài toán** | $N$ | **{metrics['total_tasks']}** bài | Số lượng bài toán kiểm thử trong tập benchmark. |
| **Độ chính xác Zero-shot** | **Pass@1** | **{metrics['pass_at_1_rate']}%** ({metrics['pass_at_1_count']}/{metrics['total_tasks']}) | Tỷ lệ vượt qua kiểm định Z3 ngay lần sinh đầu tiên. |
| **Độ chính xác khép kín** | **Pass@K** | **{metrics['pass_at_k_rate']}%** ({metrics['pass_at_k_count']}/{metrics['total_tasks']}) | Tỷ lệ thành công sau chu trình tự sửa lỗi Actor-Critic. |
| **Tỷ lệ tự sửa thành công** | **RSR** | **{metrics['repair_success_rate']}%** ({metrics['repaired_count']}/{metrics['failed_at_1_count']}) | Tỷ lệ sửa đúng trên tập các bài ban đầu bị Z3 từ chối. |
| **Thời gian trung bình** | $T_{{avg}}$ | **{metrics['avg_time_per_task_sec']}s** | Thời gian trung bình mỗi bài (Pass: {metrics['avg_pass_time_sec']}s, Fail: {metrics['avg_fail_time_sec']}s). |

---

## 2. Ma Trận Phân Loại Lỗi Z3 Solver (Error Taxonomy Matrix)

Bảng thống kê các dạng lỗi logic toán học mà bộ giải Z3 SMT Solver phát hiện:

| Dạng lỗi logic (Error Category) | Số lượng phát hiện | Tỷ lệ (%) | Nguyên nhân bản chất |
| :--- | :---: | :---: | :--- |
"""
    failed_total = metrics['total_tasks'] - metrics['pass_at_k_count']
    if metrics['error_distribution']:
        for cat, cnt in metrics['error_distribution'].items():
            pct = round(cnt / failed_total * 100, 2) if failed_total else 0
            md_content += f"| `{cat}` | {cnt} | {pct}% | Vi phạm chứng minh hình thức hoặc ngữ pháp logic. |\n"
    else:
        md_content += "| *Không có lỗi (Tất cả đều Pass)* | 0 | 0% | Mã nguồn đạt Zero-Hallucination 100%. |\n"

    md_content += f"""
---

## 3. Danh Sách Chi Tiết Từng Bài Toán

| STT | Bài toán | Trạng thái | Lượt K | Pass@1 | Lỗi Z3 cuối | Thời gian (s) |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: |
"""
    for idx, r in enumerate(raw_rows, 1):
        status = "**PASS**" if r["is_success"] else "*FAIL*"
        p1 = "✅" if r["pass_at_1"] else "❌"
        md_content += f"| {idx} | `{r['task_name']}` | {status} | {r['total_iterations']} | {p1} | `{r['error_taxonomy']}` | {r['execution_time_sec']}s |\n"

    output_path.write_text(md_content, encoding="utf-8")


def main():
    console = Console()
    args = parse_args()

    # Xác định file kết quả CSV
    if args.results_file:
        csv_path = Path(args.results_file)
    else:
        csv_path = find_latest_results_file(args.results_dir)

    if not csv_path or not csv_path.exists():
        console.print(f"[bold red][LỖI][/bold red] Không tìm thấy file CSV kết quả nào trong: {args.results_dir}")
        return

    console.print(Panel(f"[bold cyan]Đang phân tích dữ liệu thực nghiệm từ:[/bold cyan] {csv_path}", title="EVALUATION METRICS ENGINE"))

    rows = load_benchmark_csv(csv_path)
    metrics = calculate_metrics(rows)

    if not metrics:
        console.print("[bold red][LỖI][/bold red] Dữ liệu CSV rỗng.")
        return

    # In bảng chỉ số hiệu năng
    table = Table(title="BẢNG CHỈ SỐ NGHIÊN CỨU KHOA HỌC (EVALUATION METRICS)", show_header=True)
    table.add_column("Chỉ số khoa học", style="bold cyan")
    table.add_column("Ký hiệu", justify="center", style="yellow")
    table.add_column("Giá trị", justify="center", style="bold green")
    table.add_column("Diễn giải học thuật", style="dim")

    table.add_row("Quy mô bài toán", "N", f"{metrics['total_tasks']} bài", "Tổng số bài toán benchmark")
    table.add_row("Độ chính xác Zero-shot", "Pass@1", f"{metrics['pass_at_1_rate']}%", f"{metrics['pass_at_1_count']}/{metrics['total_tasks']} bài đúng ngay lần đầu")
    table.add_row("Độ chính xác Pass@K", f"Pass@K", f"{metrics['pass_at_k_rate']}%", f"{metrics['pass_at_k_count']}/{metrics['total_tasks']} bài đúng sau tự sửa")
    table.add_row("Tỷ lệ tự sửa thành công", "RSR", f"{metrics['repair_success_rate']}%", f"Cứu thành công {metrics['repaired_count']}/{metrics['failed_at_1_count']} bài fail ban đầu")
    table.add_row("Thời gian trung bình", "T_avg", f"{metrics['avg_time_per_task_sec']}s", f"Pass: {metrics['avg_pass_time_sec']}s | Fail: {metrics['avg_fail_time_sec']}s")

    console.print(table)

    # In ma trận phân loại lỗi Z3
    if metrics["error_distribution"]:
        err_table = Table(title="MA TRẬN PHÂN LOẠI LỖI LOGIC Z3 (ERROR TAXONOMY MATRIX)", show_header=True)
        err_table.add_column("Nhóm lỗi logic Z3 phát hiện", style="bold red")
        err_table.add_column("Số lần xuất hiện", justify="center")
        err_table.add_column("Tỷ lệ trên tổng bài Fail", justify="center", style="yellow")

        failed_total = metrics['total_tasks'] - metrics['pass_at_k_count']
        for cat, cnt in metrics["error_distribution"].items():
            pct = round(cnt / failed_total * 100, 2) if failed_total else 0
            err_table.add_row(cat, str(cnt), f"{pct}%")
        console.print(err_table)

    # Xuất các file báo cáo Markdown và JSON
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = csv_path.parent
    md_file = results_dir / f"metrics_summary_{timestamp_str}.md"
    json_file = results_dir / f"metrics_summary_{timestamp_str}.json"

    export_markdown_report(metrics, md_file, rows)
    with open(json_file, "w", encoding="utf-8") as jf:
        json.dump(metrics, jf, ensure_ascii=False, indent=2)

    console.print(f"\n[bold green]✓ Đã kết xuất báo cáo Markdown thành công tại:[/bold green] [cyan]{md_file}[/cyan]")
    console.print(f"[bold green]✓ Đã lưu dữ liệu thống kê JSON tại:[/bold green] [cyan]{json_file}[/cyan]\n")


if __name__ == "__main__":
    main()
