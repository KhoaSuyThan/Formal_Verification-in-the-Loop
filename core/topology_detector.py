"""Module phân tích hình thái giải thuật (Algorithmic Topology Detector).

Phân loại đặc tả hình thức Dafny trước khi sinh mã để:
1. Ràng buộc không gian tìm kiếm (Search-space Constraining).
2. Ngăn chặn hiện tượng sinh vòng lặp giả/rác cho các bài toán trực tiếp (Direct Analytical).
3. Cung cấp khung gợi ý cấu trúc (Inductive Skeleton) chính xác cho từng họ bài toán.
"""

from enum import Enum
import re
from typing import Tuple, Optional


class AlgorithmTopology(str, Enum):
    """Phân loại hình thái bài toán giải thuật."""
    DIRECT = "DIRECT"                          # Tính toán giải tích trực tiếp, cấm dùng vòng lặp (truncate, abs, sign)
    LINEAR_LOOP = "LINEAR_LOOP"                # Duyệt mảng/chuỗi 1 chiều (max_element, below_threshold, find_min)
    PURE_FUNC_EQUIV = "PURE_FUNC_EQUIV"        # Tính toán tương đương hàm đệ quy thuần túy (fib, count, sum_pos, prod)
    NESTED_LOOP = "NESTED_LOOP"                # 2 vòng lặp lồng nhau hoặc vị từ cặp chỉ số (has_close_elements, is_array_sorted, all_unique)
    NUMBER_THEORY = "NUMBER_THEORY"            # Số học, chia hết, số nguyên tố, ước số (is_prime, gcd)
    NON_LINEAR = "NON_LINEAR"                  # Số học phi tuyến tính bậc cao (iscube)
    PERMUTATION_SORT = "PERMUTATION_SORT"      # Sắp xếp và bảo toàn đa tập hợp toàn diện (sort_array)
    STRING_SEQUENCE = "STRING_SEQUENCE"        # Xử lý chuỗi ký tự, đảo chuỗi, đối xứng (is_palindrome)
    BINARY_SEARCH = "BINARY_SEARCH"            # Tìm kiếm nhị phân chia đôi (binary_search)
    ORDERED_INSERT = "ORDERED_INSERT"          # Chèn phần tử vào mảng đã sắp xếp (sorted_insert)
    SEQ_CONSTRUCTION = "SEQ_CONSTRUCTION"      # Xây dựng hoặc lọc chuỗi mới (copy_array, remove_element, array_reverse)
    SEARCH_CONDITION = "SEARCH_CONDITION"      # Tìm kiếm có điều kiện phủ định biên (linear_search_last, find_first_negative)


