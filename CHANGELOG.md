# Nhật Ký Thay Đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi nhận tại đây theo thứ tự thời gian mới nhất ở trên đầu.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/).

---

## [0.3.0] - 2026-09-27
- **Benchmark Suite**: Thêm 5 bài toán mới vào [data/benchmarks/clover/](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/clover/) (`abs_val`, `find_min`, `sum_to_n`, `linear_search`, `sign_function`).
- **Batch Runner**: Hiện thực [experiments/run_benchmark.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/run_benchmark.py) tự động chạy hàng loạt bài toán, giao diện Rich và xuất kết quả CSV/logs.
- **Thực nghiệm**: Hoàn thành chạy kiểm định 6 bài toán mẫu với mô hình `qwen2.5-coder:7b` (Pass@1 đạt 66.67%).
- **Prompt Agent**: Tinh chỉnh [agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py) chuẩn hóa cú pháp vòng lặp `while` và bất biến `invariant` cho Dafny 4.x.

## [0.2.0] - 2026-09-27
- **Verification Engine**: Tích hợp Dafny 4.11 + Z3 Solver vào `tools/dafny/`, tự động cấu hình qua [core/dafny_engine.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/dafny_engine.py).
- **LLM Agent**: Tích hợp LiteLLM kết nối Ollama local (`qwen2.5-coder:7b`), bổ sung cơ chế chống timeout và bóc tách thẻ `<think>`.
- **Pipeline Controller**: Xây dựng [core/pipeline_controller.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py) điều phối vòng lặp khép kín Pass@K.
- **Single Runner**: Tạo script [run_single.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/run_single.py) chạy kiểm thử đơn lẻ bài toán mẫu.

## [0.1.0] - 2026-09-27
- **Khởi tạo dự án**: Thiết lập cấu trúc thư mục chuẩn NCKH, [requirements.txt](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/requirements.txt) và [.gitignore](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.gitignore).
- **Core Modules**: Xây dựng [spec_locker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/spec_locker.py) (khóa đặc tả SHA-256) và [diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py) (phân loại lỗi Z3).
- **Tài liệu**: Chuẩn hóa toàn diện [README.md](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/README.md) với sơ đồ Mermaid và cấu trúc thư mục.
