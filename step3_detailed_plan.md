# KẾ HOẠCH CHI TIẾT BƯỚC 3: ĐỐI CHUẨN ABLATION STUDY VỚI STANFORD CLOVER (2024)
**Dự án**: Formal Verification-in-the-Loop  
**Phiên bản mục tiêu**: v1.5.0-step3  
**Thời gian lập**: 05/10/2026

---

## 🎯 1. MỤC TIÊU TỔNG QUAN

Chứng minh bằng số liệu thực nghiệm khoa học có thể kiểm chứng (Reproducible Empirical Evidence) rằng: Khung phương pháp đề xuất của đề tài (kết hợp Neuro-Symbolic 4 Trục: Topology Directive + Syntax Normalizer + Spec-Locker + CEGAR Counterexample) vượt trội rõ rệt so với phương pháp gốc của **Stanford Clover (2024)** (chỉ dựa vào prompting tuần tự thuần túy).

### Câu hỏi nghiên cứu (Research Questions - RQs):
- **RQ1 (Tỷ lệ chứng minh thành công)**: Việc tích hợp các chứng chỉ hình thức (Proof Annotations) và sửa cú pháp tự động có nâng cao tỷ lệ Pass@1 và Pass@3 so với Clover Baseline hay không?
- **RQ2 (Ngăn ngừa suy thoái đặc tả)**: Cơ chế Spec-Locker SHA-256 ngăn chặn được bao nhiêu % trường hợp LLM tự ý gian lận/sửa đổi đề bài (Spec-Tampering $H_1$) so với Clover?
- **RQ3 (Tốc độ hội tụ và phản ví dụ)**: Phản ví dụ CEGAR cụ thể từ Z3 SMT Solver giúp rút ngắn bao nhiêu vòng lặp tự sửa lỗi trung bình?

---

## 📋 2. PHÂN TÍCH THÀNH PHẦN KỸ THUẬT

### 2.1. Cấu hình so sánh 2 phương pháp (Ablation Configuration):

| Tiêu chí kỹ thuật | Stanford Clover Baseline (2024) | Hệ Thống Đề Xuất (Our Neuro-Symbolic System) |
|:---|:---|:---|
| **Mồi gợi hình thái (Topology)** | ❌ Tắt (`enable_topology=False`) | ✅ Kích hoạt 12 hình thái thuật toán |
| **Bảo toàn & Chuẩn hóa cú pháp** | ❌ Tắt (`enable_normalizer=False`) | ✅ Kích hoạt 23 phép biến đổi (bao gồm Trục 4 `decreases` & `modifies`) |
| **Khóa toàn vẹn đặc tả** | ❌ Tắt (`enable_spec_locker=False`) — chỉ ghi nhận vi phạm | ✅ Kích hoạt Spec-Locker SHA-256 chống gian lận |
| **Phản hồi lỗi sửa mã** | Thô (Raw Dafny error message) | ✅ Chẩn đoán ngữ nghĩa chuyên sâu + CEGAR Counterexample |

---

## 🔧 3. THỨ TỰ TRIỂN KHAI CHI TIẾT (6 BƯỚC CON)

### Bước 3.1: Mở rộng `PipelineController` hỗ trợ các cờ Ablation
**File**: [`core/pipeline_controller.py`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/pipeline_controller.py)

Bổ sung các tham số cấu hình tùy biến vào `__init__`:
```python
def __init__(
    self,
    agent: LLMAgent,
    engine: DafnyEngine,
    max_k: int = 3,
    verbose: bool = True,
    enable_topology: bool = True,
    enable_normalizer: bool = True,
    enable_spec_locker: bool = True,
    enable_semantic_hints: bool = True,
    enable_cegar: bool = True,
):
```
- Khi `enable_normalizer=False`: Giữ nguyên mã thô do LLM sinh ra, không gọi `SyntaxNormalizer.normalize()`.
- Khi `enable_topology=False`: Không chèn chỉ dẫn khung bất biến hình thái vào prompt.
- Khi `enable_semantic_hints=False`: Chỉ truyền trực tiếp thông báo lỗi thô của Dafny CLI sang prompt sửa lỗi (giống Stanford Clover).
- Khi `enable_spec_locker=False`: Vẫn tính toán kiểm tra mã băm để ghi nhận tỷ lệ vi phạm đặc tả $H_1$, nhưng không ngắt sớm tiến trình để đo lường toàn diện hành vi của LLM.

