# Nhật Ký Thay Đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi nhận tại đây theo thứ tự thời gian mới nhất ở trên đầu.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/).

---

## [1.6.1-groq-tracker] - 2026-10-09: Bộ Theo Dõi & Thống Kê Token Groq Cloud API (LPU Inference)
- **Cốt lõi Token Tracker ([core/token_tracker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/token_tracker.py))**: Bổ sung các hàm `get_groq_token_usage()`, `record_groq_tokens()` và `reset_groq_tokens()`; lưu trữ kiên cố số liệu Token Input/Output và số lượt gọi vào `artifacts/results/groq_token_usage.json`.
- **Tự động trích xuất Token ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py))**: Tự động đọc `response.usage` từ phản hồi của LiteLLM khi gọi các mô hình Groq Cloud để cộng dồn chính xác lượng token tiêu thụ.
- **Trực quan hóa Header Web UI ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**: Bổ sung thẻ thống kê **⚡ Groq Token** màu cam Neon đặc trưng của Groq đặt song song cạnh thẻ **💎 Gemini Token** trên thanh tiêu đề Hero; hiển thị chi tiết tổng token, In, Out và tổng calls.
- **Kiểm thử tự động ([tests/test_token_tracker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_token_tracker.py))**: Mở rộng unit test cho bộ đếm token Groq; toàn bộ test suite đạt **113/113 tests PASSED 100%**.

## [1.6.0-groq] - 2026-10-09: Tích Hợp Hạ Tầng Suy Luận Siêu Tốc Groq Cloud (LPU Inference)
- **Cấu hình API ([.env](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.env), [.env.example](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.env.example))**: Bổ sung `GROQ_API_KEY` kết nối cụm máy chủ chip LPU.
- **Phòng vệ Rate Limit 429 ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py))**: Tự động bắt lỗi 429/TPM, ngủ giãn cách và retry tối đa 3 lần; tối ưu `max_tokens` (8192 cho CoT, 2048 cho mã trực tiếp).
- **Mở rộng mô hình khả dụng ([core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py))**: Đăng ký `groq/qwen/qwen3.8-27b` (Qwen 3.8 27B), `groq/openai/gpt-oss-120b` (GPT-OSS 120B) và `groq/openai/gpt-oss-20b` (phân loại `Cloud (Groq LPU)`).
- **Đồng bộ Web UI ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py), [web_demo/tabs/](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/))**: Hỗ trợ chọn mô hình Groq trên Sidebar, Tab 3 (Đối chuẩn Clover) và Tab 4 (So tài đa mô hình kèm khuyến nghị 1–2 Workers).
- **Kiểm thử ([tests/test_groq_integration.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_groq_integration.py))**: 6 bài test xác thực kết nối thực tế; toàn bộ test suite đạt **112/112 tests PASSED 100%**.

## [1.5.0-step5] - 2026-10-06: Mở Rộng Cấu Trúc Dữ Liệu Quy Nạp (Cây Nhị Phân & Danh Sách Liên Kết - Bước 5)
- **Tập Benchmark Quy Nạp Mới ([data/benchmarks/advanced_inductive/](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/advanced_inductive/))**: Xây dựng 5 bài toán chuẩn hóa cú pháp Dafny 4.x và Z3 SMT Solver:
  - `tree_size_height.dfy`: Kích thước & chiều cao cây nhị phân, chứng minh bất biến $size \ge height$ qua đệ quy cấu trúc.
  - `bst_search.dfy`: Cây nhị phân tìm kiếm BST, kiểm chứng bảo toàn vị từ `is_bst` và `tree_contains`.
  - `bst_insert.dfy`: Chèn phần tử vào cây BST, chứng minh bảo toàn cấu trúc và thứ tự toán học.
  - `linked_list_reverse.dfy`: Đảo ngược danh sách liên kết đại số quy nạp `datatype List = Nil | Cons(...)`.
  - `linked_list_stats.dfy`: Thống kê độ dài và tổng giá trị danh sách liên kết quy nạp.
- **Nâng Cấp Nhận Diện Hình Thái Toán Học ([core/topology_detector.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/topology_detector.py))**:
  - Bổ sung 2 hình thái giải thuật mới: `AlgorithmTopology.RECURSIVE_TREE` và `AlgorithmTopology.LINKED_LIST`.
  - Tự động phát hiện cấu trúc `datatype Tree` và `datatype List` với mức độ ưu tiên cao.
  - Cung cấp khung chỉ dẫn cấu trúc (*Inductive Directive Skeleton*) hướng dẫn LLM sinh mẫu khớp mẫu đại số `match-case`, đồng thời khẳng định bảo chứng dừng tự động (*Termination Guaranteed*) của đệ quy cấu trúc trong Dafny.
