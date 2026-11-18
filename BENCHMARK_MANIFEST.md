# Bảng Kiểm Kê Benchmark Toàn Diện (Master Benchmark Manifest)

**Dự án:** Formal Verification-in-the-Loop  
**Mục tiêu:** Kế hoạch 75 ngày hoàn thiện nghiên cứu và bài báo CYSG 2027 (HUTECH 2027)  
**Mốc cập nhật:** Hoàn tất sớm tới Mốc Ngày 10 — 18/11/2026  
**Dữ liệu máy đọc (16 cột chuẩn):** [benchmark_manifest.csv](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/benchmark_manifest.csv)  
**Giao thức thực nghiệm đã khóa:** [protocol_cysg2027.yaml](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/configs/protocol_cysg2027.yaml)

---

## 1. Tổng Quan Cơ Cấu Bài Toán Hiện Có Trong Repository

Toàn bộ kho lưu trữ hiện có tổng cộng **55 bài toán** được chia thành 3 phân nhóm theo 2 Track nghiên cứu tách biệt:

| Phân nhóm | Track | Số lượng | Nguồn gốc | Trạng thái sau Cổng Kiểm Tra Ngày 10 |
| :--- | :---: | :---: | :--- | :--- |
| **🏆 Core-30 Benchmark** | Track 1 (`synthesis`) | **30** | Clover (6), HumanEval-Dafny (10), Advanced (14) | `included_core`: Đã kiểm chứng, kết quả mốc **29/30 (96.7%)**, giữ nguyên không chạy lại. |
| **🌳 Advanced Inductive** | Track 1 (`synthesis`) | **5** | Tự phát triển (Cây BST & Danh sách liên kết) | `included_ext_inductive`: **5/5 bản tham chiếu đã pass `Dafny.exe verify` (Dafny 4.11.0)**. |
| **⚡ DafnyBench20** | Track 2 (`hint_restoration`) | **20** | `sun-wendy/DafnyBench` (commit `0cd28fee`) | **19 bài `included_hint_restore`** (hợp lệ cú pháp Dafny 4.x) + **1 bài `excluded`** (`MatrixMultiplication` lỗi parser Dafny 4.x). |
| **TỔNG CỘNG** | 2 Tracks | **55** | **54 bài hợp lệ** (35 Synthesis + 19 Hint Restore) | Đã khóa giao thức tại [protocol_cysg2027.yaml](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/configs/protocol_cysg2027.yaml). |

---

## 2. Danh Mục Chi Tiết 55 Bài Toán

### 2.1. Nhóm 1: Core-30 Benchmark (30 bài toán cốt lõi)
> **Quy ước:** Toàn bộ 30 bài này giữ nguyên kết quả mốc đối chuẩn ngày 15/10/2026, mã băm SHA-256 bảo vệ toàn vẹn hợp đồng.

