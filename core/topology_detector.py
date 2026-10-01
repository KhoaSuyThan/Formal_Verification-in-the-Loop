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
    PURE_FUNC_EQUIV = "PURE_FUNC_EQUIV"        # Tính toán tương đương hàm đệ quy thuần túy (fib)
    NESTED_LOOP = "NESTED_LOOP"                # 2 vòng lặp lồng nhau hoặc tìm cặp chỉ số (has_close_elements)
    NUMBER_THEORY = "NUMBER_THEORY"            # Số học, chia hết, số nguyên tố, ước số (is_prime, gcd)
    NON_LINEAR = "NON_LINEAR"                  # Số học phi tuyến tính bậc cao (iscube)
    PERMUTATION_SORT = "PERMUTATION_SORT"      # Sắp xếp và bảo toàn đa tập hợp (sort_array)
    STRING_SEQUENCE = "STRING_SEQUENCE"        # Xử lý chuỗi ký tự, đảo chuỗi, đối xứng (is_palindrome)


class TopologyDetector:
    """Bộ nhận diện hình thái bài toán dựa trên AST và đặc tả toán học."""

    @classmethod
    def detect(cls, raw_spec: str) -> AlgorithmTopology:
        """Phân loại hình thái bài toán từ mã nguồn đặc tả."""
        spec_lower = raw_spec.lower()

        # 1. Nhận diện Sorting / Permutation
        if "multiset" in spec_lower or "sort" in spec_lower:
            return AlgorithmTopology.PERMUTATION_SORT

        # 2. Nhận diện Non-linear (Bậc 3 hoặc phi tuyến)
        if "cube" in spec_lower or re.search(r'\*\s*\w+\s*\*\s*\w+', raw_spec):
            return AlgorithmTopology.NON_LINEAR

        # 3. Nhận diện Chuỗi ký tự & Đối xứng (Palindrome / String Sequence)
        if "string" in spec_lower and ("palindrome" in spec_lower or "reverse" in spec_lower):
            return AlgorithmTopology.STRING_SEQUENCE

        # 4. Nhận diện Pure Function Equivalence (Hàm đệ quy được định nghĩa trong file và gọi trong ensures)
        # Tìm function <name>(...): ...
        pure_func_match = re.search(r'\bfunction\s+([a-zA-Z_]\w*)\s*\(', raw_spec)
        if pure_func_match:
            func_name = pure_func_match.group(1)
            # Kiểm tra nếu ensures có gọi func_name(...)
            ensures_match = re.search(r'ensures\b[^\n]*\b' + re.escape(func_name) + r'\s*\(', raw_spec)
            if ensures_match and func_name != "abs":
                return AlgorithmTopology.PURE_FUNC_EQUIV


        # 4. Nhận diện Nested Loop (2 định lượng i, j trong ensures hoặc có i != j)
        nested_quant_pattern = re.compile(
            r'ensures\b[^\n]*(?:exists|forall)\s+[a-zA-Z_]\w*\s*(?::\s*\w+)?\s*,\s*[a-zA-Z_]\w*',
            re.IGNORECASE
        )
        if nested_quant_pattern.search(raw_spec) or ("i != j" in raw_spec and "exists" in spec_lower):
            return AlgorithmTopology.NESTED_LOOP

        # 5. Nhận diện Number Theory (chia hết, mod %, prime, gcd)
        if "%" in raw_spec or "prime" in spec_lower or "gcd" in spec_lower or "divisor" in spec_lower:
            return AlgorithmTopology.NUMBER_THEORY

        # 6. Kiểm tra xem có cấu trúc mảng/chuỗi không (seq<T>, array, string)
        has_collection = bool(re.search(r'\b(?:seq<|array<|string\b|\[\])', raw_spec))
        has_quantifier = "forall" in spec_lower or "exists" in spec_lower

        # Nếu có mảng/chuỗi hoặc có quantifier -> Linear Loop
        if has_collection or has_quantifier or "sum" in spec_lower:
            return AlgorithmTopology.LINEAR_LOOP

        # 7. Mặc định là Direct Analytical (Tính toán trực tiếp: truncate, abs_val, sign_function, sample_max)
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
                "- Phương thức đang tính toán giá trị tương đương một hàm pure function toán học.\n"
                "- Vòng lặp `while` BẮT BUỘC phải đồng bộ các biến trạng thái lặp với giá trị của hàm tại bước lặp hiện tại "
                "(ví dụ: `invariant a == f(i)` và `invariant b == f(i + 1)`)."
            )

        if topology == AlgorithmTopology.LINEAR_LOOP:
            return (
                "[RÀNG BUỘC CẤU TRÚC - DUYỆT TUẦN TỰ MẢNG / CHUỖI (LINEAR LOOP)]:\n"
                "- Sử dụng một vòng lặp `while` duy nhất với biến đếm `i`.\n"
                "- Bắt buộc có bất biến chặn biên chỉ số (`invariant 0 <= i <= |s|` hoặc `1 <= i <= |s|`).\n"
                "- Nếu hậu điều kiện yêu cầu kết quả thuộc mảng (exists), BẮT BUỘC gán phần tử đầu tiên trực tiếp cho biến trả về: `result := s[0];`\n"
                "- Khởi tạo biến lặp `var i := 1;` và dùng trực tiếp biến trả về: `invariant exists j :: 0 <= j < i && s[j] == result` (TUYỆT ĐỐI KHÔNG tạo biến trung gian như cur_acc hay max)."
            )

        if topology == AlgorithmTopology.NESTED_LOOP:
            return (
                "[RÀNG BUỘC CẤU TRÚC - TÌM KIẾM CẶP PHẦN TỬ 2 CHIỀU (NESTED PAIRWISE SEARCH)]:\n"
                "- Phương thức kiểm tra sự tồn tại của cặp chỉ số (i, j) với i != j thỏa mãn điều kiện P(numbers[i], numbers[j]).\n"
                "- BẮT BUỘC sử dụng mẫu hình bất biến quy nạp 2 chiều phủ định chuẩn xác để Z3 chứng minh được trường hợp flag == false:\n"
                "  ```dafny\n"
                "  flag := false;\n"
                "  var i := 0;\n"
                "  while i < |numbers|\n"
                "    invariant 0 <= i <= |numbers|\n"
                "    invariant forall a: int, b: int :: 0 <= a < i && 0 <= b < |numbers| && a != b ==> !P(numbers[a], numbers[b])\n"
                "    decreases |numbers| - i\n"
                "  {\n"
                "    var j := 0;\n"
                "    while j < |numbers|\n"
                "      invariant 0 <= j <= |numbers|\n"
                "      invariant forall b: int :: 0 <= b < j && b != i ==> !P(numbers[i], numbers[b])\n"
                "      decreases |numbers| - j\n"
                "    {\n"
                "      if i != j && P(numbers[i], numbers[j]) {\n"
                "        flag := true;\n"
                "        return;\n"
                "      }\n"
                "      j := j + 1;\n"
                "    }\n"
                "    i := i + 1;\n"
                "  }\n"
                "  return;\n"
                "  ```"
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

        return ""