- **Mở Rộng Danh Mục Bài Toán & Giao Diện Web ([web_demo/helpers.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/helpers.py), [app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Tích hợp nhóm thứ 4 `"Advanced Inductive Structures (Cây & Danh Sách)"` vào registry, mở rộng tổng quy mô từ **30 lên 35 bài toán**.
  - Bổ sung preset `"inductive"` trong helper và cập nhật hộp thoại Modal chọn bài sang bố cục 4 cột cân đối kèm dropdown preset *"🌳 Bộ Quy Nạp Inductive (5 bài)"*.
- **Kiểm Thử Đơn Vị Toàn Diện ([tests/test_inductive_structures.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_inductive_structures.py))**:
  - Bổ sung 8 bài test mới kiểm tra tính toàn vẹn tệp đặc tả, nhận diện Topology, chỉ dẫn quy nạp, mở rộng registry 35 bài.
  - Toàn bộ test suite đạt **106/106 tests PASSED 100%** trong 10.81s.

## [1.5.0-step4-perf] - 2026-10-06: Tối Ưu Hóa Timeout LLM & Kiểm Soát Token Tránh Nghẽn VRAM
- **Nâng ngưỡng Timeout an toàn ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py), [core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py))**: Tăng `timeout_sec` từ 90s lên 180s (3 phút) giúp các mô hình Local AI (Qwen 7B, LLaMA 8B) đủ thời gian giải quyết các bài toán HumanEval nặng (`fib`, `is-prime`, `sort_array`), triệt tiêu hoàn toàn lỗi `Connection timed out after 90.0 seconds`.
- **Kiểm soát Token theo kiến trúc mô hình ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py))**: Giới hạn `max_tokens = 1024` cho các mô hình sinh mã trực tiếp (Qwen, LLaMA) giúp rút ngắn thời gian sinh từ 40s xuống 15–20s; giữ nguyên 8192 tokens cho DeepSeek-R1 để phục vụ suy luận dài Chain-of-Thought (CoT).
- **Khuyến nghị tài nguyên luồng ([web_demo/tabs/tab_cross_model_view.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/tab_cross_model_view.py))**: Bổ sung chỉ dẫn trực quan khuyến nghị số luồng `Workers`: Local AI (1–2 Workers để dồn VRAM/GPU, tránh hiện tượng Swap mô hình); Cloud AI (4–8 Workers để tăng tốc tối đa qua API Google).
- **Mặc định mô hình Tab 4 ([web_demo/tabs/tab_cross_model_view.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/tab_cross_model_view.py))**: Đổi mặc định danh sách so tài sang chỉ 2 mô hình Local (`Qwen 7B`, `LLaMA 8B`), tránh tự động gọi Cloud Gemini ngoài ý muốn.
- **Hỗ trợ CLI Benchmark đa luồng ([experiments/run_cross_model_benchmark.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/run_cross_model_benchmark.py))**: Thêm cờ `--workers` và `--no-cache` cho script chạy dòng lệnh.
- **Kiểm thử tự động ([tests/](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/))**: Toàn bộ 98/98 unit tests đạt kết quả PASSED 100% trong 11.42s.

## [1.5.0-step4] - 2026-10-06: Song Song Hóa Benchmark & Bộ Nhớ Đệm SMT Verification Cache (Bước 4)
- **Bộ nhớ đệm SMT Verification Cache ([core/verification_cache.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/verification_cache.py))**: Băm SHA-256 mã nguồn và cờ kiểm định, lưu đệm kết quả Z3 an toàn đa luồng (`threading.Lock`), giúp tái sử dụng kiểm định tức thì (<0.001s).
- **Tích hợp SMT Cache vào Engine ([core/dafny_engine.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/dafny_engine.py))**: Tự động kiểm tra và cập nhật cache trước khi gọi subprocess Z3 CLI.
- **Thực thi đa luồng song song ([core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py))**: Hỗ trợ tham số `workers` (1-8 luồng) với `ThreadPoolExecutor`, bảo đảm Thread-safe khi cập nhật checkpoint và tiến trình.
- **Giao diện Web Tab 4 ([web_demo/tabs/tab_cross_model_view.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/tab_cross_model_view.py))**: Bổ sung thanh trượt số luồng `Workers (1-8)` và checkbox bật/tắt `SMT Verification Cache`.
- **Kiểm thử tự động ([tests/test_parallel_benchmark.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_parallel_benchmark.py))**: Thêm 6 bài test mới, nâng tổng số test lên 98 bài, toàn bộ 98/98 tests PASSED 100%.