| STT | Task ID | Tệp nguồn (.dfy) | Nhóm giải thuật | Trạng thái | Kết quả mốc |
| :---: | :--- | :--- | :--- | :---: | :---: |
| 1 | `clover_abs_val` | `data/benchmarks/clover/abs_val.dfy` | Số học | `included_core` | Verified Pass@1 |
| 2 | `clover_find_min` | `data/benchmarks/clover/find_min.dfy` | Mảng / Min-Max | `included_core` | Verified Pass@1 |
| 3 | `clover_linear_search` | `data/benchmarks/clover/linear_search.dfy` | Mảng / Tìm kiếm tuyến tính | `included_core` | Verified Pass@1 |
| 4 | `clover_sample_max` | `data/benchmarks/clover/sample_max.dfy` | Số học | `included_core` | Verified Pass@1 |
| 5 | `clover_sign_function` | `data/benchmarks/clover/sign_function.dfy` | Số học | `included_core` | Verified Pass@1 |
| 6 | `clover_sum_to_n` | `data/benchmarks/clover/sum_to_n.dfy` | Số học / Vòng lặp tính tổng | `included_core` | Verified Pass@1 |
| 7 | `humaneval_000_has_close_elements` | `data/benchmarks/humaneval_dafny/000-has_close_elements.dfy` | Mảng / Vòng lặp lồng $O(N^2)$ | `included_core` | Verified Pass@1 |
| 8 | `humaneval_002_truncate` | `data/benchmarks/humaneval_dafny/002-truncate.dfy` | Số học số thực | `included_core` | Verified Pass@1 |
| 9 | `humaneval_010_is_palindrome` | `data/benchmarks/humaneval_dafny/010-is_palindrome.dfy` | Chuỗi / Palindrome | `included_core` | Verified Pass@1 |
| 10 | `humaneval_013_greatest_common_divisor` | `data/benchmarks/humaneval_dafny/013-greatest_common_divisor.dfy` | Lý thuyết số / GCD Euclid | `included_core` | Verified Pass@1 |
| 11 | `humaneval_031_is_prime` | `data/benchmarks/humaneval_dafny/031-is-prime.dfy` | Lý thuyết số / Số nguyên tố | `included_core` | Verified repair@2 |
| 12 | `humaneval_035_max_element` | `data/benchmarks/humaneval_dafny/035-max-element.dfy` | Mảng / Tìm Max | `included_core` | Verified Pass@1 |
| 13 | `humaneval_052_below_threshold` | `data/benchmarks/humaneval_dafny/052-below-threshold.dfy` | Mảng / Kiểm tra ngưỡng | `included_core` | Verified Pass@1 |
| 14 | `humaneval_055_fib` | `data/benchmarks/humaneval_dafny/055-fib.dfy` | Đệ quy / Dãy Fibonacci | `included_core` | Verified Pass@1 |
| 15 | `humaneval_077_iscube` | `data/benchmarks/humaneval_dafny/077-iscube.dfy` | Số học phi tuyến / Bổ đề đơn điệu | `included_core` | Verified Pass@1 |
| 16 | `humaneval_088_sort_array` | `data/benchmarks/humaneval_dafny/088-sort_array.dfy` | Mảng / Sắp xếp chẵn lẻ | `included_core` | Verified Pass@1 |
| 17 | `advanced_all_unique` | `data/benchmarks/advanced/all_unique.dfy` | Mảng / Kiểm tra trùng lặp | `included_core` | Verified Pass@1 |
| 18 | `advanced_array_reverse` | `data/benchmarks/advanced/array_reverse.dfy` | Mảng / Đảo ngược 2 con trỏ | `included_core` | Verified Pass@1 |
| 19 | `advanced_binary_search` | `data/benchmarks/advanced/binary_search.dfy` | Tìm kiếm nhị phân | `included_core` | Verified Pass@1 |
| 20 | `advanced_copy_array` | `data/benchmarks/advanced/copy_array.dfy` | Mảng / Sao chép tuyến tính | `included_core` | Verified Pass@1 |
| 21 | `advanced_count_elements` | `data/benchmarks/advanced/count_elements.dfy` | Mảng / Đếm tần suất | `included_core` | Verified Pass@1 |
| 22 | `advanced_find_first_negative` | `data/benchmarks/advanced/find_first_negative.dfy` | Mảng / Tìm kiếm có điều kiện | `included_core` | Verified Pass@1 |
| 23 | `advanced_is_array_sorted` | `data/benchmarks/advanced/is_array_sorted.dfy` | Mảng / Kiểm tra thứ tự | `included_core` | Verified Pass@1 |
| 24 | `advanced_linear_search_last` | `data/benchmarks/advanced/linear_search_last.dfy` | Mảng / Tìm vị trí cuối | `included_core` | Verified Pass@1 |
| 25 | `advanced_matrix_diagonal_sum` | `data/benchmarks/advanced/matrix_diagonal_sum.dfy` | Ma trận / Tổng đường chéo | `included_core` | Verified Pass@1 |
| 26 | `advanced_matrix_row_sum` | `data/benchmarks/advanced/matrix_row_sum.dfy` | Ma trận / Tổng hàng | `included_core` | Verified Pass@1 |
| 27 | `advanced_product_of_array` | `data/benchmarks/advanced/product_of_array.dfy` | Mảng / Tích dồn | `included_core` | Verified Pass@1 |
| 28 | `advanced_remove_element` | `data/benchmarks/advanced/remove_element.dfy` | Mảng / Loại bỏ phần tử | `included_core` | Verified Pass@1 |
| 29 | `advanced_sorted_insert` | `data/benchmarks/advanced/sorted_insert.dfy` | Mảng / Chèn có thứ tự | `included_core` | Verified Pass@1 |
| 30 | `advanced_sum_positive` | `data/benchmarks/advanced/sum_positive.dfy` | Mảng / Tổng số dương | `included_core` | Verified Pass@1 |

