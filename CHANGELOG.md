# Nhật Ký Thay Đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi nhận tại đây theo thứ tự thời gian mới nhất ở trên đầu.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/).

---

## [0.7.0] - 2026-09-29: Web Demo Streamlit Tương Tác & Chạy Hàng Loạt
- **Giao Diện Streamlit ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Hỗ trợ chế độ chạy Đơn Lẻ & Hàng Loạt (Batch Mode) với bảng tiến trình thời gian thực.
  - Tối ưu UX Sidebar: Bộ chọn nhanh tự tính số lượng, hộp thoại Modal Dialog (`@st.dialog`) lọc tìm bài theo tên file `.dfy`, khóa nhập phím trên selectbox.
  - Trực quan hóa Actor-Critic Live Studio, khóa đặc tả SHA-256, Code Diff trực quan và Scientific Metrics Dashboard.
- **Tiện Ích Web Demo ([web_demo/helpers.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/helpers.py))**: Quản lý danh mục bài toán phẳng (`get_flat_task_registry()`) và bộ so sánh diff mã nguồn HTML.

## [0.6.0] - 2026-09-28 đến 2026-09-29: Đạt Mốc 12/16 Bài PASS (75.0%)
- **Kết Quả Thực Nghiệm**: Đạt **12/16 bài PASS (75.0%)** trên mô hình `qwen2.5-coder:7b`:
  - Clover Benchmark: **6/6 bài PASS (100.0%)**.
  - HumanEval-Dafny: **6/10 bài PASS (60.0%)** (`002`, `013`, `031`, `035`, `052`, `055`).
  - Tỷ lệ tự sửa thành công (RSR): **100.0%**.
- **Nhận Diện Hình Thái Giải Thuật ([topology_detector.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/topology_detector.py))**: Phân loại 7 hình thái giải thuật, định hướng cấu trúc vòng lặp và bất biến ngay từ Pha 1 sinh mã.
- **Chuẩn Hóa Cú Pháp & Toán Học ([syntax_normalizer.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/syntax_normalizer.py))**: Tích hợp 19 phép biến đổi tự động chuẩn hóa cú pháp Dafny 4.x và biểu thức toán học.
- **Chẩn Đoán Ngữ Nghĩa & Phản Hồi Hình Thức ([diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py))**: Sinh gợi ý bất biến quy nạp song hành (`forall` & `exists`) và cơ chế chống bế tắc lặp mã (Stagnation Breaker).
- **Bộ Kiểm Thử Đơn Vị**: Đạt chuẩn **39/39 unit tests (100% green)**.

     

## [0.4.2] - 2026-09-27
- **Subset Preservation Protocol**: Nâng cấp [core/spec_locker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/spec_locker.py) kiểm tra tính toàn vẹn của tập đặc tả gốc ($S_{orig} \subseteq S_{new}$), hỗ trợ chứng minh theo mô-đun (Helper Lemmas) mà vẫn ngăn chặn 100% việc sửa/xóa đặc tả.
- **Chuẩn hóa Ngữ nghĩa Out-Parameters**: Cập nhật [agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py) loại bỏ triệt để lỗi xung đột ngữ nghĩa `Duplicate local-variable name` trên biến trả về (`returns`), đồng thời nâng timeout an toàn lên 240s cho mô hình cục bộ.
- **Unit Testing**: Bổ sung bộ test tự động [tests/test_spec_locker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_spec_locker.py) xác thực cơ chế bảo tồn tập con.

## [0.4.1] - 2026-09-27
- **Template Preserver**: Hiện thực [core/template_preserver.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/template_preserver.py) tự động nhận diện và bảo toàn 100% các hàm tiên đề (`pure functions`, `predicates`, `lemmas`) trong đề bài chuẩn benchmark.
- **Tối ưu hóa LLMAgent Prompt**: Bổ sung quy tắc ép kiểu số thực (`x.Floor as real`), bất biến tồn tại (`invariant exists`) và chỉ dẫn sửa lỗi trong [agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py).
- **Khắc phục lỗi hệ thống**: Bài `002-truncate` đạt Pass@1 ngay lượt đầu; các bài `000`, `077` loại bỏ triệt để lỗi biên dịch `unresolved identifier` và `SpecTamperingViolation`.

## [0.4.0] - 2026-09-27
- **Metrics Evaluation Engine**: Hiện thực [experiments/evaluate_metrics.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/evaluate_metrics.py) tự động tính toán các chỉ số NCKH (Pass@1, Pass@K, RSR, Error Taxonomy Matrix) và xuất báo cáo Markdown / JSON.
- **HumanEval-Dafny Suite**: Nạp và chuẩn hóa 10 bài toán chuẩn đầu tiên từ JetBrains Research vào [data/benchmarks/humaneval_dafny/](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/humaneval_dafny/).
- **Kiểm thử thực nghiệm**: Kết xuất báo cáo đánh giá khoa học mẫu thành công tại `artifacts/results/metrics_summary_*.md`.

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
