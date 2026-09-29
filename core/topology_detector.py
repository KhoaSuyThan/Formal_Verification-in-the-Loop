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

        # 3. Nhận diện Pure Function Equivalence (Hàm đệ quy được định nghĩa trong file và gọi trong ensures)
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
                "[RÀNG BUỘC CẤU TRÚC - TÌM KIẾM CẶP PHẦN TỬ (NESTED LOOP)]:\n"
                "- Cần 2 vòng lặp `while` lồng nhau: vòng ngoài biến `i`, vòng trong biến `j := i + 1`.\n"
                "- Cả 2 vòng lặp đều phải có invariant chặn biên và bất biến tiền tố."
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

        return ""