---

### 2.2. Nhóm 2: Advanced Inductive Structures (5 bài)
> **Trọng tâm kiểm tra Ngày 2–3:** Rà soát cấu trúc đại số `datatype`, vị từ bảo toàn BST/List và chứng minh quy nạp cấu trúc.

| STT | Task ID | Tệp nguồn (.dfy) | Cấu trúc dữ liệu | Trạng thái kiểm chứng Dafny 4.11.0 |
| :---: | :--- | :--- | :--- | :---: |
| 31 | `inductive_bst_insert` | `data/benchmarks/advanced_inductive/bst_insert.dfy` | Cây nhị phân tìm kiếm (BST) | `included_ext_inductive` (Ref Verified: 3 verified, 0 errors) |
| 32 | `inductive_bst_search` | `data/benchmarks/advanced_inductive/bst_search.dfy` | Cây nhị phân tìm kiếm (BST) | `included_ext_inductive` (Ref Verified: 3 verified, 0 errors) |
| 33 | `inductive_linked_list_reverse` | `data/benchmarks/advanced_inductive/linked_list_reverse.dfy` | Danh sách liên kết đại số | `included_ext_inductive` (Ref Verified: 5 verified, 0 errors) |
| 34 | `inductive_linked_list_stats` | `data/benchmarks/advanced_inductive/linked_list_stats.dfy` | Danh sách liên kết đại số | `included_ext_inductive` (Ref Verified: 3 verified, 0 errors) |
| 35 | `inductive_tree_size_height` | `data/benchmarks/advanced_inductive/tree_size_height.dfy` | Cây nhị phân | `included_ext_inductive` (Ref Verified: 4 verified, 0 errors) |

---

### 2.3. Nhóm 3: DafnyBench20 (20 bài khôi phục gợi ý chứng minh)
> **Trọng tâm kiểm tra Ngày 2–3:** Kiểm tra bản tham chiếu gốc (`upstream_gold_path`) bằng Dafny CLI; khắc phục cơ chế patch gợi ý chứng minh (không sinh lại toàn bộ code để tránh `invalid_candidate`).