## [1.5.0-step3] - 2026-10-05: Đối Chuẩn Ablation Study với Stanford Clover & Xuất LaTeX (Bước 3)
- **Cờ bóc tách Pipeline ([core/pipeline_controller.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py))**: Bổ sung 5 cờ cấu hình (`enable_topology`, `enable_normalizer`, `enable_spec_locker`, `enable_semantic_hints`, `enable_cegar`) cho phép đối chuẩn bóc tách giữa Stanford Clover Baseline và Hệ Thống Đề Xuất.
- **Xuất bảng LaTeX ([core/latex_exporter.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/latex_exporter.py))**: Sinh mã bảng `booktabs` chuẩn bài báo khoa học, tự động làm nổi bật chỉ số tối ưu kèm tính năng tải tệp `.tex`.
- **Thực nghiệm & Web UI ([experiments/run_clover_baseline_comparison.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/run_clover_baseline_comparison.py), [web_demo/tabs/tab_metrics_view.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/tab_metrics_view.py))**: Bộ runner đối chuẩn lưu kết quả kiên cố; giao diện Tab 3 tích hợp nút chạy trực tiếp kèm tiến trình thời gian thực và tùy chọn mô hình linh hoạt.
- **Kiểm thử ([tests/test_clover_ablation.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_clover_ablation.py))**: Thêm 6 test case mới, toàn bộ 92/92 tests PASSED 100%.

## [1.5.0-step2] - 2026-10-05: Bảo Chứng Dừng Decreases & Suy Luận Modifies (Trục 4)
- **Tự động suy luận `decreases` & `modifies` ([core/syntax_normalizer.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/syntax_normalizer.py))**:
  - Triển khai `infer_loop_decreases()` tự động chèn ranking function cho các mẫu hình vòng lặp (tiến, lùi, nhị phân, Euclid mod/trừ, `<=`, hỗ trợ cả ngoặc `{` cùng dòng).
  - Triển khai `infer_array_modifies()` tự động bổ sung `modifies a` cho method thao tác mảng in-place, phân biệt an toàn giữa mảng khả biến `array<T>` và chuỗi bất biến `seq<T>`.
- **Nâng cấp chẩn đoán lỗi dừng & engine ([core/diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py), [core/dafny_engine.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/dafny_engine.py))**:
  - `DiagnosticParser`: Sinh chỉ dẫn ranking function chi tiết cho 3 lỗi `TerminationFailure` (`might not decrease`, `cannot prove termination`, `bounded below`).
  - `DafnyEngine`: Bổ sung cờ `--allow-warnings` tránh đánh trượt bài toán khi chỉ có warning vô hại.
- **Tối ưu Prompt & Kiểm thử ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py), [tests/test_axis4_termination.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_axis4_termination.py))**:
  - Bổ sung quy tắc Total Correctness vào system prompt LLM để tối ưu Pass@1.
  - Tạo 17 bài test mới cho Trục 4; toàn bộ 86/86 bài kiểm thử của hệ thống đạt PASSED 100%.

## [1.5.0-step1] - 2026-10-05: Tái Cấu Trúc Mô-đun Hóa Giao Diện (Bước 1)
- **Mô-đun hóa giao diện ([web_demo/tabs/](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/))**: Tách 4 tab độc lập (`tab_pipeline_view`, `tab_diff_view`, `tab_metrics_view`, `tab_cross_model_view`).
- **Thu gọn tệp điều phối ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**: Giảm ~67% dung lượng (từ 1.995 dòng xuống 660 dòng), tách biệt Bootstrap, Sidebar và logic từng Tab.
- **Kiểm thử giao diện ([tests/test_modular_ui.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_modular_ui.py))**: Thêm 4 bài test bảo đảm tính toàn vẹn export và chữ ký hàm (69/69 tests passed).

