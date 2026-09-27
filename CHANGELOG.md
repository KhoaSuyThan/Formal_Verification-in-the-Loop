# Nhật Ký Thay Đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi nhận tại đây theo thứ tự thời gian mới nhất ở trên đầu.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/).

---

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