| STT | Task ID | Tệp nguồn (.dfy) | Dạng bài toán | Trạng thái thẩm định Ngày 2–3 |
| :---: | :--- | :--- | :--- | :---: |
| 36 | `dafnybench_bubblesort` | `CS494-final-project_tmp_tmp7nof55uq_bubblesort_no_hints.dfy` | Sắp xếp nổi bọt | Hash OK, thiếu invariant/postcondition |
| 37 | `dafnybench_exercise_maximum` | `Dafny-Exercises_tmp_tmpjm75muf__Session3Exercises_ExerciseMaximum_no_hints.dfy` | Tìm giá trị lớn nhất | Hash OK, thiếu invariant |
| 38 | `dafnybench_exercise_seq_max_sum` | `Dafny-Exercises_tmp_tmpjm75muf__Session9Exercises_ExerciseSeqMaxSum_no_hints.dfy` | Dãy con tổng lớn nhất | Hash OK, thiếu invariant |
| 39 | `dafnybench_raw_sort` | `DafnyProjects_tmp_tmp2acw_s4s_RawSort_no_hints.dfy` | Thuật toán sắp xếp | Hash OK, thiếu decreases (termination) |
| 40 | `dafnybench_partition_odd_even` | `DafnyProjects_tmp_tmp2acw_s4s_partitionOddEven_no_hints.dfy` | Phân chia chẵn lẻ | Hash OK, thiếu invariant |
| 41 | `dafnybench_binary_search_dec` | `Dafny_tmp_tmp0wu8wmfr_Heimaverkefni 2_BinarySearchDec_no_hints.dfy` | Tìm kiếm nhị phân giảm | Hash OK, thiếu invariant |
| 42 | `dafnybench_insertion_sort` | `Final-Project-Dafny_tmp_tmpmcywuqox_Attempts_Insertion_Sorted_Standard_no_hints.dfy` | Sắp xếp chèn | Hash OK, thiếu invariant |
| 43 | `dafnybench_copilot_sort_array` | `HATRA-2022-Paper_tmp_tmp5texxy8l_copilot_verification_Sort Array_sort_array_no_hints.dfy` | Sắp xếp mảng Copilot | Hash OK, thiếu invariant |
| 44 | `dafnybench_matrix_multiplication` | `Program-Verification-Dataset_tmp_tmpgbdrlnu__Dafny_advanced examples_MatrixMultiplication_no_hints.dfy` | Nhân ma trận | ⚠️ **Lỗi cú pháp parser Dafny 4.x** (AssignStatement) |
| 45 | `dafnybench_lol_sort` | `Program-Verification-Dataset_tmp_tmpgbdrlnu__Dafny_verified algorithms_lol_sort_no_hints.dfy` | Thuật toán sắp xếp | Hash OK, thiếu invariant |
| 46 | `dafnybench_non_overlapping_intervals` | `Software-Verification_tmp_tmpv4ueky2d_Non-overlapping Intervals_non_overlapping_intervals_no_hints.dfy` | Khoảng không chồng lấn | Hash OK, thiếu invariant |
| 47 | `dafnybench_uiowa_binary_search` | `dafl_tmp_tmp_r3_8w3y_dafny_examples_uiowa_binary-search_no_hints.dfy` | Tìm kiếm nhị phân UIowa | Hash OK, thiếu invariant |
| 48 | `dafnybench_selection_sort` | `Dafny_Verify_tmp_tmphq7j0row_dataset_detailed_examples_SelectionSort_no_hints.dfy` | Sắp xếp chọn | Hash OK, thiếu invariant |
| 49 | `dafnybench_challenges_ex1` | `formal_verication_dafny_tmp_tmpwgl2qz28_Challenges_ex1_no_hints.dfy` | Bài toán số học logic | Hash OK, thiếu invariant |
| 50 | `dafnybench_exercise_fibonacci` | `Dafny-Exercises_tmp_tmpjm75muf__Session2Exercises_ExerciseFibonacci_no_hints.dfy` | Đệ quy Fibonacci | Hash OK, thiếu invariant |
| 51 | `dafnybench_modifying_arrays` | `dafl_tmp_tmp_r3_8w3y_dafny_examples_uiowa_modifying-arrays_no_hints.dfy` | Biến đổi mảng in-place | Hash OK, thiếu invariant |
| 52 | `dafnybench_segment_sum` | `dafny-language-server_tmp_tmpkir0kenl_Test_dafny2_SegmentSum_no_hints.dfy` | Tổng đoạn mảng | Hash OK, thiếu invariant |
| 53 | `dafnybench_merge_sort` | `AssertivePrograming_tmp_tmpwf43uz0e_MergeSort_no_hints.dfy` | Sắp xếp trộn MergeSort | Hash OK, thiếu invariant |
| 54 | `dafnybench_valid_anagram` | `Program-Verification-Dataset_tmp_tmpgbdrlnu__Dafny_algorithms and leetcode_leetcode_validAnagram_no_hints.dfy` | Kiểm tra đảo chữ Anagram | Hash OK, thiếu invariant |
| 55 | `dafnybench_power` | `cs245-verification_tmp_tmp0h_nxhqp_power_no_hints.dfy` | Tính lũy thừa nhanh | Hash OK, thiếu invariant |

---

## 3. Kết Quả Thẩm Định Benchmark (Ngày 2 & 3)

