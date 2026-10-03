"""Module tiện ích hỗ trợ giao diện Web Demo Streamlit.

Cung cấp các hàm tải bài toán mẫu, tạo hiển thị so sánh mã nguồn (code diff)
và trích xuất dữ liệu khoa học từ các file kết quả thực nghiệm.
"""

import difflib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def get_benchmark_tasks() -> Dict[str, Dict[str, str]]:
    """Trả về danh mục các bài toán benchmark phân loại theo nhóm."""
    tasks = {
        "Clover Benchmark (Stanford)": {
            "abs_val - Tìm giá trị tuyệt đối": "data/benchmarks/clover/abs_val.dfy",
            "find_min - Tìm giá trị nhỏ nhất trong mảng": "data/benchmarks/clover/find_min.dfy",
            "linear_search - Tìm kiếm phần tử tuyến tính": "data/benchmarks/clover/linear_search.dfy",
            "sample_max - Tìm cực đại trong 3 số": "data/benchmarks/clover/sample_max.dfy",
            "sign_function - Hàm dấu số nguyên": "data/benchmarks/clover/sign_function.dfy",
            "sum_to_n - Tính tổng cấp số cộng 0..n": "data/benchmarks/clover/sum_to_n.dfy",
        },
        "HumanEval-Dafny (JetBrains)": {
            "002-truncate - Tách phần thập phân số thực": "data/benchmarks/humaneval_dafny/002-truncate.dfy",
            "013-greatest_common_divisor - Thuật toán Euclid tìm GCD": "data/benchmarks/humaneval_dafny/013-greatest_common_divisor.dfy",
            "031-is-prime - Kiểm tra số nguyên tố tuyến tính": "data/benchmarks/humaneval_dafny/031-is-prime.dfy",
            "035-max-element - Cực đại mảng với bất biến song hành": "data/benchmarks/humaneval_dafny/035-max-element.dfy",
            "052-below-threshold - Kiểm tra ngưỡng toàn thể của mảng": "data/benchmarks/humaneval_dafny/052-below-threshold.dfy",
            "055-fib - Thuật toán lặp đồng bộ đệ quy Fibonacci": "data/benchmarks/humaneval_dafny/055-fib.dfy",
            "000-has_close_elements - Kiểm tra khoảng cách 2 phần tử": "data/benchmarks/humaneval_dafny/000-has_close_elements.dfy",
            "010-is_palindrome - Kiểm tra chuỗi đối xứng": "data/benchmarks/humaneval_dafny/010-is_palindrome.dfy",
            "077-iscube - Kiểm tra số lập phương": "data/benchmarks/humaneval_dafny/077-iscube.dfy",
            "088-sort_array - Sắp xếp mảng": "data/benchmarks/humaneval_dafny/088-sort_array.dfy",
        },
        "Advanced Algorithms (Mở Rộng)": {
            "binary_search - Tìm kiếm nhị phân": "data/benchmarks/advanced/binary_search.dfy",
            "linear_search_last - Tìm vị trí phần tử cuối cùng": "data/benchmarks/advanced/linear_search_last.dfy",
            "find_first_negative - Tìm số âm đầu tiên": "data/benchmarks/advanced/find_first_negative.dfy",
            "array_reverse - Đảo ngược dãy tuần tự": "data/benchmarks/advanced/array_reverse.dfy",
            "is_array_sorted - Kiểm tra dãy sắp xếp tăng dần": "data/benchmarks/advanced/is_array_sorted.dfy",
            "remove_element - Lọc bỏ phần tử theo giá trị": "data/benchmarks/advanced/remove_element.dfy",
            "copy_array - Sao chép dãy bảo toàn phần tử": "data/benchmarks/advanced/copy_array.dfy",
            "count_elements - Đếm số lần xuất hiện đệ quy": "data/benchmarks/advanced/count_elements.dfy",
            "sum_positive - Tính tổng các số nguyên dương": "data/benchmarks/advanced/sum_positive.dfy",
            "product_of_array - Tính tích các phần tử trong dãy": "data/benchmarks/advanced/product_of_array.dfy",
            "all_unique - Kiểm tra dãy không có phần tử trùng": "data/benchmarks/advanced/all_unique.dfy",
            "matrix_row_sum - Tính tổng từng hàng ma trận 2D": "data/benchmarks/advanced/matrix_row_sum.dfy",
            "matrix_diagonal_sum - Tính tổng đường chéo ma trận vuông": "data/benchmarks/advanced/matrix_diagonal_sum.dfy",
            "sorted_insert - Chèn phần tử vào dãy đã sắp xếp": "data/benchmarks/advanced/sorted_insert.dfy",
        }
    }
    return tasks