## [1.4.0] - 2026-10-03: Tự Sửa Lỗi Hướng Dẫn Bằng Phản Ví Dụ SMT (Neuro-Symbolic CEGAR - Trục 3)
- **Kích hoạt cờ Solver Counterexample ([core/dafny_engine.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/dafny_engine.py))**:
  - Tích hợp cờ `--extract-counterexample` của Dafny/Z3 CLI trong phương thức `verify()`, kích hoạt bộ giải SMT trích xuất mô hình trạng thái dữ liệu cụ thể gây vi phạm kiểm định logic.
- **Bộ Bóc Tách & Cấu Trúc Hóa Phản Ví Dụ ([core/diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py))**:
  - Định nghĩa dataclass `CounterexampleData` quản lý `initial_state`, `failing_state`, `violated_clause` và `description`.
  - Triển khai hàm `extract_counterexample()` tự động bóc tách các biểu thức `assume` từ Z3, chuyển đổi thành ánh xạ giá trị biến trực quan.
  - Nâng cấp `format_diagnostic_feedback()` tự động chèn khối phản hồi CEGAR hướng mục tiêu (`🎯 PHẢN VÍ DỤ CỤ THỂ TỪ Z3 SMT SOLVER`) để hướng dẫn LLM sửa trúng ca biên thay vì suy đoán mù.
- **Tích hợp Vòng Lặp & Benchmark ([core/pipeline_controller.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py), [core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py))**:
  - Bổ sung `counterexample_desc` và `has_cegar` vào `IterationLog` và `PipelineResult`.
  - Bổ sung chỉ số `cegar_repaired_count` vào `ModelBenchmarkSummary` để định lượng số bài được cứu nhờ phản ví dụ.
- **Trực Quan Hóa Giao Diện ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py), [web_demo/helpers.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/helpers.py))**:
  - Tab 1: Hiển thị thẻ cảnh báo màu cam nổi bật `🎯 Phản ví dụ Z3 (CEGAR): [x = ... ➔ y = ...]` ngay tại từng lượt tự sửa lỗi (cả khi chạy trực tiếp lẫn khi nạp lịch sử đã lưu).
- **Kiểm Thử Độc Lập & Thực Nghiệm Z3 ([tests/test_cegar_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_cegar_parser.py))**:
  - 6 ca kiểm thử bao phủ toàn diện: số âm, đa biến, không có phản ví dụ, prompt CEGAR và **bài test live trực tiếp gọi Dafny 4.x/Z3 CLI** (100% passed).

## [1.3.6] - 2026-10-03: Định Lượng Chuỗi Suy Luận CoT & Phân Tích Hiện Tượng Overthinking (Trục 2)
- **Module Bóc Tách & Định Lượng CoT ([core/cot_extractor.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cot_extractor.py))**:
  - Triển khai hàm `extract_cot_trace` bóc tách độc lập giữa chuỗi suy luận bên trong `<think>...</think>` và mã nguồn Dafny sạch để đưa vào Z3 SMT Solver (xử lý an toàn cả trường hợp thẻ suy nghĩ bị cắt cụt do chạm trần token).
  - Thuật toán `analyze_cot_density` phân tích mật độ các từ khóa toán học cốt lõi (`invariant`, `ensures`, `boundary`, `decreases`) và nhận diện ngưỡng suy nghĩ quá độ (*Overthinking Threshold* > 800 tokens theo *arXiv:2505.12886*).
- **Tích hợp sâu vào Agent & Pipeline ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py), [core/pipeline_controller.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py))**:
  - Ghi nhận `last_cot_trace` và `last_cot_tokens` qua từng vòng lặp tự sửa lỗi Pass@K của [PipelineController](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py), lưu kiên cố trong `IterationLog` và `PipelineResult`.
- **Nâng cấp đối chuẩn Benchmark ([core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py))**:
  - Bổ sung trường `avg_cot_tokens` vào `ModelBenchmarkSummary` và chi tiết `cot_tokens`, `has_cot`, `cot_preview`, `cot_trace` trong từng bản ghi bài toán.