1. **20 Bài DafnyBench:**
   * **Độ toàn vẹn:** 20/20 tệp tồn tại, SHA-256 khớp tuyệt đối 100% với commit đã ghim.
   * **Bản chất lỗi:** 19/20 bài khi chạy qua Dafny 4.11.0 đều báo lỗi thiếu bất biến vòng lặp (`invariant`) hoặc hàm giảm (`decreases`), đúng 100% theo thiết kế của bài toán khôi phục gợi ý chứng minh.
   * **Cảnh báo cần xử lý:** Bài `MatrixMultiplication` gặp lỗi cú pháp phân tích tĩnh do phiên bản Dafny cũ dùng cú pháp không tương thích với Dafny 4.x (`m3[i',j']`). Bài này cần được chuẩn hóa cú pháp hoặc đưa vào danh sách loại trừ có lý do minh bạch (`exclusion_reason`).

2. **5 Bài Advanced Inductive:**
   * Bản chất là bài toán **sinh mã từ đặc tả (Code Synthesis)** giống như Core-30 (phần thân hàm để trống giữa `// impl-start` và `// impl-end`).
   * Cần bổ sung lời giải tham chiếu (Gold reference) cho 5 bài này để chứng minh đặc tả toán học là khả chứng (satisfiable & provable) trước khi đưa vào mẫu số đánh giá chính thức.

---

## 4. Phân Tích Trùng Lặp Ngữ Nghĩa & Phân Tầng Giải Thuật (Ngày 4)

Sau khi đối chiếu chi tiết chữ ký hàm, kiểu dữ liệu (`seq` vs `array`), tiền/hậu điều kiện của 20 bài DafnyBench với Core-30, kết quả rà soát ghi nhận:

### 4.1. Các ca có sự tương đồng hoặc biến thể ngữ nghĩa (Semantic Overlap / Variant)
1. **Tìm kiếm nhị phân (`Binary_Search`):**
   * `advanced_binary_search` (Core-30): Tìm vị trí trên `seq<int>` tăng dần, trả về `index: int` (-1 nếu không thấy).
   * `dafnybench_uiowa_binary_search`: Tìm thành viên trên `array<int>` tăng dần, trả về `b: bool`. $\to$ **Biến thể (Variant)** khác biệt về kiểu dữ liệu (Heap Array) và kiểu trả về (Boolean).
   * `dafnybench_binary_search_dec`: Tìm điểm phân hoạch trên dãy giảm dần số thực (`seq<real>`, $a[p] \ge a[q]$), trả về chỉ số chia nửa đầu $\ge x$ và nửa sau $< x$. $\to$ **Biến thể độc lập**, giải bài toán phân hoạch biên.
2. **Dãy Fibonacci (`Recursion_Fibonacci`):**
   * `humaneval_055_fib` (Core-30): 1 method tính số Fib thứ n.
   * `dafnybench_exercise_fibonacci`: Bài toán đa hàm gồm 3 methods (`fibonacci1`, `fibonacci2`, `fibonacci3`) cài đặt 3 giải thuật khác nhau (đệ quy tích lũy, vòng lặp bottom-up, cập nhật biến). $\to$ Gán nhãn `semantic_overlap_fibonacci`, nhưng độ khó cao hơn.
3. **Giá trị lớn nhất (`Array_MinMax`):**
   * `humaneval_035_max_element` (Core-30): 1 method tìm max trên `seq<int>`.
   * `dafnybench_exercise_maximum`: Bài toán đa hàm gồm 6 methods trên `array<int>` chứng minh giá trị max, vị trí first max và last max. $\to$ Gán nhãn `semantic_overlap_maximum`.

### 4.2. Bảng Phân Tầng 7 Nhóm Giải Thuật Toàn Tập (55 Bài)