# Danh sách bài toán mục tiêu khoa học cốt lõi đã đạt chứng minh 100% (16/16 bài - 100.0%)
TARGET_12_TASK_NAMES = {
    # Clover Benchmark (6/6)
    "abs_val",
    "find_min",
    "linear_search",
    "sample_max",
    "sign_function",
    "sum_to_n",
    # HumanEval-Dafny (10/10)
    "000-has_close_elements",
    "002-truncate",
    "010-is_palindrome",
    "013-greatest_common_divisor",
    "031-is-prime",
    "035-max-element",
    "052-below-threshold",
    "055-fib",
    "077-iscube",
    "088-sort_array",
}





def get_flat_task_registry() -> Dict[str, dict]:
    """Trả về bảng danh mục phẳng của toàn bộ 30 bài toán thuộc 3 tập benchmark.
    
    Khóa (Key) là chuỗi hiển thị có gắn thẻ tập dữ liệu để người dùng dễ chọn,
    Giá trị (Value) chứa metadata của bài toán: tên mã, đường dẫn, tập dữ liệu, cờ target.
    """
    groups = get_benchmark_tasks()
    registry = {}

    for group_name, tasks in groups.items():
        if "Clover" in group_name:
            tag = "Clover"
        elif "HumanEval" in group_name:
            tag = "HumanEval"
        else:
            tag = "Advanced"

        for label, rel_path in tasks.items():
            short_name = label.split(" - ")[0].strip()
            display_label = f"[{tag}] {label}"
            is_target = short_name in TARGET_12_TASK_NAMES
            registry[display_label] = {
                "display_label": display_label,
                "short_name": short_name,
                "label": label,
                "rel_path": rel_path,
                "group": tag,
                "group_full": group_name,
                "is_target": is_target,
            }
    return registry


def get_preset_labels(preset_type: str = "target_12") -> List[str]:
    """Lấy danh sách các nhãn bài toán theo bộ thiết lập sẵn (preset).
    
    Tham số preset_type:
    - 'target_12': 16 bài toán mục tiêu cốt lõi (Clover + HumanEval)
    - 'clover': Toàn bộ 6 bài toán tập Clover
    - 'humaneval': Toàn bộ 10 bài toán tập HumanEval
    - 'advanced': Toàn bộ 14 bài toán tập Mở Rộng Advanced
    - 'all': Toàn bộ 30 bài toán trong kho benchmark
    """
    registry = get_flat_task_registry()
    if preset_type == "target_12":
        return [k for k, v in registry.items() if v["is_target"]]
    elif preset_type == "clover":
        return [k for k, v in registry.items() if v["group"] == "Clover"]
    elif preset_type == "humaneval":
        return [k for k, v in registry.items() if v["group"] == "HumanEval"]
    elif preset_type == "advanced":
        return [k for k, v in registry.items() if v["group"] == "Advanced"]
    elif preset_type == "all":
        return list(registry.keys())
    return []


def load_task_spec(rel_path: str) -> str:
    """Đọc nội dung tệp đặc tả Dafny."""
    full_path = PROJECT_ROOT / rel_path
    if not full_path.is_file():
        return ""
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_code_diff_html(original_code: str, repaired_code: str) -> str:
    """Tạo bảng HTML trực quan hóa sự khác biệt giữa mã lỗi và mã đã sửa."""
    orig_lines = original_code.splitlines()
    repaired_lines = repaired_code.splitlines()

    diff = list(difflib.ndiff(orig_lines, repaired_lines))

    html = [
        '<div style="font-family: Consolas, monospace; font-size: 13px; line-height: 1.5; '
        'background-color: #0d1117; color: #c9d1d9; padding: 12px; border-radius: 8px; '
        'border: 1px solid #30363d; overflow-x: auto; max-height: 480px;">'
    ]

    for line in diff:
        marker = line[:2]
        content = line[2:]
        safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        if marker == "- ":
            html.append(
                f'<div style="background-color: rgba(248, 81, 73, 0.18); color: #ff7b72; '
                f'padding: 1px 6px; border-radius: 3px;">- {safe_content}</div>'
            )
        elif marker == "+ ":
            html.append(
                f'<div style="background-color: rgba(63, 185, 80, 0.18); color: #7ee787; '
                f'padding: 1px 6px; border-radius: 3px;">+ {safe_content}</div>'
            )
        elif marker == "? ":
            continue
        else:
            html.append(f'<div style="padding: 1px 6px; color: #8b949e;">&nbsp;&nbsp;{safe_content}</div>')

    html.append("</div>")
    return "\n".join(html)