- **Nâng cấp giao diện trực quan Tab 4 ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Bổ sung cột *CoT Token TB ($L_{CoT}$)* trong Bảng Ma Trận Đối Đầu khi có mô hình suy luận tham gia.
  - Bổ sung cột *Suy Luận CoT* trong Bảng Nhật Ký Chi Tiết.
  - Thêm khung phân tích: **Phân Tích Hiện Tượng 'Overthinking' & Chuỗi Suy Luận CoT (arXiv:2505.12886)** so sánh số token trung bình giữa nhóm bài Đạt ($H_0$) và Thất Bại ($H_1 \to H_4$), tích hợp **Kính Soi Chuỗi Suy Luận (CoT Inspector)** để xem toàn văn đoạn suy nghĩ của mô hình.
- **Kiểm thử tự động ([tests/test_cot_extractor.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_cot_extractor.py))**:
  - 6 ca kiểm thử bao phủ toàn bộ các tình huống CoT đầy đủ, cắt cụt, mã giả bên trong think, và mô hình non-reasoning (100% test passed).

- **Tái cấu trúc bố cục Dashboard Tab 4 ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Gộp chung 3 biểu đồ (*Tỷ Lệ Đạt*, *Thời Gian TB*, *Phân Bố Ảo Giác*) vào **1 hàng ngang duy nhất** với 3 cột cân xứng (`st.columns([1, 1, 1.15])`), giải quyết triệt để tình trạng biểu đồ cột bị kéo giãn quá rộng.
  - Chuẩn hóa khoảng cách cột (`bargap=0.35` - `0.45`) giúp thanh bar thon gọn, thanh thoát, hiển thị cân đối bất kể so sánh 2 hay nhiều mô hình.
  - Ẩn thanh thang đo màu (colorbar) ở biểu đồ *Thời Gian TB* (`coloraxis_showscale=False`) để giải phóng không gian hiển thị, đồng đều trực quan với 2 biểu đồ còn lại.
  - **Hiển thị đầy đủ 5 tầng bản chất ảo giác ($H_0 \to H_4$)**: Bố trí chú thích (legend) nằm ngay **bên dưới biểu đồ** và **chia đều thành 2 cột** (`entrywidth=0.48`), giúp người dùng quan sát toàn vẹn cả 5 nhóm ảo giác mà không bị tràn khung hay che khuất dữ liệu.


- **Bộ phân loại ảo giác toán học ([core/hallucination_classifier.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/hallucination_classifier.py))**:
  - Ánh xạ trực tiếp từ *Nature (HSSC 2024)* và Z3 SMT Solver thành 5 nhóm: $H_0$ (Zero-Hallucination), $H_1$ (Spec-Tampering), $H_2$ (Inductive Fallacy), $H_3$ (Boundary Overflow), và $H_4$ (Semantic Drift).
  - Tích hợp tự động vào [core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py), gán nhãn ảo giác cho từng bài toán giải thất bại.
- **Nâng cấp giao diện trực quan Tab 4 ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Thêm biểu đồ cột chồng Plotly: **Phân Bố Bản Chất Ảo Giác Đối Đầu** so sánh cơ cấu ảo giác giữa các mô hình.
  - Bổ sung cột **Phân Loại Ảo Giác (Nature 2024)** kèm badge màu sắc trực quan trong Bảng Nhật Ký Chi Tiết.
  - Thêm khung kiến giải học thuật tóm tắt 5 tầng bản chất ảo giác.
  - Đảm bảo tương thích ngược 100% với các file dữ liệu lịch sử trước đây.
- **Kiểm thử tự động ([tests/test_hallucination_classifier.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_hallucination_classifier.py))**:
  - Bổ sung 6 ca kiểm thử bao phủ toàn bộ các nhóm $H_0 \to H_4$ (100% test passed).

## [1.3.3] - 2026-10-03: Cơ Chế Tiếp Tục Chạy Benchmark (Resume) & Tối Ưu Quản Lý Lịch Sử
- **Tài liệu hóa lộ trình nghiên cứu khoa học ([RESEARCH_IMPROVEMENT_PLAN.md](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/RESEARCH_IMPROVEMENT_PLAN.md))**:
  - Xây dựng bản kế hoạch chi tiết gồm 4 trục cải tiến nâng tầm bài báo khoa học dựa trên 7 công trình tham khảo (Nature 2024, Stanford Clover 2024, IEEE/ACM TSE 2026, arXiv 2025-2026).
- **Cơ chế tiếp tục chạy từ checkpoint dở dang ([core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py), [experiments/run_cross_model_benchmark.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/run_cross_model_benchmark.py))**:
  - Thêm `resume_from_checkpoint=True` (CLI `--resume`): tự động nạp `cross_model_benchmark_latest.json`, bỏ qua các bài đã xong và tiếp tục chạy từ bài dở dang mà không mất kết quả cũ.
  - Hỗ trợ mở rộng số lượng bài (vd: từ 10 lên 16/30 bài) hoặc thêm mô hình mới một cách linh hoạt.
