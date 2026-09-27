"""Script thực thi kiểm định đơn lẻ một bài toán (Single-task Runner).

Chạy mặc định với mô hình Ollama qwen2.5-coder:7b trên bài toán mẫu sample_max.dfy.
"""

import sys
# Cấu hình UTF-8 cho console Windows để hiển thị tiếng Việt và biểu tượng
sys.stdout.reconfigure(encoding='utf-8')

import argparse
from pathlib import Path

from core.dafny_engine import DafnyEngine
from core.spec_locker import SpecLocker
from core.diagnostic_parser import DiagnosticParser
from agents.llm_agent import LLMAgent
from core.pipeline_controller import PipelineController


def parse_args():
    """Bóc tách tham số dòng lệnh."""
    parser = argparse.ArgumentParser(description="Chạy kiểm định hình thức cho một bài toán Dafny.")
    parser.add_argument(
        "--task",
        type=str,
        default="data/benchmarks/clover/sample_max.dfy",
        help="Đường dẫn đến file bài toán Dafny (.dfy)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="ollama/qwen2.5-coder:7b",
        help="Tên mô hình LLM (mặc định: ollama/qwen2.5-coder:7b)"
    )
    parser.add_argument(
        "--max_k",
        type=int,
        default=3,
        help="Số lượt lặp tự sửa lỗi tối đa (mặc định: 3)"
    )
    return parser.parse_args()


def main():
    """Hàm điều khiển chính."""
    args = parse_args()
    task_file = Path(args.task)

    if not task_file.exists():
        print(f"[LỖI] Không tìm thấy file đề bài: {task_file}")
        return

    print("=" * 60)
    print("  KHUNG SINH MÃ VÀ TỰ SỬA LỖI KHÉP KÍN (FORMAL VERIFICATION)")
    print("=" * 60)
    print(f"Bài toán kiểm thử: {task_file.name}")
    print(f"Mô hình LLM:      {args.model}")
    print(f"Giới hạn Pass@K:  K = {args.max_k}")
    print("-" * 60)

    raw_spec = task_file.read_text(encoding="utf-8")
    original_hash = SpecLocker.get_hash(raw_spec)
    print(f"Mã băm đặc tả gốc (SHA-256): {original_hash[:16]}...")

    # Khởi tạo các thành phần
    engine = DafnyEngine(timeout_sec=15)
    agent = LLMAgent(model_name=args.model)

    # Kiểm tra sự sẵn sàng của Dafny CLI
    if not engine.is_available():
        print("\n[CẢNH BÁO MÔI TRƯỜNG] Dafny CLI chưa được cài đặt hoặc chưa thêm vào PATH!")
        print("-> Đang kích hoạt chế độ Kiểm tra LLM sinh mã & Spec-Locking Guard...")
        
        prompt = f"Hãy hoàn thiện phương thức Dafny sau để vượt qua kiểm định hình thức:\n\n{raw_spec}"
        generated_code = agent.generate_code(prompt)
        print("\n--- [MÃ NGUỒN QWEN2.5 SINH RA] ---")
        print(generated_code)
        print("-" * 35)

        is_valid_spec = SpecLocker.is_valid(original_hash, generated_code)
        if is_valid_spec:
            print("🛡️ [Spec-Locking]: HỢP LỆ! Mã nguồn bảo toàn 100% điều kiện ensures gốc.")
        else:
            print("❌ [Spec-Locking]: CẢNH BÁO! LLM đã tự ý sửa đổi điều kiện ensures.")

        print("\n💡 Gợi ý: Hãy cài đặt Dafny 4.x và thêm vào PATH để kích hoạt Z3 tự động chứng minh 100%.")
        return

    # Nếu Dafny đã sẵn sàng -> Kích hoạt Pipeline khép kín đầy đủ
    controller = PipelineController(agent=agent, engine=engine, max_k=args.max_k)
    print("\n[BẮT ĐẦU] Khởi động vòng lặp kiểm định hình thức...")
    result = controller.run_task(raw_spec=raw_spec, task_name=task_file.stem)

    print("\n" + "=" * 60)
    if result.is_success:
        print(f"🏆 THÀNH CÔNG! Đã chứng minh tính đúng đắn 100% tại lượt {result.total_iterations} (Zero-Hallucination).")
        print("\n--- Mã nguồn hoàn chỉnh đã được kiểm định ---")
        print(result.final_code)
    else:
        print(f"⚠️ THẤT BẠI: {result.failure_reason}")
        print(f"Tổng số lượt thử: {result.total_iterations}")
    print("=" * 60)


if __name__ == "__main__":
    main()