def load_latest_summary_metrics() -> Optional[dict]:
    """Tải số liệu thống kê khoa học mới nhất từ thư mục artifacts/results."""
    results_dir = PROJECT_ROOT / "artifacts" / "results"
    if not results_dir.is_dir():
        return None

    # Tìm file JSON tổng hợp mới nhất
    json_files = sorted(results_dir.glob("metrics_summary_*.json"), key=os.path.getmtime, reverse=True)
    if not json_files:
        return None

    try:
        with open(json_files[0], "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_last_single_run(
    task_name: str,
    task_label: str,
    spec_content: str,
    model_name: str,
    max_k: int,
    timeout_sec: int,
    result_obj: Any,
    elapsed: float,
) -> None:
    """Lưu trữ kiên cố kết quả kiểm định lượt đơn lẻ gần nhất vào artifacts/results/last_single_run.json."""
    results_dir = PROJECT_ROOT / "artifacts" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    target_file = results_dir / "last_single_run.json"

    # Trích xuất lịch sử các lượt chạy từ đối tượng PipelineResult
    history_data = []
    if hasattr(result_obj, "history"):
        for item in result_obj.history:
            history_data.append({
                "iteration": item.iteration,
                "code": item.code,
                "is_verified": item.is_verified,
                "error_taxonomy": item.error_taxonomy,
                "error_message": item.error_message,
                "cot_trace": getattr(item, "cot_trace", ""),
                "cot_tokens": getattr(item, "cot_tokens", 0),
                "counterexample_desc": getattr(item, "counterexample_desc", ""),
                "has_cegar": getattr(item, "has_cegar", False),
            })

    data = {
        "timestamp": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "task_name": task_name,
        "task_label": task_label,
        "spec_content": spec_content,
        "model_name": model_name,
        "max_k": max_k,
        "timeout_sec": timeout_sec,
        "elapsed": round(elapsed, 2),
        "is_success": getattr(result_obj, "is_success", False),
        "total_iterations": getattr(result_obj, "total_iterations", 0),
        "final_code": getattr(result_obj, "final_code", ""),
        "failure_reason": getattr(result_obj, "failure_reason", ""),
        "history": history_data,
    }

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi khi lưu last_single_run.json: {e}")


def load_last_single_run() -> Optional[dict]:
    """Tải kết quả kiểm định đơn lẻ gần nhất từ artifacts/results/last_single_run.json."""
    target_file = PROJECT_ROOT / "artifacts" / "results" / "last_single_run.json"
    if not target_file.is_file():
        return None
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_last_single_run() -> bool:
    """Xóa bỏ file lưu trữ lịch sử lượt chạy đơn lẻ gần nhất."""
    target_file = PROJECT_ROOT / "artifacts" / "results" / "last_single_run.json"
    if target_file.is_file():
        try:
            target_file.unlink()
            return True
        except Exception:
            return False
    return False


def dict_to_pipeline_result(data: dict) -> Tuple[Any, dict]:
    """Chuyển đổi dữ liệu dict từ last_single_run.json thành đối tượng PipelineResult để hiển thị."""
    from core.pipeline_controller import IterationLog, PipelineResult

    history_logs = []
    for h in data.get("history", []):
        history_logs.append(
            IterationLog(
                iteration=h.get("iteration", 1),
                code=h.get("code", ""),
                is_spec_valid=h.get("is_spec_valid", True),
                is_verified=h.get("is_verified", False),
                error_message=h.get("error_message", ""),
                error_taxonomy=h.get("error_taxonomy", ""),
                cot_trace=h.get("cot_trace", ""),
                cot_tokens=h.get("cot_tokens", 0),
                counterexample_desc=h.get("counterexample_desc", ""),
                has_cegar=h.get("has_cegar", False),
            )
        )

    res = PipelineResult(
        task_name=data.get("task_name", ""),
        is_success=data.get("is_success", False),
        total_iterations=data.get("total_iterations", 0),
        final_code=data.get("final_code", ""),
        history=history_logs,
        failure_reason=data.get("failure_reason", ""),
    )
    return res, data



def save_last_batch_run(
    results_list: List[dict],
    total_batch_time: float,
    model_name: str,
    max_k: int,
    timeout_sec: int,
) -> None:
    """Lưu trữ kiên cố kết quả đợt chạy hàng loạt gần nhất vào artifacts/results/last_batch_run.json."""
    results_dir = PROJECT_ROOT / "artifacts" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    target_file = results_dir / "last_batch_run.json"

    data = {
        "timestamp": datetime.now().strftime("%H:%M:%S %d/%m/%Y"),
        "model_name": model_name,
        "max_k": max_k,
        "timeout_sec": timeout_sec,
        "total_batch_time": round(total_batch_time, 2),
        "results_list": results_list,
    }

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi khi lưu last_batch_run.json: {e}")


def load_last_batch_run() -> Optional[dict]:
    """Tải kết quả đợt chạy hàng loạt gần nhất từ artifacts/results/last_batch_run.json."""
    target_file = PROJECT_ROOT / "artifacts" / "results" / "last_batch_run.json"
    if not target_file.is_file():
        return None
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def clear_last_batch_run() -> bool:
    """Xóa bỏ file lưu trữ lịch sử đợt chạy hàng loạt gần nhất."""
    target_file = PROJECT_ROOT / "artifacts" / "results" / "last_batch_run.json"
    if target_file.is_file():
        try:
            target_file.unlink()
            return True
        except Exception:
            return False
    return False