- **Tối ưu giao diện Web Benchmark ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Hiển thị nút `▶️ Tiếp Tục Chạy (X bài đã xong)` cạnh `🚀 Chạy Mới Từ Đầu` khi phát hiện lần chạy dở dang.
  - Tự động nạp tức thì khi chọn file lịch sử trong dropdown; khắc phục lỗi kẹt bảng kết quả.
  - Mở trực tiếp bảng **Nhật Ký Chi Tiết Toàn Bộ Lượt Giải** bên dưới biểu đồ để dễ dàng tra cứu từng bài.
- **Kiểm thử tự động ([tests/test_cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_cross_model_evaluator.py))**:
  - Bổ sung `test_run_benchmark_resume` kiểm chứng luồng kế thừa checkpoint (100% test passed).

## [1.3.2] - 2026-10-02: Khắc Phục Lỗi DeepSeek-R1 & Bổ Sung Nút Dừng Chạy Tiến Trình
- **Tối ưu thích ứng mô hình suy luận sâu Chain-of-Thought ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py))**:
  - Khắc phục triệt để lỗi DeepSeek-R1 thất bại 0/10: nâng `max_tokens` từ 2048 lên 8192 và nâng timeout từ 90s lên 240s khi gọi dòng mô hình `deepseek`.
  - Cải tiến bộ bóc tách `_clean_markdown` với cơ chế phòng vệ chống nuốt code khi thẻ `<think>` chưa kịp đóng do chạm trần token.
- **Bổ sung Nút Dừng Chạy an toàn ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py), [core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py))**:
  - **Tab 1 (Kiểm Định Hàng Loạt)**: Bổ sung nút `⏹️ DỪNG TIẾN TRÌNH`, cho phép dừng sau bài hiện tại và hiển thị bảng kết quả những bài đã hoàn thành.
  - **Tab 4 (So Sánh Đối Đầu)**: Bổ sung nút `⏹️ Dừng So Sánh`, hỗ trợ callback `stop_check` ngắt sớm chuỗi benchmark và bảo toàn toàn bộ dữ liệu checkpoint.

## [1.3.1] - 2026-10-02: Làm Rõ & Mở Rộng Hỗ Trợ Mô Hình Gemini Flash Trên Giao Diện Web
- **Làm rõ phân hệ mô hình Flash ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Xác nhận toàn bộ cấu hình Cloud AI sử dụng dòng **Gemini Flash** (`gemini-2.5-flash`, `gemini-3.5-flash`) nhằm tối ưu hạn ngạch Free Tier (15 RPM / 1.500 requests/ngày) và chống nghẽn 429 so với dòng Pro (2 RPM).
  - Cập nhật nhãn hiển thị tại Tab 4 thành rõ ràng `Gemini 2.5 Flash (Cloud - Quota cao 1500 req/ngày)` và `Gemini 3.5 Flash`.
- **Mở rộng Sidebar ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Bổ sung `gemini-2.5-flash` và `gemini-3.5-flash` vào dropdown Mục 3 (Cấu hình mô hình) ở Sidebar bên trái, cho phép chọn trực tiếp khi chạy chế độ Đơn Lẻ hoặc Hàng Loạt.

## [1.3.0] - 2026-10-01: Hệ Thống Đánh Giá Đối Đầu Đa Mô Hình (Cross-Model Evaluation) & Hoàn Thiện Dự Án
- **Tích hợp Cloud AI thế hệ mới (Google Gemini 3.5/2.5 Flash & OpenAI) ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py))**: 
  - Kết nối REST API Google AI Studio trực tiếp; nâng ngưỡng `maxOutputTokens: 8192` loại bỏ dứt điểm hiện tượng suy luận ngầm (Internal Thinking) nuốt token làm cụt code; xử lý thích ứng lỗi HTTP 429 qua trích xuất thời gian chờ động (`retryDelay`).
  - Kiểm chứng thực tế: Gemini 3.5 Flash giải quyết thành công hàng loạt bài toán khó (`002-truncate`, `013-gcd`, `031-is-prime`, `035-max-element`, `055-fib`) đạt 100% Z3 Verified với tốc độ vượt trội (~12s/bài).
