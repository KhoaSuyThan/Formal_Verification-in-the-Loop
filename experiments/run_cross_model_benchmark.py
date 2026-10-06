"""Script dòng lệnh (CLI) chạy thực nghiệm so sánh chéo đa mô hình (Cross-Model Evaluation).

Sử dụng:
    python experiments/run_cross_model_benchmark.py --models qwen deepseek gemini --preset sample
    python experiments/run_cross_model_benchmark.py --models qwen gemini --preset core
    python experiments/run_cross_model_benchmark.py --models qwen deepseek gemini --preset all
"""

import os
import sys
import argparse
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Đảm bảo đường dẫn gốc của dự án nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from core.cross_model_evaluator import CrossModelEvaluator
from web_demo.helpers import get_flat_task_registry


MODEL_MAP = {
    "qwen": "ollama/qwen2.5-coder:7b",
    "deepseek": "ollama/deepseek-r1:7b",
    "gemini": "gemini-3.5-flash",
    "gemini-3.5": "gemini-3.5-flash",
    "gemini-2.5": "gemini-2.5-flash",
    "gemini-3.6": "gemini-3.6-flash",
    "llama": "ollama/llama3.1:8b"
}


def parse_args():
    parser = argparse.ArgumentParser(description="Chạy Benchmark Đối Đầu Đa Mô Hình (Cross-Model Evaluation)")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["qwen", "gemini", "llama"],
        help="Danh sách mô hình cần benchmark: qwen, gemini, llama, deepseek"
    )
    parser.add_argument(
        "--preset",
        choices=["sample", "core", "clover", "humaneval", "all"],
        default="sample",
        help="Tập bài toán: sample (5 bài tiêu biểu), core (16 bài mục tiêu), clover (6 bài), humaneval (10 bài), all (30 bài toàn bộ)"
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="Số lần tự sửa tối đa Pass@K (mặc định K=3)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Tiếp tục chạy từ checkpoint dở dang thay vì chạy mới từ đầu"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Số luồng chạy song song (1 = tuần tự, 2-8 = ThreadPoolExecutor đa luồng)"
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Vô hiệu hóa bộ đệm SMT Verification Cache (mặc định luôn bật cache)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    registry = get_flat_task_registry()

    # Ánh xạ tên mô hình
    model_ids = [MODEL_MAP.get(m.lower(), m) for m in args.models]

    # Chọn tập bài toán
    if args.preset == "sample":
        target_keys = [
            k for k in registry.keys()
            if any(name in k for name in ["abs_val", "sample_max", "002-truncate", "013-greatest_common_divisor", "binary_search"])
        ][:5]
    elif args.preset == "clover":
        target_keys = [k for k, v in registry.items() if v["group"] == "Clover"]
    elif args.preset == "humaneval":
        target_keys = [k for k, v in registry.items() if v["group"] == "HumanEval"]
    elif args.preset == "core":
        target_keys = [k for k, v in registry.items() if v["is_target"]]
    else:
        target_keys = list(registry.keys())

    print("=" * 70)
    print("🚀 BẮT ĐẦU CHẠY BENCHMARK ĐỐI ĐẦU ĐA MÔ HÌNH (CROSS-MODEL EVALUATION)")
    print("=" * 70)
    print(f"Mô hình tham gia: {model_ids}")
    print(f"Số bài toán: {len(target_keys)} bài (Chế độ: {args.preset})")
    print(f"Tham số Pass@K: K={args.max_attempts}")
    if args.resume:
        print("📌 Chế độ: TIẾP TỤC CHẠY TỪ CHECKPOINT (Resume from Checkpoint)")
    print("-" * 70)

    dafny_path = os.getenv("DAFNY_PATH")
    evaluator = CrossModelEvaluator(dafny_path=dafny_path)

    def on_progress(model_id, cur_step, total_steps, msg, data=None):
        pct = (cur_step / max(1, total_steps)) * 100.0
        print(f"[{cur_step:2d}/{total_steps:2d}] ({pct:5.1f}%) {msg}")

    results = evaluator.run_benchmark(
        model_ids=model_ids,
        task_keys=target_keys,
        max_attempts=args.max_attempts,
        progress_callback=on_progress,
        resume_from_checkpoint=args.resume,
        workers=args.workers,
        use_cache=not args.no_cache
    )

    print("\n" + "=" * 70)
    print("📊 KẾT QUẢ ĐỐI ĐẦU TỔNG HỢP (BENCHMARK MATRIX)")
    print("=" * 70)
    print(f"{'Mô hình':<22} | {'Loại':<15} | {'Bài':<4} | {'Pass@1':<8} | {'Pass@K':<8} | {'T_avg (s)':<10} | {'Loops'}")
    print("-" * 80)
    for s in results["summaries"]:
        print(
            f"{s['display_name']:<22} | {s['model_type']:<15} | {s['total_tasks']:<4} | "
            f"{s['pass_at_1_rate']:<7.1f}% | {s['pass_at_k_rate']:<7.1f}% | "
            f"{s['avg_duration_sec']:<10.2f} | {s['avg_repair_loops']:.2f}"
        )
    print("-" * 80)

    print("\n📝 MÃ BẢNG LATEX CHO BÀI BÁO KHOA HỌC:")
    print(results.get("latex_table", ""))
    print("\n🎉 Toàn bộ kết quả đã được lưu tại artifacts/results/cross_model_benchmark_latest.json")


if __name__ == "__main__":
    main()
