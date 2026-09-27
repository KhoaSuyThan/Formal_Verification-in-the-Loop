# Nhật Ký Thay Đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi nhận tại đây theo thứ tự thời gian mới nhất ở trên đầu.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/).

---

## [0.2.0] - 2026-09-27

### Đã thêm (Added)
- Tích hợp thành công bộ kiểm định hình thức [Dafny 4.11](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tools/dafny/Dafny.exe) và bộ giải toán học Z3 SMT Solver vào đường ống Actor-Critic.
- Tự động phát hiện binary Dafny trong thư mục `tools/dafny/` và cấu hình qua file `.env`.
- Cập nhật cờ kiểm định `--verification-time-limit` chuẩn hóa cho Dafny 4.x.
- Module [llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py): Kết nối LiteLLM với mô hình local Ollama `qwen2.5-coder:7b` (và Cloud LLMs), xử lý prompt sinh mã và vá lỗi theo đặc tả hình thức Dafny.
- Nâng cấp [llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py): Bổ sung cơ chế bắt ngoại lệ Timeout (120s), giới hạn max_tokens (1024) và tự động bóc tách thẻ `<think>` cho các mô hình Reasoning (DeepSeek-R1).
- Bổ sung `tools/` vào [.gitignore](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.gitignore) để cách ly binary Dafny.
- Module [pipeline_controller.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py): Điều phối vòng lặp kiểm định khép kín Pass@K kết hợp Agent, SpecLocker, DafnyEngine và DiagnosticParser.
- Cấu hình hệ thống: [experiment_config.yaml](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/configs/experiment_config.yaml) và [.env.example](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.env.example) mặc định kích hoạt Ollama.
- Script thực thi nhanh [run_single.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/run_single.py) tại thư mục gốc, cấu hình UTF-8 cho console Windows.
- Thực nghiệm thành công với mô hình Qwen2.5 trên bài toán [sample_max.dfy](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/clover/sample_max.dfy), Z3 Solver chứng minh tính đúng đắn 100% tại Pass@1 (Zero-Hallucination).

## [0.1.0] - 2026-09-27

### Đã thêm (Added)
- File [.gitignore](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.gitignore): Cấu hình loại trừ bytecode Python, môi trường ảo và các file nhạy cảm.
- Khởi tạo cấu trúc thư mục dự án chuẩn NCKH: `core/`, `agents/`, `configs/`, `experiments/`, `data/benchmarks/clover/`, `data/benchmarks/humaneval_dafny/`, `data/raw/`, `artifacts/logs/`, `artifacts/results/`.
- File [requirements.txt](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/requirements.txt): Cung cấp các thư viện `litellm`, `pydantic`, `pyyaml`, `pandas`, `python-dotenv`, `tqdm`, `rich`.
- Module [spec_locker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/spec_locker.py): Giao thức khóa cứng đặc tả (Spec-Locking Protocol) bằng SHA-256 đối với các mệnh đề `ensures`, hỗ trợ chuẩn hóa comment và dấu chấm phẩy.
- Module [dafny_engine.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/dafny_engine.py): Wrapper gọi Dafny CLI kiểm định tính đúng đắn với Z3 SMT Solver, hỗ trợ timeout và phát hiện trạng thái cài đặt Dafny.
- Module [diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py): Bóc tách tọa độ lỗi và phân loại lỗi theo Error Taxonomy (`PostconditionViolation`, `LoopInvariantViolation`, `PreconditionViolation`, `TerminationFailure`, `OutOfBounds`).
- Dữ liệu kiểm thử mẫu: [sample_max.dfy](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/clover/sample_max.dfy) trong tập benchmark Clover.

### Đã sửa (Changed)
- Chuẩn hóa toàn bộ [README.md](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/README.md): Bọc sơ đồ kiến trúc vào Mermaid chart, bọc cây thư mục vào code block để chống vỡ layout hiển thị trên GitHub; loại bỏ các tag trích dẫn rác `[cite: ...]`.