- **Module điều phối đối đầu & Token Tracking ([core/cross_model_evaluator.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/cross_model_evaluator.py), [core/token_tracker.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/token_tracker.py))**:
  - Tự động hóa đánh giá đối kháng giữa Local (Qwen 7B, LLaMA 8B) và Cloud (Gemini, GPT); hỗ trợ lưu Checkpoint lũy tiến (Incremental Checkpoint) bảo toàn kết quả khi gián đoạn mạng; bộ đếm Token lưu trữ bền vững vào JSON.
- **Giao diện Web Demo & CLI Runner đa năng ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py), [experiments/run_cross_model_benchmark.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/run_cross_model_benchmark.py))**:
  - Bổ sung Tab 4 "⚔️ So Sánh Chéo" kèm bảng nhật ký từng bài theo thời gian thực (Live Task Stream Log); công cụ CLI linh hoạt với các bộ chọn `--preset` (`sample`, `humaneval`, `all`).
- **Hoàn thiện tài liệu chuẩn NCKH ([README.md](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/README.md), [.env.example](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/.env.example))**:
  - Bổ sung hệ thống huy hiệu trạng thái, bảng chi tiết 30 bài toán benchmark bao phủ 12 hình thái giải thuật, hướng dẫn cài đặt Ollama/Cloud API và ma trận thực nghiệm đối đầu.
- **Chất lượng kiểm thử**: Toàn bộ 46/46 unit tests đạt 100% Green.

## [1.2.0] - 2026-10-01: Chinh Phục Tuyệt Đối 30/30 Bài Benchmark & Sân Chơi Tự Do
- **Mở rộng 12 hình thái ([core/topology_detector.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/topology_detector.py))**: Bổ sung `ORDERED_INSERT`, `SEQ_CONSTRUCTION`, `SEARCH_CONDITION`, hoàn thiện inductive skeletons cho `LINEAR_LOOP` và `NESTED_LOOP`, đưa tỷ lệ đạt Z3 Solver lên mốc tuyệt đối 30/30 bài (100.0%).
- **Chuẩn hóa cú pháp tự động ([core/syntax_normalizer.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/syntax_normalizer.py))**: Bổ sung bộ lọc `fix_negated_comparison`, cơ chế phòng vệ chống `NoneType` và tự động kích hoạt bổ đề đơn điệu.
- **Web Demo & Sân chơi ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**: Tích hợp Sân chơi Tự do (Playground) nạp mẫu nhanh, tối ưu co giãn 3 chế độ (`Đơn`, `Hàng loạt`, `Tự do`) và cấu hình 2 cột song song.
- **Tài liệu hệ thống ([PROJECT_OVERVIEW.md](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/PROJECT_OVERVIEW.md))**: Biên soạn tổng quan toàn diện về kiến trúc Actor-Critic 3 pha, 4 trụ cột kỹ thuật và cam kết liêm chính khoa học.
- **Kiểm thử chất lượng**: Đạt chuẩn 42/42 unit tests tự động (100% pass).

## [1.0.0] - 2026-10-01: Chinh Phục Tuyệt Đối 16/16 Bài Benchmark Gốc (100%)
- **Cột mốc cốt lõi**: Hoàn thành toàn bộ benchmark gồm `088-sort_array`, `010-is_palindrome`, `077-iscube`.
- **Liêm chính khoa học**: 100% bảo toàn mã băm SHA-256 (`SpecLocker`), không sửa đặc tả, không gian lận.


## [0.9.1] - 2026-09-30: Đạt Mốc 14/16 Bài PASS (87.5%) - Số Học Phi Tuyến & Bổ Đề Đơn Điệu (Bài 077)
- **Ràng Buộc Cấu Trúc Số Học Phi Tuyến ([core/topology_detector.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/topology_detector.py))**:
  - Bổ sung chỉ dẫn hình thái `NON_LINEAR` cho các bài toán tìm căn bậc cao và kiểm tra lũy thừa/lập phương.
  - Hướng dẫn cấu trúc vòng lặp tìm căn tăng dần `cube_root` kết hợp với việc tự động gọi bổ đề đơn điệu có sẵn trong file (`lemma cube_of_larger_is_larger()`).