---

### Bước 3.2: Xây dựng module trích xuất bảng LaTeX chuẩn bài báo (`core/latex_exporter.py`)
**File MỚI**: [`core/latex_exporter.py`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/core/latex_exporter.py)

Triển khai class `LaTeXExporter` chuyên trách:
- `generate_clover_comparison_table(results_data: Dict[str, Any]) -> str`:
  - Tạo bảng LaTeX chuẩn `booktabs` (`\toprule`, `\midrule`, `\bottomrule`).
  - Hiển thị so sánh từng khía cạnh:
    - Pass@1 Rate (%)
    - Pass@K Rate (%)
    - Spec-Tampering Rate $H_1$ (%)
    - Average Repair Loops
    - Average Convergence Time (s)
    - CEGAR Recovery Count
  - Hỗ trợ đánh dấu đậm (`\textbf{...}`) giá trị tốt nhất trong từng chỉ số.

---

### Bước 3.3: Xây dựng script thực nghiệm tự động (`experiments/run_clover_baseline_comparison.py`)
**File MỚI**: [`experiments/run_clover_baseline_comparison.py`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/experiments/run_clover_baseline_comparison.py)

- Chạy kiểm thử đối đầu giữa 2 cấu hình trên cùng một tập bài toán (hỗ trợ preset: `sample` 5 bài, `core` 16 bài, hoặc `all` 30 bài).
- Lưu kết quả chi tiết xuống:
  `artifacts/results/clover_vs_our_system_baseline.json`
- Tự động in bảng tóm tắt đối đầu và sinh mã LaTeX ra màn hình terminal.

---

### Bước 3.4: Tích hợp nút xuất/sao chép mã LaTeX vào giao diện Web
**File**: [`web_demo/tabs/tab_metrics_view.py`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/web_demo/tabs/tab_metrics_view.py)

- Bổ sung một khu vực chuyên biệt: **"Bảng Đối Chuẩn Ablation Study (Stanford Clover vs. Our System)"**.
- Hiển thị bảng so sánh trực quan trên web.
- Cung cấp nút bấm:
  - 📋 **Sao chép mã LaTeX Overleaf**
  - 💾 **Tải xuống tệp `table_ablation_clover.tex`**

---

### Bước 3.5: Tạo bộ kiểm thử tự động `tests/test_clover_ablation.py`
**File MỚI**: [`tests/test_clover_ablation.py`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/tests/test_clover_ablation.py)

Kiểm thử:
1. `test_pipeline_ablation_flags`: Kiểm tra `PipelineController` tắt mở chuẩn xác các module khi đặt các cờ `enable_*`.
2. `test_latex_exporter_syntax`: Kiểm tra mã LaTeX sinh ra đúng cú pháp `booktabs`, không thiếu thẻ đóng, hỗ trợ đầy đủ ký tự escape.
3. `test_latex_exporter_highlight`: Kiểm tra thuật toán bôi đậm chỉ số tối ưu.
4. `test_clover_baseline_runner_mock`: Kiểm tra luồng chạy của script runner.

---

### Bước 3.6: Kiểm thử toàn bộ hệ thống & Cập nhật CHANGELOG
- Chạy `pytest` bảo đảm 100% tests passed.
- Cập nhật [`CHANGELOG.md`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/CHANGELOG.md) phiên bản `[1.5.0-step3]`.
- Cập nhật [`implementation_plan_all_improvements.md`](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/implementation_plan_all_improvements.md).