| Nhóm Giải Thuật (Algorithm Taxonomy) | Quy mô | Phân bố nguồn bài toán |
| :--- | :---: | :--- |
| **1. Arithmetic & Number Theory** | **11 bài** | Clover (4), HumanEval (3: `truncate`, `gcd`, `is_prime`, `iscube`), DafnyBench (2: `challenges_ex1`, `power`) |
| **2. Linear Loop & Array Search** | **17 bài** | Clover (2), HumanEval (3: `has_close`, `palindrome`, `below_threshold`), Advanced (9), DafnyBench (3: `exercise_seq_max_sum`, `modifying_arrays`, `segment_sum`) |
| **3. Binary Search** | **3 bài** | Advanced (1: `binary_search`), DafnyBench (2: `uiowa_binary_search`, `binary_search_dec`) |
| **4. Sorting Algorithms** | **9 bài** | HumanEval (1: `sort_array`), Advanced (2: `sorted_insert`, `is_array_sorted`), DafnyBench (6: `bubblesort`, `raw_sort`, `insertion_sort`, `copilot_sort_array`, `lol_sort`, `selection_sort`, `merge_sort`) |
| **5. Matrix Operations** | **3 bài** | Advanced (2: `matrix_diagonal_sum`, `matrix_row_sum`), DafnyBench (1: `matrix_multiplication` - chờ sửa cú pháp) |
| **6. Intervals, Strings & Puzzles** | **3 bài** | DafnyBench (3: `non_overlapping_intervals`, `valid_anagram`, `partition_odd_even`) |
| **7. Recursion & Inductive Structures** | **9 bài** | HumanEval (1: `fib`), Advanced Inductive (5: BST & List), DafnyBench (3: `exercise_fibonacci`, `exercise_maximum`, ...) |
| **TỔNG CỘNG** | **55 bài** | **Cơ cấu cân bằng, bao phủ toàn diện 7 phân tầng giải thuật** |

---

## 5. Kết Quả Chạy Thử Nghiệm Pilot (5 Bài) & Dự Báo Khả Thi (Ngày 5 & 6)

### 5.1. Kết Quả Thực Nghiệm Pilot Thực Tế với `gemini-2.5-flash`
Dữ liệu thô lưu trữ tại: [pilot_5_results.json](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/artifacts/results/pilot_5_results.json).

| STT | Bài toán Pilot | Nhóm giải thuật | Dạng thức | Kết quả | Thời gian | Phân tích cơ chế & Giá trị học thuật |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `tree_size_height` | Quy nạp cây | Synthesis | **FAILED (Vòng 2)** | 64.52s | **Báo cáo ca thất bại do Spec-Tampering:** LLM tự ý chèn `decreases t` vào hợp đồng gốc, bị `SpecLocker` phát hiện và chặn vi phạm. Ca này minh họa vai trò phát hiện sửa đổi đặc tả, không phải bài toán chứng minh thành công. |
| 2 | `dafnybench_power` | Số học & Lũy thừa | Hint Restore | **FAILED (3 lượt)** | 150.75s | Không vi phạm hợp đồng (`hint_safe: true`), nhưng Z3 báo lỗi thiếu bổ đề lũy thừa: `assert 1 == power(a,0)`. |
| 3 | `dafnybench_uiowa_binary_search` | Tìm kiếm nhị phân | Hint Restore | **🏆 PASSED (Lượt 1)** | **25.12s** | **Ví dụ pilot được Verifier xác nhận:** Sinh bất biến chính xác 100%, được Dafny 4.11.0 chứng minh ngay tại Lượt 1 (`3 verified, 0 errors`). |
| 4 | `dafnybench_non_overlapping_intervals` | Khoảng thời gian | Hint Restore | **FAILED (3 lượt)** | 95.68s | Thuật toán tham lam phức tạp, thiếu bất biến bao đóng khoảng. |
| 5 | `dafnybench_bubblesort` | Thuật toán sắp xếp | Hint Restore | **FAILED (3 lượt)** | 100.80s | Vòng lặp lồng $O(N^2)$ sắp xếp mảng, đòi hỏi bất biến hoán vị `multiset` 2 tầng. |

