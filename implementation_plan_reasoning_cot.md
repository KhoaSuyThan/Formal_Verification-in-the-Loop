# KẾ HOẠCH TRIỂN KHAI TRỤC 2: PHÂN TÍCH HIỆN TƯỢNG "OVERTHINKING & REASONING COT"

**Căn cứ khoa học**: 
1. *arXiv:2505.12886* (2025): *Detection and Mitigation of Hallucination in Large Reasoning Models: A Mechanistic Perspective*.
2. *arXiv:2505.23646* (2025): *Are Reasoning Models More Prone to Hallucination?*.
3. Thực nghiệm đối chuẩn mô hình Reasoning (`ollama/deepseek-r1:7b`) so với Non-Reasoning (`qwen2.5-coder:7b`, `llama3.1:8b`) và Cloud Frontier (`gemini-2.5/3.5-flash`).

---

## 1. MỤC TIÊU KHOA HỌC & ĐÓNG GÓP CHO BÀI BÁO (RESEARCH QUESTIONS)

* **RQ1 (Correlation)**: *Độ dài chuỗi suy luận $L_{CoT}$ (số lượng token bên trong thẻ `<think>`) có tương quan thuận với tỷ lệ chứng minh đúng đắn $H_0$ của Z3 SMT Solver không?*
* **RQ2 (Overthinking Threshold)**: *Có tồn tại một "ngưỡng suy nghĩ quá độ" (Overthinking Threshold) mà vượt qua đó, mô hình sinh ra các bất biến vòng lặp dư thừa/sai lệch (`spurious invariants`), dẫn tới ảo giác ngụy biện quy nạp $H_2$ hoặc làm Z3 Solver bị timeout?*
* **RQ3 (Mechanistic Contrast)**: *Mô hình Reasoning (DeepSeek-R1) thất bại ở tầng ảo giác nào nhiều nhất so với mô hình Non-Reasoning?*

---

## 2. THIẾT KẾ CÁC THÀNH PHẦN KỸ THUẬT (SYSTEM ARCHITECTURE)

```
[Phản hồi từ LLM]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│  core/cot_extractor.py (Bóc Tách & Phân Tích CoT)      │
│  - extract_cot_trace(raw_text) -> (clean_code, cot)   │
│  - calculate_cot_metrics(cot_text) -> {tokens, depth} │
└──────────────────────────┬─────────────────────────────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
 [Mã Dafny Sạch]                     [Chỉ Số Suy Luận CoT]
       │                                       │
       ▼                                       ▼
 [Z3 SMT Solver]                     [Lưu Trữ Chi Tiết]
 - Chứng minh VCs                    - cot_tokens ($L_{CoT}$)
 - Phân loại H0 - H4                 - thought_trace (nội dung)
       │                                       │
       └───────────────────┬───────────────────┘
                           │
                           ▼
 ┌───────────────────────────────────────────────────────┐
 │ Giao Diện Tab 4: Overthinking & CoT Analysis Hub      │
 │ - Xem trực tiếp quá trình "suy nghĩ" của DeepSeek-R1 │
 │ - Biểu đồ Overthinking vs Pass Rate                   │
 └───────────────────────────────────────────────────────┘
```

---

## 3. KẾ HOẠCH TRIỂN KHAI THEO TỪNG BƯỚC

### Bước 1: Xây dựng Module Bóc Tách CoT (`core/cot_extractor.py`)
- Định nghĩa hàm chuẩn hóa:
  ```python
  def extract_cot_trace(raw_text: str) -> Tuple[str, str, int]:
      """Bóc tách phản hồi thành (clean_code, thought_trace, token_count)."""
  ```
- Xử lý các tình huống biên:
  - Thẻ `<think>...</think>` đầy đủ.
  - Thẻ `<think>` bị cắt cụt do chạm trần token (`maxOutputTokens`).
  - Mô hình không dùng thẻ suy nghĩ (Non-reasoning models): Trả về `thought_trace = ""`, `token_count = 0`.
- Phân tích mật độ thuật ngữ toán học trong CoT (đếm số lần mô hình nhắc tới `invariant`, `ensures`, `boundary`, `inductive`).

### Bước 2: Tích hợp vào `agents/llm_agent.py` & `core/pipeline_controller.py`
- Cập nhật `agents/llm_agent.py`:
  - Lưu giữ thuộc tính `last_cot_trace: str` và `last_cot_tokens: int` sau mỗi lần gọi mô hình.
- Cập nhật `core/pipeline_controller.py`:
  - Bổ sung trường `cot_trace: str = ""` và `cot_tokens: int = 0` vào `IterationLog`.
  - Bổ sung `cot_tokens: int = 0` và `cot_trace: str = ""` vào `PipelineResult`.
  - Giữ nguyên vẹn tương thích ngược 100% với các mã kiểm định cũ.

### Bước 3: Lưu trữ Chỉ Số CoT trong Benchmark (`core/cross_model_evaluator.py`)
- Khi ghi nhận kết quả từng bài của từng mô hình vào `task_records`:
  - Lưu:
    - `"has_cot"`: `bool` (True nếu có suy luận CoT)
    - `"cot_tokens"`: `int` (Số token suy luận)
    - `"cot_preview"`: Chuỗi tóm tắt 150 ký tự đầu của suy nghĩ.
    - `"cot_trace"`: Toàn văn chuỗi suy luận.
  - Cập nhật bảng tổng kết `ModelBenchmarkSummary` thêm chỉ số:
    - `avg_cot_tokens`: Số token suy luận trung bình mỗi bài của mô hình.

### Bước 4: Viết Bộ Kiểm Thử Tự Động (`tests/test_cot_extractor.py`)
- Kiểm thử các trường hợp:
  1. DeepSeek-R1 có thẻ `<think>` chuẩn kèm code Dafny.
  2. DeepSeek-R1 bị timeout hoặc dở dang giữa thẻ `<think>`.
  3. Mô hình Non-reasoning (Qwen, LLaMA) sinh code trực tiếp không có `<think>`.
  4. Chuỗi suy luận có chứa code giả định bên trong (không bị parse nhầm thành mã nguồn chính).

### Bước 5: Nâng Cấp Giao Diện Trực Quan (Tab 4 — `app.py`)
1. **Xem Quá Trình Suy Luận (CoT Inspector)**:
   - Trong bảng chi tiết, nếu bài nào có chuỗi suy luận (như DeepSeek-R1), người dùng có thể mở expander xem toàn văn đoạn suy nghĩ toán học của mô hình trước khi viết mã.
2. **Biểu Đồ Phân Tích Hiện Tượng Overthinking**:
   - Thêm biểu đồ so sánh: **Số lượng Token Suy Luận Trung Bình giữa Nhóm Thành Công ($H_0$) vs Nhóm Thất Bại ($H_1 \to H_4$)**.
   - Chứng minh trực quan hiện tượng Overthinking: Các bài thất bại thường có lượng token suy luận cao hơn đáng kể so với các bài giải trúng ngay từ đầu.

---

## 4. TIÊU CHÍ HOÀN THÀNH & KIỂM ĐỊNH (DEFINITION OF DONE)
1. `pytest tests/test_cot_extractor.py` đạt **100% passed**.
2. Toàn bộ 53 tests cũ vẫn duy trì **100% passed**.
3. Cú pháp `app.py` biên dịch sạch lỗi (`python -m py_compile app.py`).
4. Giao diện hiển thị trực quan, mượt mà trên Tab 4 và không làm chậm tốc độ của các mô hình Non-reasoning.
5. Cập nhật `CHANGELOG.md` theo quy định.