- **Tối Ưu Chẩn Đoán Ngữ Nghĩa ([core/diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py))**:
  - Hỗ trợ phản hồi hướng dẫn gọi bổ đề tiên đề đơn điệu cho các bài toán số học bậc cao khi Z3 báo vi phạm hậu điều kiện.
- **Kết Quả Thực Nghiệm & Mở Rộng Benchmark ([web_demo/helpers.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/helpers.py))**:
  - Bài **`077-iscube`** đạt chứng minh toán học **PASS 100% ngay tại Lượt 1 (Pass@1)** trên mô hình `qwen2.5-coder:7b` với `temperature = 0.0` (thời gian ~40s).
  - Khóa đặc tả SHA-256 bảo toàn 100%, không sửa đặc tả và không hardcode tên bài toán.
  - Nâng tỷ lệ đạt kiểm định của toàn bộ dự án lên **14/16 bài PASS (87.5%)**; nhóm HumanEval-Dafny đạt **8/10 bài PASS (80.0%)**.
  - Toàn bộ **41/41 unit tests** đạt chuẩn xanh (100% green).


## [0.9.0] - 2026-09-30: Đạt Mốc 13/16 Bài PASS (81.25%) - Mẫu Hình Bất Biến 2 Chiều (Bài 000)
- **Nâng Cấp Hình Thái Tìm Kiếm 2 Chiều ([core/topology_detector.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/topology_detector.py))**:
  - Tích hợp mẫu hình bất biến quy nạp 2 chiều phủ định (`NESTED_PAIRWISE_SEARCH`) cho các bài toán kiểm tra sự tồn tại của cặp phần tử ($O(N^2)$ Pairwise Search).
  - Cung cấp khung bất biến quy nạp 2 lớp (`!flag ==> forall a, b...`) cho vòng ngoài và vòng trong, giúp Z3 SMT Solver chứng minh toán học trường hợp `flag == false` hoàn toàn tất định.
- **Tối Ưu Chẩn Đoán Ngữ Nghĩa ([core/diagnostic_parser.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/diagnostic_parser.py))**:
  - Bổ sung hướng dẫn sinh bất biến phủ định 2 chiều cho các bài toán có hậu điều kiện dạng cờ boolean tồn tại (`flag == (exists i, j ...)`).
- **Kết Quả Thực Nghiệm & Mở Rộng Benchmark ([web_demo/helpers.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/helpers.py))**:
  - Bài **`000-has_close_elements`** đạt chứng minh toán học **PASS 100% ngay tại Lượt 1 (Pass@1)** trên mô hình `qwen2.5-coder:7b` (thời gian ~35s).
  - Khóa đặc tả SHA-256 bảo toàn nguyên vẹn 100%, không sửa bất kỳ dòng đặc tả nào và không hardcode tên bài toán.
  - Nâng tỷ lệ đạt kiểm định của toàn bộ dự án lên **13/16 bài PASS (81.25%)**; nhóm HumanEval-Dafny đạt **7/10 bài PASS (70.0%)**.
  - Toàn bộ **41/41 unit tests** đạt chuẩn xanh (100% green).


## [0.8.1] - 2026-09-30: Chuẩn Hóa Nhiệt Độ Tất Định (Temperature = 0.0) & Tùy Biến Sidebar
- **Chuẩn Hóa Nhiệt Độ Tất Định ([agents/llm_agent.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/agents/llm_agent.py))**:
  - Đặt giá trị mặc định `temperature = 0.0` (Greedy Decoding) để loại bỏ tính ngẫu nhiên, đảm bảo 100% tính tái lập kết quả thực nghiệm chuẩn NCKH.
- **Tùy Biến Trực Quan Sidebar ([app.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/app.py))**:
  - Tích hợp thanh trượt `Temperature (0.0 - 0.5)` trong container "Cấu Hình Mô Hình" cho phép tùy biến trực tiếp trên Web Demo Streamlit.
  - Đồng bộ truyền tham số `temperature` vào `LLMAgent` trong cả chế độ Đơn Lẻ và Hàng Loạt.
- **Lưu Trữ Kiên Cố Lịch Sử Kiểm Định ([web_demo/helpers.py](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/helpers.py))**:
  - Bổ sung các hàm lưu và tải kiên cố kết quả đợt chạy đơn lẻ và hàng loạt vào `artifacts/results/last_single_run.json` và `last_batch_run.json`.
  - Bộ kiểm thử `tests/test_persistent_history.py` đạt chuẩn 41/41 unit tests passed (100% green).


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
