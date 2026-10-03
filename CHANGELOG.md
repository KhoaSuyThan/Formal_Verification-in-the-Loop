# Nhật Ký Thay Đổi (Changelog)

Tất cả các thay đổi đáng chú ý của dự án sẽ được ghi nhận tại đây theo thứ tự thời gian mới nhất ở trên đầu.

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/vi/1.0.0/).

---

## [1.3.3] - 2026-10-03: Cơ Chế Tiếp Tục Chạy Benchmark (Resume) & Tối Ưu Quản Lý Lịch Sử
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