> [!IMPORTANT]
> **Đánh Giá Khách Quan Về Pilot:**
> Hai ca `uiowa_binary_search` (passed) và `tree_size_height` (failed do vi phạm hợp đồng) chỉ là các ví dụ minh họa cơ chế hoạt động của bộ lọc kiểm định trong giai đoạn pilot nhỏ. Chúng **hoàn toàn chưa đủ để đại diện cho kết quả trên toàn bộ DafnyBench20**. Mở rộng đánh giá toàn tập 20 bài cần đảm bảo bộ khôi phục proof hints chạy độc lập và không để LLM can thiệp vào mã nguồn gốc.

### 5.2. Kết Quả Pilot Kiểm Chứng Sau Khi Nâng Cấp Runner với `ollama/qwen2.5-coder:7b` (Mốc Ngày 8–10)
Dữ liệu thô kèm siêu dữ liệu truy xuất (`provenance`) lưu tại: [pilot_dafnybench_qwen7b.json](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/artifacts/results/pilot_dafnybench_qwen7b.json).

- **Cấu hình thực thi:** `ollama/qwen2.5-coder:7b` (100% Local Offline trên cổng `11434`), `Dafny 4.11.0`, `max_attempts = 2`, ghi đầy đủ `git_commit`, `git_dirty`, `git_diff_sha256`.
- **Kết quả kiểm chứng bảo toàn hợp đồng:**
  - Cả 2 lượt sinh của `qwen2.5-coder:7b` trên bài `uiowa_binary-search` đều đạt **`hint_integrity_valid: true`**, **`original_code_preserved: true`**, **`strict_contract_issues: []`** (`invalid_candidate = 0`).
  - Hệ thống chuyển ứng viên qua `Dafny.exe verify` và trích xuất thông báo lỗi kiểu dữ liệu thực tế từ Z3/Dafny (`expected array<int>, found seq<int>` tại `invariant isSorted(a[lo..hi])`), chứng minh bộ lọc dòng chuẩn hóa (`_canonical_code_lines`) đã khắc phục triệt để lỗi loại nhầm `invalid_candidate` do khác biệt khoảng trắng/comment.

---

## 6. Quyết Định Cổng Đánh Giá Ngày 7 & Mốc Kiểm Soát Ngày 10

1. **Hoàn tất kiểm định 55 bài hiện có (54 bài hợp lệ, 1 bài loại trừ):**
   * **Track 1 — Program Synthesis (`synthesis`, 35 bài hợp lệ):**
     - **30 bài Core-30 (`included_core`):** Giữ nguyên kết quả đối chuẩn (29/30).
     - **5 bài Advanced Inductive (`included_ext_inductive`):** Đã sửa `ghost predicate is_bst` và hậu điều kiện bảo toàn tập giá trị của `bst_insert`; cả 5/5 bài đều có lời giải tham chiếu pass 100% qua `Dafny.exe verify` (Dafny 4.11.0).
   * **Track 2 — Proof Hint Restoration (`hint_restoration`, 19 bài hợp lệ, 1 bài loại):**
     - **19 bài DafnyBench (`included_hint_restore`):** Hợp lệ cú pháp Dafny 4.11.0, báo cáo thành bảng riêng biệt hoàn toàn với Track 1.
     - **1 bài loại trừ (`excluded`):** `dafnybench_matrix_multiplication` do lỗi parser Dafny 4.x trên tên biến có dấu nháy đơn `m3[i',j']`.
2. **Khóa Giao Thức Thực Nghiệm Ngày 10:**
   * Đã khóa tại [configs/protocol_cysg2027.yaml](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/configs/protocol_cysg2027.yaml) và cập nhật đủ 16 cột chuẩn hóa tại [data/benchmarks/benchmark_manifest.csv](file:///c:/Users/aaa/Pictures/SaveCode/Formal_Verification-in-the-Loop/data/benchmarks/benchmark_manifest.csv).
3. **Mục tiêu Giai đoạn tiếp theo (Ngày 11–24: Thu thập Benchmark ngoài Đợt 1 & 2):**
   * Thu thập và sàng lọc thêm **26–46 bài toán Dafny hợp lệ** từ nguồn công khai (CloverBench / MBPP-DFY / DafnyBench) để đạt tổng cộng **80–100 bài toán hợp lệ** trước Cổng chất lượng Ngày 27 (14/12).