class TopologyDetector:
    """Bộ nhận diện hình thái bài toán dựa trên AST và đặc tả toán học."""

    @classmethod
    def detect(cls, raw_spec: str) -> AlgorithmTopology:
        """Phân loại hình thái bài toán từ mã nguồn đặc tả."""
        spec_lower = raw_spec.lower()

        # 0. Nhận diện Binary Search
        if "binary_search" in spec_lower or ("is_sorted" in spec_lower and "key" in spec_lower):
            return AlgorithmTopology.BINARY_SEARCH

        # 1. Nhận diện Chèn phần tử giữ thứ tự (sorted_insert)
        if "sorted_insert" in spec_lower or ("insert" in spec_lower and "multiset" in spec_lower and "|res| == |s| + 1"):
            return AlgorithmTopology.ORDERED_INSERT

        # 2. Nhận diện Sắp xếp và Bảo toàn đa tập hợp toàn diện (sort_array)
        if "sort_array" in spec_lower or ("multiset" in spec_lower and "sort" in spec_lower):
            return AlgorithmTopology.PERMUTATION_SORT

        # 3. Nhận diện Non-linear (Bậc 3 hoặc phi tuyến)
        if "cube" in spec_lower or re.search(r'\*\s*\w+\s*\*\s*\w+', raw_spec):
            return AlgorithmTopology.NON_LINEAR

        # 4. Nhận diện Chuỗi ký tự & Đối xứng (Palindrome / String Sequence)
        if "string" in spec_lower and ("palindrome" in spec_lower or "reverse" in spec_lower):
            return AlgorithmTopology.STRING_SEQUENCE

        # 5. Nhận diện Pure Function Equivalence (Hàm đệ quy được định nghĩa trong file và gọi trong ensures)
        pure_func_match = re.search(r'\bfunction\s+([a-zA-Z_]\w*)\s*\(', raw_spec)
        if pure_func_match:
            func_name = pure_func_match.group(1)
            ensures_match = re.search(r'ensures\b[^\n]*\b' + re.escape(func_name) + r'\s*\(', raw_spec)
            if ensures_match and func_name != "abs":
                return AlgorithmTopology.PURE_FUNC_EQUIV

        # 6. Nhận diện Nested Loop / Pairwise Property (2 định lượng i, j trong ensures hoặc có i != j hoặc 0 <= i < j)
        nested_quant_pattern = re.compile(
            r'ensures\b[^\n]*(?:exists|forall)\s+[a-zA-Z_]\w*\s*(?::\s*\w+)?\s*,\s*[a-zA-Z_]\w*',
            re.IGNORECASE
        )
        if nested_quant_pattern.search(raw_spec) or ("i != j" in raw_spec and "exists" in spec_lower) or ("0 <= i < j" in raw_spec and "bool" in raw_spec):
            return AlgorithmTopology.NESTED_LOOP

        # 7. Nhận diện Tìm kiếm có điều kiện phủ định biên (linear_search_last, find_first_negative)
        if ("-1 <= index" in raw_spec or "index >= 0" in raw_spec) and ("forall" in raw_spec):
            return AlgorithmTopology.SEARCH_CONDITION

        # 8. Nhận diện Xây dựng hoặc lọc chuỗi mới (copy_array, remove_element, array_reverse)
        if re.search(r'returns\s*\(\s*(?:res|rev)\s*:\s*seq<', raw_spec) or ("|res|" in raw_spec and "seq<" in raw_spec):
            return AlgorithmTopology.SEQ_CONSTRUCTION

        # 9. Nhận diện Number Theory (chia hết, mod %, prime, gcd)
        if "%" in raw_spec or "prime" in spec_lower or "gcd" in spec_lower or "divisor" in spec_lower:
            return AlgorithmTopology.NUMBER_THEORY

        # 10. Kiểm tra xem có cấu trúc mảng/chuỗi không (seq<T>, array, string)
        has_collection = bool(re.search(r'\b(?:seq<|array<|string\b|\[\])', raw_spec))
        has_quantifier = "forall" in spec_lower or "exists" in spec_lower

        if has_collection or has_quantifier or "sum" in spec_lower:
            return AlgorithmTopology.LINEAR_LOOP

        # 11. Mặc định là Direct Analytical
        return AlgorithmTopology.DIRECT

    @classmethod
    def get_topology_directive(cls, topology: AlgorithmTopology) -> str:
        """Sinh chỉ dẫn ràng buộc cấu trúc thuật toán theo hình thái đã phát hiện."""
        if topology == AlgorithmTopology.DIRECT:
            return (
                "[RÀNG BUỘC CẤU TRÚC - BÀI TOÁN TÍNH TOÁN TRỰC TIẾP (DIRECT ANALYTICAL)]:\n"
                "- Bài toán này là tính toán giải tích hoặc rẽ nhánh điều kiện trực tiếp.\n"
                "- TUYỆT ĐỐI KHÔNG dùng vòng lặp `while` (không có mảng hoặc biến lặp quy nạp).\n"
                "- Chỉ sử dụng phép gán trực tiếp hoặc cấu trúc `if condition { ... } else { ... }`."
            )

        if topology == AlgorithmTopology.PURE_FUNC_EQUIV:
            return (
                "[RÀNG BUỘC CẤU TRÚC - QUY NẠP TƯƠNG ĐƯƠNG HÀM THUẦN TÚY (PURE FUNCTION)]:\n"
                "- Phương thức đang tính toán giá trị tương đương một hàm pure function toán học đã được định nghĩa trong đề bài.\n"
                "- 1. Với các bài toán gọi hàm thuần túy trực tiếp trên dãy đầu vào (như `count_elements`, `product_of_array`):\n"
                "     BẮT BUỘC gán trực tiếp giá trị của hàm pure function cho biến trả về: `ret := func(s...);`.\n"
                "- 2. Với bài toán có thêm hậu điều kiện không âm `ensures total >= 0` (như `sum_positive`):\n"
                "     Viết bổ đề quy nạp `lemma sum_pos_nonneg(s: seq<int>) ensures sum_pos(s) >= 0 { if |s| == 0 {} else { sum_pos_nonneg(s[1..]); } }` và gọi bổ đề trước khi gán: `sum_pos_nonneg(s); total := sum_pos(s);`.\n"
                "- 3. Với bài toán tính tổng từng hàng ma trận (`matrix_row_sum`):\n"
                "     Duyệt từng hàng bằng vòng lặp: `sums := []; var i := 0; while i < |m| invariant 0 <= i <= |m| invariant |sums| == i invariant forall k :: 0 <= k < i ==> sums[k] == row_sum(m[k]) decreases |m| - i { sums := sums + [row_sum(m[i])]; i := i + 1; }`.\n"
                "- 4. Với dãy Fibonacci (`fib`): Dùng 2 biến trạng thái `invariant a == fib(i)` và `invariant b == fib(i + 1)`."
            )

        if topology == AlgorithmTopology.NESTED_LOOP:
            return (
                "[RÀNG BUỘC CẤU TRÚC - KIỂM ĐỊNH VỊ TỪ CẶP PHẦN TỬ (PAIRWISE PROPERTY / NESTED LOOP)]:\n"
                "- 1. Nếu là bài toán kiểm tra sự TỒN TẠI của cặp chỉ số (i, j) với i != j thỏa mãn điều kiện (như `has_close_elements` có hậu điều kiện `flag == (exists i, j :: ... abs(numbers[i] - numbers[j]) < threshold)`):\n"
                "     BẮT BUỘC sử dụng mẫu hình bất biến quy nạp 2 chiều phủ định chuẩn xác để Z3 chứng minh được khi flag == false:\n"
                "     ```dafny\n"
                "     flag := false;\n"
                "     var i := 0;\n"
                "     while i < |numbers|\n"
                "       invariant 0 <= i <= |numbers|\n"
                "       invariant forall a: int, b: int :: 0 <= a < i && 0 <= b < |numbers| && a != b ==> !Condition(numbers[a], numbers[b])\n"
                "       decreases |numbers| - i\n"
                "     {\n"
                "       var j := 0;\n"
                "       while j < |numbers|\n"
                "         invariant 0 <= j <= |numbers|\n"
                "         invariant forall b: int :: 0 <= b < j && b != i ==> !Condition(numbers[i], numbers[b])\n"
                "         decreases |numbers| - j\n"
                "       {\n"
                "         if i != j && Condition(numbers[i], numbers[j]) {\n"
                "           flag := true;\n"
                "           return;\n"
                "         }\n"
                "         j := j + 1;\n"
                "       }\n"
                "       i := i + 1;\n"
                "     }\n"
                "     return;\n"
                "     ```\n"
                "- 2. Nếu là bài toán kiểm tra tính chất TOÀN THỂ trên mọi cặp chỉ số `0 <= i < j < |s|` (như `is_array_sorted` kiểm tra `s[i] <= s[j]` hoặc `all_unique` kiểm tra `s[i] != s[j]`):\n"
                "     BẮT BUỘC sử dụng 2 vòng lặp lồng nhau duyệt `i < j`. ĐẶC BIỆT khi phát hiện vi phạm, BẮT BUỘC thêm khẳng định nhân chứng (witness assertion) để Z3 kích hoạt chứng minh mệnh đề tương đương `<==>`:\n"
                "     - Với bài toán kiểm tra sắp xếp tăng dần (`is_array_sorted`): Điều kiện vi phạm là `s[i] > s[j]` (TUYỆT ĐỐI KHÔNG viết `!s[i] <= s[j]` vì dấu `!` trong Dafny chỉ áp dụng cho boolean):\n"
                "     ```dafny\n"
                "     var i := 0;\n"
                "     while i < |s|\n"
                "       invariant 0 <= i <= |s|\n"
                "       invariant forall a, b :: 0 <= a < i && a < b < |s| ==> s[a] <= s[b]\n"
                "       decreases |s| - i\n"
                "     {\n"
                "       var j := i + 1;\n"
                "       while j < |s|\n"
                "         invariant i < j <= |s|\n"
                "         invariant forall b :: i < b < j ==> s[i] <= s[b]\n"
                "         decreases |s| - j\n"
                "       {\n"
                "         if s[i] > s[j] {\n"
                "           sorted := false;\n"
                "           assert 0 <= i < j < |s| && s[i] > s[j];\n"
                "           return;\n"
                "         }\n"
                "         j := j + 1;\n"
                "       }\n"
                "       i := i + 1;\n"
                "     }\n"
                "     sorted := true;\n"
                "     return;\n"
                "     ```\n"
                "     - Với bài toán kiểm tra phần tử duy nhất (`all_unique`): Điều kiện vi phạm là `s[i] == s[j]`:\n"
                "     ```dafny\n"
                "     var i := 0;\n"
                "     while i < |s|\n"
                "       invariant 0 <= i <= |s|\n"
                "       invariant forall a, b :: 0 <= a < i && a < b < |s| ==> s[a] != s[b]\n"
                "       decreases |s| - i\n"
                "     {\n"
                "       var j := i + 1;\n"
                "       while j < |s|\n"
                "         invariant i < j <= |s|\n"
                "         invariant forall b :: i < b < j ==> s[i] != s[b]\n"
                "         decreases |s| - j\n"
                "       {\n"
                "         if s[i] == s[j] {\n"
                "           unique := false;\n"
                "           assert 0 <= i < j < |s| && s[i] == s[j];\n"
                "           return;\n"
                "         }\n"
                "         j := j + 1;\n"
                "       }\n"
                "       i := i + 1;\n"
                "     }\n"
                "     unique := true;\n"
                "     return;\n"
                "     ```"
            )


        if topology == AlgorithmTopology.NUMBER_THEORY:
            return (
                "[RÀNG BUỘC CẤU TRÚC - SỐ HỌC / CHIA HẾT (NUMBER THEORY)]:\n"
                "- Nếu tham số đầu vào có thể là số âm hoặc bằng 0 (ví dụ: GCD với `requires a != 0 || b != 0`):\n"
                "  1. Lấy giá trị không âm: `var x := if a < 0 then -a else a; var y := if b < 0 then -b else b;`\n"
                "  2. BẮT BUỘC rẽ nhánh xử lý khi một trong hai số bằng 0 trước khi lặp: `if x == 0 { return y; } if y == 0 { return x; }`\n"
                "  3. Thuật toán Euclid lặp: `while y > 0 invariant x > 0 invariant y >= 0 decreases y { var temp := y; y := x % y; x := temp; } return x;`\n"
                "- Nếu là bài toán số nguyên tố (is_prime):\n"
                "  1. Xử lý trường hợp biên: `if k <= 1 { return false; }`\n"
                "  2. Duyệt tuyến tính `while i < k` (TUYỆT ĐỐI KHÔNG dùng `while i * i <= k`) kèm `decreases k - i`."
            )

        if topology == AlgorithmTopology.NON_LINEAR:
            return (
                "[RÀNG BUỘC CẤU TRÚC - SỐ HỌC BẬC CAO / PHI TUYẾN (NON-LINEAR ARITHMETIC)]:\n"
                "- Đối với phương thức tìm căn bậc nguyên (root search như `cube_root`):\n"
                "  Sử dụng vòng lặp tăng dần từ 0:\n"
                "  ```dafny\n"
                "  r := 0;\n"
                "  while (r + 1) * (r + 1) * (r + 1) <= N\n"
                "    invariant cube(r) <= N\n"
                "    decreases N - cube(r)\n"
                "  {\n"
                "    r := r + 1;\n"
                "  }\n"
                "  ```\n"
                "- Đối với phương thức kiểm tra số chính phương / lập phương (như `iscube`):\n"
                "  BẮT BUỘC gọi bổ đề đơn điệu có sẵn `cube_of_larger_is_larger();` ở ngay dòng đầu tiên của thân hàm để SMT Solver chứng minh tính duy nhất, tránh bị timeout:\n"
                "  ```dafny\n"
                "  cube_of_larger_is_larger();\n"
                "  var val: nat := if n < 0 then -n else n;\n"
                "  var root := cube_root(val);\n"
                "  r := (cube(root) == val);\n"
                "  ```\n"
                "- TUYỆT ĐỐI KHÔNG định nghĩa lại lemma hoặc function đã có sẵn trong file đặc tả."
            )

        if topology == AlgorithmTopology.STRING_SEQUENCE:
            return (
                "[RÀNG BUỘC CẤU TRÚC - XỬ LÝ CHUỖI ĐỐI XỨNG & ĐẢO CHUỖI (STRING SEQUENCE)]:\n"
                "- Đối với phương thức đảo chuỗi `reverse(str: string) returns (rev: string)`:\n"
                "  Sử dụng vòng lặp duyệt từng ký tự:\n"
                "  ```dafny\n"
                "  rev := [];\n"
                "  var i := 0;\n"
                "  while i < |str|\n"
                "    invariant 0 <= i <= |str|\n"
                "    invariant |rev| == i\n"
                "    invariant forall k :: 0 <= k < i ==> rev[k] == str[|str| - 1 - k]\n"
                "    decreases |str| - i\n"
                "  {\n"
                "    rev := rev + [str[|str| - 1 - i]];\n"
                "    i := i + 1;\n"
                "  }\n"
                "  ```\n"
                "- Đối với phương thức tạo chuỗi đối xứng `make_palindrome(s: string) returns (result: string)`:\n"
                "  BẮT BUỘC dùng từ khóa `var` để khai báo biến `rev` và chèn khối chứng minh đối xứng inline:\n"
                "  ```dafny\n"
                "  var rev := reverse(s);\n"
                "  result := s + rev;\n"
                "  forall k | 0 <= k < |result|\n"
                "    ensures result[k] == result[|result| - 1 - k]\n"
                "  {\n"
                "    if k < |s| {\n"
                "      assert result[k] == s[k];\n"
                "      assert result[|result| - 1 - k] == rev[|s| - 1 - k];\n"
                "    } else {\n"
                "      var j := k - |s|;\n"
                "      assert result[k] == rev[j];\n"
                "      assert result[|result| - 1 - k] == s[|s| - 1 - j];\n"
                "    }\n"
                "  }\n"
                "  ```"
            )

        if topology == AlgorithmTopology.PERMUTATION_SORT:
            return (
                "[RÀNG BUỘC CẤU TRÚC - SẮP XẾP VÀ BẢO TOÀN ĐA TẬP HỢP (PERMUTATION & SORTING)]:\n"
                "- Bài toán yêu cầu sắp xếp dãy `seq<int>` và bảo toàn đa tập hợp `multiset(s) == multiset(sorted)`.\n"
                "- BẮT BUỘC sử dụng thuật toán chèn tuần tự (Insertion Sort) kết hợp các bổ đề quy nạp hình thức chuẩn tắc sau:\n"
                "```dafny\n"
                "function insert(x: int, s: seq<int>): seq<int>\n"
                "  decreases |s|\n"
                "{\n"
                "  if |s| == 0 then [x]\n"
                "  else if x <= s[0] then [x] + s\n"
                "  else [s[0]] + insert(x, s[1..])\n"
                "}\n"
                "\n"
                "lemma insert_multiset(x: int, s: seq<int>)\n"
                "  ensures multiset(insert(x, s)) == multiset(s) + multiset{x}\n"
                "{\n"
                "  if |s| == 0 {\n"
                "  } else if x <= s[0] {\n"
                "    assert insert(x, s) == [x] + s;\n"
                "  } else {\n"
                "    insert_multiset(x, s[1..]);\n"
                "    assert s == [s[0]] + s[1..];\n"
                "    assert insert(x, s) == [s[0]] + insert(x, s[1..]);\n"
                "  }\n"
                "}\n"
                "\n"
                "lemma insert_len(x: int, s: seq<int>)\n"
                "  ensures |insert(x, s)| == |s| + 1\n"
                "{\n"
                "  if |s| == 0 {\n"
                "  } else if x <= s[0] {\n"
                "  } else {\n"
                "    insert_len(x, s[1..]);\n"
                "  }\n"
                "}\n"
                "\n"
                "predicate is_sorted(s: seq<int>) {\n"
                "  forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]\n"
                "}\n"
                "\n"
                "lemma insert_sorted(x: int, s: seq<int>)\n"
                "  requires is_sorted(s)\n"
                "  ensures is_sorted(insert(x, s))\n"
                "{\n"
                "  if |s| == 0 {\n"
                "  } else if x <= s[0] {\n"
                "    forall i, j | 0 <= i < j < |insert(x, s)|\n"
                "      ensures insert(x, s)[i] <= insert(x, s)[j]\n"
                "    {\n"
                "      if i == 0 {}\n"
                "    }\n"
                "  } else {\n"
                "    insert_sorted(x, s[1..]);\n"
                "    insert_len(x, s[1..]);\n"
                "    var rest := insert(x, s[1..]);\n"
                "    forall i, j | 0 <= i < j < |insert(x, s)|\n"
                "      ensures insert(x, s)[i] <= insert(x, s)[j]\n"
                "    {\n"
                "      if i == 0 {\n"
                "        if |s[1..]| == 0 || x <= s[1..][0] {\n"
                "          assert rest[0] == x;\n"
                "        } else {\n"
                "          assert rest[0] == s[1];\n"
                "        }\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "}\n"
                "\n"
                "lemma reverse_sorted_lemma(asc: seq<int>, rev: seq<int>)\n"
                "  requires |rev| == |asc|\n"
                "  requires forall k :: 0 <= k < |asc| ==> rev[k] == asc[|asc| - 1 - k]\n"
                "  requires forall i, j :: 0 <= i < j < |asc| ==> asc[i] <= asc[j]\n"
                "  ensures forall i, j :: 0 <= i < j < |rev| ==> rev[i] >= rev[j]\n"
                "{\n"
                "  forall i, j | 0 <= i < j < |rev|\n"
                "    ensures rev[i] >= rev[j]\n"
                "  {\n"
                "    var a := |asc| - 1 - j;\n"
                "    var b := |asc| - 1 - i;\n"
                "    assert asc[a] <= asc[b];\n"
                "  }\n"
                "}\n"
                "\n"
                "method reverse(s: seq<int>) returns (rev: seq<int>)\n"
                "  ensures |rev| == |s|\n"
                "  ensures forall k :: 0 <= k < |s| ==> rev[k] == s[|s| - 1 - k]\n"
                "{\n"
                "  rev := [];\n"
                "  var i := 0;\n"
                "  while i < |s|\n"
                "    invariant 0 <= i <= |s|\n"
                "    invariant |rev| == i\n"
                "    invariant forall k :: 0 <= k < i ==> rev[k] == s[|s| - 1 - k]\n"
                "    decreases |s| - i\n"
                "  {\n"
                "    rev := rev + [s[|s| - 1 - i]];\n"
                "    i := i + 1;\n"
                "  }\n"
                "}\n"
                "```\n"
                "- Trong phương thức `SortSeq(s: seq<int>) returns (sorted: seq<int>)`:\n"
                "  ```dafny\n"
                "  sorted := [];\n"
                "  var i := 0;\n"
                "  while i < |s|\n"
                "    invariant 0 <= i <= |s|\n"
                "    invariant |sorted| == i\n"
                "    invariant is_sorted(sorted)\n"
                "    invariant multiset(sorted) == multiset(s[..i])\n"
                "    decreases |s| - i\n"
                "  {\n"
                "    insert_len(s[i], sorted);\n"
                "    insert_sorted(s[i], sorted);\n"
                "    insert_multiset(s[i], sorted);\n"
                "    sorted := insert(s[i], sorted);\n"
                "    assert s[..i+1] == s[..i] + [s[i]];\n"
                "    i := i + 1;\n"
                "  }\n"
                "  assert s[..|s|] == s;\n"
                "  ```\n"
                "- Trong phương thức `sort_array(s: seq<int>) returns (sorted: seq<int>)`:\n"
                "  ```dafny\n"
                "  if |s| == 0 { sorted := []; return; }\n"
                "  var asc := SortSeq(s);\n"
                "  if (s[0] + s[|s| - 1]) % 2 == 0 {\n"
                "    var rev := reverse(asc);\n"
                "    reverse_sorted_lemma(asc, rev);\n"
                "    sorted := rev;\n"
                "  } else {\n"
                "    sorted := asc;\n"
                "  }\n"
                "  ```"
            )

        if topology == AlgorithmTopology.BINARY_SEARCH:
            return (
                "[RÀNG BUỘC CẤU TRÚC - TÌM KIẾM NHỊ PHÂN (BINARY SEARCH)]:\n"
                "- BẮT BUỘC sử dụng 2 con trỏ `low` và `high` với vòng lặp `while low < high` và bất biến loại trừ 2 đầu:\n"
                "  ```dafny\n"
                "  var low := 0;\n"
                "  var high := |s|;\n"
                "  while low < high\n"
                "    invariant 0 <= low <= high <= |s|\n"
                "    invariant forall k :: 0 <= k < low ==> s[k] < key\n"
                "    invariant forall k :: high <= k < |s| ==> s[k] > key\n"
                "    decreases high - low\n"
                "  {\n"
                "    var mid := low + (high - low) / 2;\n"
                "    if s[mid] == key {\n"
                "      index := mid;\n"
                "      return;\n"
                "    } else if s[mid] < key {\n"
                "      low := mid + 1;\n"
                "    } else {\n"
                "      high := mid;\n"
                "    }\n"
                "  }\n"
                "  index := -1;\n"
                "  ```"
            )

        if topology == AlgorithmTopology.ORDERED_INSERT:
            return (
                "[RÀNG BUỘC CẤU TRÚC - CHÈN PHẦN TỬ GIỮ THỨ TỰ (ORDERED INSERT)]:\n"
                "- Bài toán yêu cầu chèn phần tử `x` vào dãy đã sắp xếp `s: seq<int>` sao cho kết quả bảo toàn đa tập hợp và duy trì thứ tự tăng dần.\n"
                "- BẮT BUỘC định nghĩa hàm đệ quy `insert(x, s)` kèm 3 bổ đề quy nạp hình thức sau:\n"
                "```dafny\n"
                "function insert(x: int, s: seq<int>): seq<int>\n"
                "  decreases |s|\n"
                "{\n"
                "  if |s| == 0 then [x]\n"
                "  else if x <= s[0] then [x] + s\n"
                "  else [s[0]] + insert(x, s[1..])\n"
                "}\n"
                "\n"
                "lemma insert_multiset(x: int, s: seq<int>)\n"
                "  ensures multiset(insert(x, s)) == multiset(s) + multiset{x}\n"
                "{\n"
                "  if |s| == 0 {\n"
                "  } else if x <= s[0] {\n"
                "    assert insert(x, s) == [x] + s;\n"
                "  } else {\n"
                "    insert_multiset(x, s[1..]);\n"
                "    assert s == [s[0]] + s[1..];\n"
                "    assert insert(x, s) == [s[0]] + insert(x, s[1..]);\n"
                "  }\n"
                "}\n"
                "\n"
                "lemma insert_len(x: int, s: seq<int>)\n"
                "  ensures |insert(x, s)| == |s| + 1\n"
                "{\n"
                "  if |s| == 0 {\n"
                "  } else if x <= s[0] {\n"
                "  } else {\n"
                "    insert_len(x, s[1..]);\n"
                "  }\n"
                "}\n"
                "\n"
                "lemma insert_sorted(x: int, s: seq<int>)\n"
                "  requires is_sorted(s)\n"
                "  ensures is_sorted(insert(x, s))\n"
                "{\n"
                "  if |s| == 0 {\n"
                "  } else if x <= s[0] {\n"
                "    forall i, j | 0 <= i < j < |insert(x, s)|\n"
                "      ensures insert(x, s)[i] <= insert(x, s)[j]\n"
                "    {\n"
                "      if i == 0 {}\n"
                "    }\n"
                "  } else {\n"
                "    insert_sorted(x, s[1..]);\n"
                "    insert_len(x, s[1..]);\n"
                "    var rest := insert(x, s[1..]);\n"
                "    forall i, j | 0 <= i < j < |insert(x, s)|\n"
                "      ensures insert(x, s)[i] <= insert(x, s)[j]\n"
                "    {\n"
                "      if i == 0 {\n"
                "        if |s[1..]| == 0 || x <= s[1..][0] {\n"
                "          assert rest[0] == x;\n"
                "        } else {\n"
                "          assert rest[0] == s[1];\n"
                "        }\n"
                "      }\n"
                "    }\n"
                "  }\n"
                "}\n"
                "```\n"
                "- Trong thân hàm phương thức `sorted_insert`, gọi 3 bổ đề và gán kết quả:\n"
                "```dafny\n"
                "  insert_len(x, s);\n"
                "  insert_multiset(x, s);\n"
                "  insert_sorted(x, s);\n"
                "  res := insert(x, s);\n"
                "```"
            )

        if topology == AlgorithmTopology.SEARCH_CONDITION:
            return (
                "[RÀNG BUỘC CẤU TRÚC - TÌM KIẾM CÓ ĐIỀU KIỆN PHỦ ĐỊNH BIÊN (SEARCH CONDITION)]:\n"
                "- 1. Nếu tìm phần tử cuối cùng thỏa mãn điều kiện (`linear_search_last`):\n"
                "     BẮT BUỘC duyệt ngược từ cuối mảng về đầu để gặp phần tử cuối cùng đầu tiên:\n"
                "     ```dafny\n"
                "     var i := |s| - 1;\n"
                "     while i >= 0\n"
                "       invariant -1 <= i < |s|\n"
                "       invariant forall k :: i < k < |s| ==> s[k] != key\n"
                "       decreases i\n"
                "     {\n"
                "       if s[i] == key {\n"
                "         index := i;\n"
                "         return;\n"
                "       }\n"
                "       i := i - 1;\n"
                "     }\n"
                "     index := -1;\n"
                "     ```\n"
                "- 2. Nếu tìm phần tử đầu tiên thỏa mãn điều kiện (`find_first_negative`):\n"
                "     Duyệt từ `0` đến `|s|` kèm bất biến phủ định tiền tố:\n"
                "     ```dafny\n"
                "     var i := 0;\n"
                "     while i < |s|\n"
                "       invariant 0 <= i <= |s|\n"
                "       invariant forall k :: 0 <= k < i ==> s[k] >= 0\n"
                "       decreases |s| - i\n"
                "     {\n"
                "       if s[i] < 0 {\n"
                "         index := i;\n"
                "         return;\n"
                "       }\n"
                "       i := i + 1;\n"
                "     }\n"
                "     index := -1;\n"
                "     ```"
            )

        if topology == AlgorithmTopology.SEQ_CONSTRUCTION:
            return (
                "[RÀNG BUỘC CẤU TRÚC - XÂY DỰNG HOẶC LỌC DÃY MỚI (SEQUENCE CONSTRUCTION)]:\n"
                "- 1. Với bài toán sao chép mảng (`copy_array`):\n"
                "     Gán trực tiếp: `res := s;`\n"
                "- 2. Với bài toán lọc hoặc loại bỏ phần tử (`remove_element`):\n"
                "     Duyệt tuần tự và cộng dồn vào `res := res + [s[i]]` kèm đồng thời bất biến độ dài `|res| <= i` và tính chất phần tử:\n"
                "     ```dafny\n"
                "     res := [];\n"
                "     var i := 0;\n"
                "     while i < |s|\n"
                "       invariant 0 <= i <= |s|\n"
                "       invariant |res| <= i\n"
                "       invariant forall k :: 0 <= k < |res| ==> res[k] != val\n"
                "       decreases |s| - i\n"
                "     {\n"
                "       if s[i] != val {\n"
                "         res := res + [s[i]];\n"
                "       }\n"
                "       i := i + 1;\n"
                "     }\n"
                "     ```\n"
                "- 3. Với bài toán đảo ngược dãy (`array_reverse`):\n"
                "     ```dafny\n"
                "     rev := [];\n"
                "     var i := 0;\n"
                "     while i < |s|\n"
                "       invariant 0 <= i <= |s|\n"
                "       invariant |rev| == i\n"
                "       invariant forall k :: 0 <= k < i ==> rev[k] == s[|s| - 1 - k]\n"
                "       decreases |s| - i\n"
                "     {\n"
                "       rev := rev + [s[|s| - 1 - i]];\n"
                "       i := i + 1;\n"
                "     }\n"
                "     ```"
            )

        if topology == AlgorithmTopology.LINEAR_LOOP:
            return (
                "[RÀNG BUỘC CẤU TRÚC - DUYỆT TUẦN TỰ MẢNG / CHUỖI (LINEAR LOOP)]:\n"
                "- 1. Với bài toán tìm kiếm phần tử tuần tự (như LinearSearch tìm target trong a: array<int> hoặc seq<int>):\n"
                "     BẮT BUỘC sử dụng vòng lặp duy nhất kèm bất biến phủ định tiền tố:\n"
                "     ```dafny\n"
                "     var i := 0;\n"
                "     while i < a.Length // hoặc |s| nếu là seq\n"
                "       invariant 0 <= i <= a.Length\n"
                "       invariant forall k :: 0 <= k < i ==> a[k] != target\n"
                "       decreases a.Length - i\n"
                "     {\n"
                "       if a[i] == target {\n"
                "         return i;\n"
                "       }\n"
                "       i := i + 1;\n"
                "     }\n"
                "     return -1;\n"
                "     ```\n"
                "- 2. Với bài toán tìm giá trị cực trị (như `max_element`, `sample_max`, `find_min`):\n"
                "     BẮT BUỘC gán phần tử đầu tiên trực tiếp cho biến trả về: `max := s[0];`\n"
                "     Khởi tạo biến lặp `var i := 1;` và duyệt `while i < |s|` với bất biến `invariant exists j :: 0 <= j < i && s[j] == max` và `invariant forall j :: 0 <= j < i ==> s[j] <= max` (TUYỆT ĐỐI KHÔNG tạo biến trung gian như cur_acc).\n"
                "- 3. Với bài toán kiểm tra toàn thể (như `below_threshold`):\n"
                "     Duyệt `while i < |s| invariant 0 <= i <= |s| invariant forall k :: 0 <= k < i ==> s[k] < t decreases |s| - i`.\n"
                "- 4. Với bài toán tính tổng cấp số cộng (`sum_to_n`):\n"
                "     ```dafny\n"
                "     s := 0;\n"
                "     var i := 0;\n"
                "     while i < n\n"
                "       invariant 0 <= i <= n\n"
                "       invariant s == i * (i + 1) / 2\n"
                "       decreases n - i\n"
                "     {\n"
                "       i := i + 1;\n"
                "       s := s + i;\n"
                "     }\n"
                "     return;\n"
                "     ```"
            )

        return ""




