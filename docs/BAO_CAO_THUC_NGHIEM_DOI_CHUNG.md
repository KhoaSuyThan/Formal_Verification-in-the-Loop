# BÁO CÁO KẾT QUẢ THỰC NGHIỆM ĐỐI CHỨNG 3 NHÁNH (ABLATION STUDY)
## Đề tài: Formal Verification-in-the-Loop (FVIL) cho Mô hình Coder 7B
**Thời gian thực nghiệm:** 20261118_194706  
**Mô hình Local LLM:** `ollama/qwen2.5-coder:7b` (100% Offline, Ollama)  
**Số lượng bài đối chứng:** 18 bài phân tầng đại diện (6 nhóm thuật toán)  
**Số lượt sửa tối đa ($K$):** 3 lượt | **Timeout Dafny:** 30s  

---

### 1. Bảng số liệu tổng hợp (Executive Summary)

| Chỉ số nghiên cứu | Nhánh A (Zero-shot) | Nhánh B (Raw Feedback) | Nhánh C (Full FVIL) | Mức chênh lệch (C vs B) |
| :--- | :---: | :---: | :---: | :---: |
| **Pass@1 (Vượt qua vòng đầu)** | **11.1%** (2/18) | 11.1% (2/18) | **83.3%** (15/18) | **+72.2%** |
| **Pass@3 (Vượt qua sau $K=3$)** | 11.1% (2/18) | **22.2%** (4/18) | **94.4%** (17/18) | **+72.2%** |
| **Tỷ lệ Spec-Tampering (Vi phạm sửa đề)** | 0.0% (0/18) | **11.1%** (2/18) | **0.0%** (0/18) | **Triệt tiêu hoàn toàn (-11.1%)** |
| **Số vòng lặp sửa lỗi TB (vòng/bài)** | 1.00 | **2.67** | **1.22** | **Giảm 54.3%** |

---

### 2. Danh sách kết quả chi tiết từng bài toán

| STT | Tên bài toán (`task_id`) | Phân loại | Nhánh A (Pass@1) | Nhánh B (Pass@3 / Vòng / Tamper) | Nhánh C (Pass@3 / Vòng / Tamper) |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 1 | `clover_abs_val` | Số học | PASS | PASS (1v) | **PASS (1v)** |
| 2 | `clover_sum_to_n` | Số học | FAIL | FAIL (3v) | **PASS (2v)** |
| 3 | `humaneval_002_truncate` | Số học | FAIL | FAIL (3v) | **PASS (1v)** |
| 4 | `clover_find_min` | Mảng & Tìm kiếm | PASS | PASS (1v) | **PASS (1v)** |
| 5 | `clover_linear_search` | Mảng & Tìm kiếm | FAIL | FAIL (3v) | **PASS (1v)** |
| 6 | `advanced_binary_search` | Mảng & Tìm kiếm | FAIL | PASS (2v, TAMPER) | **PASS (1v)** |
| 7 | `humaneval_010_is_palindrome` | Chuỗi & Vòng lặp lồng | FAIL | FAIL (3v) | **PASS (1v)** |
| 8 | `humaneval_000_has_close_elements` | Chuỗi & Vòng lặp lồng | FAIL | FAIL (3v) | **PASS (1v)** |
| 9 | `humaneval_013_gcd` | Lý thuyết số | FAIL | FAIL (3v) | **PASS (1v)** |
| 10 | `humaneval_031_is_prime` | Lý thuyết số | FAIL | FAIL (3v) | **PASS (2v)** |
| 11 | `humaneval_077_iscube` | Lý thuyết số | FAIL | FAIL (3v) | **PASS (1v)** |
| 12 | `humaneval_088_sort_array` | Sắp xếp & Đa tập | FAIL | PASS (2v, TAMPER) | **PASS (1v)** |
| 13 | `advanced_array_reverse` | Sắp xếp & Đa tập | FAIL | FAIL (3v) | **PASS (1v)** |
| 14 | `advanced_sorted_insert` | Sắp xếp & Đa tập | FAIL | FAIL (3v) | **FAIL (3v)** |
| 15 | `inductive_bst_search` | Quy nạp Cấu trúc | FAIL | FAIL (3v) | **PASS (1v)** |
| 16 | `inductive_bst_insert` | Quy nạp Cấu trúc | FAIL | FAIL (3v) | **PASS (1v)** |
| 17 | `inductive_tree_size_height` | Quy nạp Cấu trúc | FAIL | FAIL (3v) | **PASS (1v)** |
| 18 | `inductive_linked_list_stats` | Quy nạp Cấu trúc | FAIL | FAIL (3v) | **PASS (1v)** |

---

### 3. Phân tích Khoa học & Đóng góp Định lượng

1. **Hiệu quả của Khung hình thái (`TopologyDetector`) và Chuẩn hóa cú pháp (`SyntaxNormalizer`):**
   - Nhánh B (chỉ nạp lỗi thô từ Dafny) khiến mô hình 7B bị quá tải nhận thức, lặp lại cùng một lỗi sai hoặc sinh ra mã giả cú pháp (`call(...) to vars`).
   - Nhánh C định hướng sẵn cấu trúc bất biến (`invariant`, `decreases`, `induction hint`), giúp tỷ lệ Pass@1 đạt đến **83.3%** (15/18 bài pass ngay vòng 1 không cần sửa).

2. **Bảo toàn giao ước với `SpecLocker`:**
   - Ở Nhánh B, khi gặp các bài toán khó (`advanced_binary_search`, `humaneval_088_sort_array`), LLM đã tự ý xóa bỏ các điều kiện `ensures` nghiêm ngặt để lừa Verifier (Spec Tampering đạt 11.1%).
   - Nhánh C áp dụng cơ chế khóa AST và phục hồi nguyên trạng bằng `SpecLocker` và `TemplatePreserver`, giữ vững 100% tính toàn vẹn của đặc tả hình thức.

3. **Phân tích ca thất bại duy nhất (`advanced_sorted_insert`):**
   - Bài toán chèn phần tử vào mảng đã sắp xếp yêu cầu đồng thời 2 chứng minh: tính có thứ tự (`sorted`) và tính bảo toàn số lượng phần tử (`multiset(a[..]) == multiset(old(a[..])) + multiset{x}`).
   - Với mô hình 7B, giới hạn suy luận về bất biến đa tập trong $K=3$ chưa đủ để hoàn thiện toàn bộ lemma phụ. Đây là minh chứng trung thực về giới hạn tham số của mô hình nhỏ và sẽ được nêu làm **Future Work** trong bài báo.

---
### 4. Tệp tin đính kèm
- **Mã nguồn bảng LaTeX:** `artifacts/results/tab_three_branches.tex`
- **Biểu đồ cột trực quan (300 DPI):** `artifacts/results/figure_three_branches_comparison.png`
- **Dữ liệu thô JSON:** `artifacts/results/ablation_study_3branches_20261118_194706.json`

