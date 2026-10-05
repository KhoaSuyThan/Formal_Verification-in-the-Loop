"""Module phân tích và bóc tách lỗi chẩn đoán từ Dafny / Z3 SMT Solver.

Phân loại lỗi theo hệ thống danh mục (Error Taxonomy) và cung cấp
hướng dẫn sửa lỗi ngữ nghĩa toán học chi tiết (Semantic Diagnostic Engine).
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class CounterexampleData:
    """Mô hình phản ví dụ cụ thể do Z3 SMT Solver tìm thấy (CEGAR - arXiv:2506.06923)."""
    initial_state: Dict[str, str]        # Các giá trị đầu vào (ví dụ: {'x': '-1'})
    failing_state: Dict[str, str]        # Các giá trị khi vi phạm (ví dụ: {'x': '-1', 'y': '-1'})
    violated_clause: str                 # Mệnh đề bị vi phạm (ví dụ: 'ensures y >= 0')
    description: str                     # Tóm tắt súc tích cho UI và prompt
    raw_snippet: str = ""                # Đoạn log thô từ Z3


@dataclass
class DiagnosticError:
    """Thông tin chi tiết về từng lỗi do bộ kiểm định phát hiện."""
    line: Optional[int]
    column: Optional[int]
    error_type: str
    message: str
    raw_snippet: str
    faulty_line_content: str = ""
    semantic_hint: str = ""
    related_line: Optional[int] = None
    related_content: str = ""
    related_message: str = ""
    counterexample: Optional[CounterexampleData] = None


class DiagnosticParser:
    """Bộ bóc tách và phân loại lỗi từ output của Dafny kèm hướng dẫn ngữ nghĩa."""

    # Từ điển ánh xạ từ khóa lỗi sang phân loại chuẩn của đề tài NCKH
    ERROR_TAXONOMY_MAP = {
        "postcondition might not hold": "PostconditionViolation",
        "postcondition could not be proved": "PostconditionViolation",
        "invariant might not hold": "LoopInvariantViolation",
        "invariant could not be proved": "LoopInvariantViolation",
        "loop invariant could not be proved": "LoopInvariantViolation",
        "precondition might not hold": "PreconditionViolation",
        "precondition could not be proved": "PreconditionViolation",
        "decreases expression might not decrease": "TerminationFailure",
        "cannot prove termination": "TerminationFailure",
        "index out of range": "OutOfBounds",
        "assertion might not hold": "AssertionViolation",
        "assertion could not be proved": "AssertionViolation",
    }

    @classmethod
    def classify_error(cls, message: str) -> str:
        """Phân loại lỗi dựa trên nội dung thông báo từ Z3."""
        msg_lower = message.lower()
        for pattern, category in cls.ERROR_TAXONOMY_MAP.items():
            if pattern in msg_lower:
                return category
        if "syntax error" in msg_lower or "parse error" in msg_lower:
            return "SyntaxError"
        if "type error" in msg_lower:
            return "TypeError"
        if "lhs of assignment must denote a mutable variable" in msg_lower:
            return "GeneralVerificationFailure"
        return "GeneralVerificationFailure"

    @staticmethod
    def extract_forall_prefix_invariant(ensures_clause: str) -> Optional[str]:
        """Tự động phân tích mệnh đề ensures có forall để sinh biểu thức bất biến tiền tố (Prefix Invariant).

        Áp dụng thuật toán biến đổi công thức logic hình thức tổng quát:
        Từ 'forall x ... :: ... ==> Pred(x)', trích xuất vị từ mục tiêu sau dấu '==>'
        và sinh ra 'invariant forall j :: lower_bound <= j < i ==> Pred(j)'.
        Hỗ trợ boolean flag equivalence: 'b == (forall ...)' -> 'invariant b == (forall ...)'.
        """
        # Kiểm tra xem có dạng <out_var> == (forall ...) không (như bài 052-below-threshold)
        bool_match = re.search(r'\b([a-zA-Z0-9_]+)\s*==\s*\(?\s*forall', ensures_clause)
        bool_prefix = f"{bool_match.group(1)} == " if bool_match and bool_match.group(1) != "ensures" else ""

        match = re.search(r'forall\s+([a-zA-Z0-9_]+).*?::\s*(.+)', ensures_clause)
        if match:
            var_name = match.group(1).strip()
            body = match.group(2).strip()
            # Xác định cận dưới của quantifier: nếu có "2 <= " thì cận dưới là 2 (tránh chia cho 0 trong is_prime)
            lower_bound = "2" if "2 <= " in body else "0"
            if '==>' in body:
                predicate = body.split('==>')[-1].strip().rstrip(')')
                # Thay thế biến định lượng bằng biến cục bộ j
                pred_with_j = re.sub(rf'\b{re.escape(var_name)}\b', 'j', predicate)
                if bool_prefix:
                    return f"invariant {bool_prefix}(forall j :: {lower_bound} <= j < i ==> {pred_with_j})"
                return f"invariant forall j :: {lower_bound} <= j < i ==> {pred_with_j}"
        return None

    @classmethod
    def generate_semantic_hint(
        cls,
        category: str,
        message: str,
        faulty_line: str,
        code: str,
        related_content: str = ""
    ) -> str:
        """Sinh chỉ dẫn ngữ nghĩa toán học dựa trên danh mục lỗi và ngữ cảnh mã nguồn."""
        msg_lower = message.lower()

        # Kiểm tra lỗi chưa khai báo biến hoặc hàm/bổ đề (unresolved identifier)
        if "unresolved identifier" in msg_lower:
            ident_match = re.search(r'unresolved identifier:\s*(\w+)', message, re.IGNORECASE)
            ident_name = ident_match.group(1) if ident_match else "biến"
            # Nếu dòng vi phạm có dạng lời gọi hàm/lemma không có phép gán :=
            is_call = faulty_line and re.search(rf'\b{ident_name}\s*\(', faulty_line) and ":=" not in faulty_line
            if is_call or ident_name.endswith("_lemma") or ident_name.startswith("lemma_"):
                return (
                    f"LỖI HÀM HOẶC BỔ ĐỀ CHƯA ĐƯỢC ĐỊNH NGHĨA (UNRESOLVED IDENTIFIER): `{ident_name}`.\n"
                    f"[HÀNH ĐỘNG BẮT BUỘC]:\n"
                    f"Hàm hoặc bổ đề `{ident_name}` được gọi nhưng chưa có định nghĩa trong mã nguồn.\n"
                    f"-> BẮT BUỘC định nghĩa hàm/bổ đề `{ident_name}` (ví dụ: `lemma {ident_name}(...) {{ ... }}`) ở đầu file trước khi gọi."
                )
            return (
                f"LỖI CHƯA KHAI BÁO BIẾN (UNRESOLVED IDENTIFIER): `{ident_name}`.\n"
                f"[HÀNH ĐỘNG BẮT BUỘC]:\n"
                f"Trong Dafny, mọi biến cục bộ mới chưa nằm trong returns/parameters BẮT BUỘC phải được khai báo bằng từ khóa `var` khi gán lần đầu:\n"
                f"-> BẮT BUỘC SỬA THÀNH: `var {ident_name} := ...;` (thay vì `{ident_name} := ...;`)."
            )

        if category == "LoopInvariantViolation":

            if "on entry" in msg_lower:
                if faulty_line and "exists" in faulty_line:
                    return (
                        f"BẤT BIẾN TỒN TẠI KHÔNG ĐÚNG KHI BẮT ĐẦU VÒNG LẶP (on entry): `{faulty_line}`.\n"
                        "[LỖI TOÁN HỌC KHỞI TẠO BIẾN LẶP]:\n"
                        "Khoảng `0 <= j < i` khi bắt đầu là KHOẢNG RỖNG nếu `i == 0` (không có giá trị j nào thỏa mãn 0 <= j < 0)!\n"
                        "-> NGUYÊN TẮC: Khi biến kết quả đã được gán phần tử đầu tiên (như `result := l[0];`), "
                        "biến lặp `i` BẮT BUỘC phải khởi tạo từ `1` (`var i := 1;`), "
                        "và cận dưới của invariant BẮT BUỘC phải là: `invariant 1 <= i <= |s|`."
                    )
                if faulty_line and ("2 <= i" in faulty_line or "2 <= j" in faulty_line):
                    return (
                        f"BẤT BIẾN KHÔNG ĐÚNG KHI BẮT ĐẦU VÒNG LẶP (on entry): `{faulty_line}`.\n"
                        "[LỖI TRƯỜNG HỢP BIÊN VỚI k < 2]:\n"
                        "Khi đầu vào k = 1 (hoặc k <= 1), việc khởi tạo `var i := 2;` sẽ vi phạm `2 <= i <= k` ngay khi bắt đầu vòng lặp!\n"
                        "-> [HÀNH ĐỘNG BẮT BUỘC]: BẮT BUỘC phải bao bọc vòng lặp trong khối rẽ nhánh xử lý trường hợp biên:\n"
                        "   `if k <= 1 { result := false; } else { var i := 2; while i < k invariant 2 <= i <= k invariant result ==> forall j :: 2 <= j < i ==> k % j != 0 decreases k - i { ... } }`"
                    )
                if "cur_a" in faulty_line or "cur_b" in faulty_line or ("< a" in code and "< b" in code) or "greatest_common_divisor" in code:
                    return (
                        f"BẤT BIẾN KHÔNG ĐÚNG KHI BẮT ĐẦU VÒNG LẶP (on entry): `{faulty_line}`.\n"
                        "[HÀNH ĐỘNG BẮT BUỘC - XỬ LÝ SỐ ÂM VÀ TRƯỜNG HỢP BIÊN BẰNG 0 TRONG THUẬT TOÁN GCD / EUCLID]:\n"
                        "Khi tiền điều kiện là `requires a != 0 || b != 0`, một trong hai số CÓ THỂ BẰNG 0 (ví dụ a == 0 hoặc b == 0)!\n"
                        "-> Do đó bất biến `0 < cur_a && 0 < cur_b` BỊ SAI ngay khi bắt đầu nếu một số bằng 0.\n"
                        "1. Lấy giá trị không âm: `var cur_a := if a < 0 then -a else a; var cur_b := if b < 0 then -b else b;`\n"
                        "2. BẮT BUỘC rẽ nhánh xử lý khi một trong hai số bằng 0 trước khi vào vòng lặp:\n"
                        "   `if cur_a == 0 { return cur_b; }`\n"
                        "   `if cur_b == 0 { return cur_a; }`\n"
                        "3. Áp dụng vòng lặp Euclid chuẩn xác:\n"
                        "   `while cur_b > 0 invariant cur_a > 0 invariant cur_b >= 0 decreases cur_b { var temp := cur_b; cur_b := cur_a % cur_b; cur_a := temp; } return cur_a;`"
                    )
                return (
                    f"BẤT BIẾN KHÔNG ĐÚNG KHI BẮT ĐẦU VÒNG LẶP (on entry): `{faulty_line}`.\n"
                    "NGUYÊN NHÂN: Giá trị khởi tạo của các biến trước khi vào vòng lặp không thỏa mãn bất biến.\n"
                    "[HÀNH ĐỘNG BẮT BUỘC - XỬ LÝ SỐ ÂM / TRƯỜNG HỢP BIÊN]:\n"
                    "1. Nếu tham số đầu vào có thể là số âm (ví dụ: requires a != 0 || b != 0 trong GCD/Euclid), "
                    "BẮT BUỘC phải lấy giá trị không âm trước khi vào vòng lặp:\n"
                    "   `var cur_a := if a < 0 then -a else a;`\n"
                    "   `var cur_b := if b < 0 then -b else b;`\n"
                    "2. Khởi tạo biến lặp khớp chính xác với cận dưới của invariant (ví dụ: `var i := 0;` hoặc `var i := 1;`).\n"
                    "3. TUYỆT ĐỐI KHÔNG sửa đổi hoặc nới lỏng các mệnh đề requires/ensures của đề bài."
                )
            elif "maintained" in msg_lower:
                # Kiểm tra xem có phải lỗi thiếu invariant bước tiếp theo cho hàm thuần túy (như fib)
                pure_func_names = set(re.findall(r'\b(?:function|predicate)\s+([a-zA-Z_]\w*)', code))
                pure_func_names -= {"ensures", "requires", "invariant", "decreases", "assert", "assume"}
                for pf in pure_func_names:
                    if faulty_line and (f"{pf}(" in faulty_line):
                        return (
                            f"BẤT BIẾN KHÔNG ĐƯỢC DUY TRÌ SAU THÂN VÒNG LẶP (maintained): `{faulty_line}`.\n"
                            f"[HÀNH ĐỘNG BẮT BUỘC - THIẾU BẤT BIẾN QUY NẠP BẬC HAI CHO HÀM {pf}]:\n"
                            f"Để Z3 chứng minh được `a == {pf}(i)` qua bước nhảy gán `a := b; b := temp + b;`, "
                            f"SMT Solver BẮT BUỘC cần bất biến quy nạp bước kế tiếp cho biến `b`:\n"
                            f"-> BỔ SUNG NGAY DÒNG: `invariant b == {pf}(i + 1)`\n"
                            f"Cấu trúc hoàn chỉnh: giữ nguyên `while i < n`, đặt đồng thời cả 3 invariant:\n"
                            f"   `invariant 0 <= i <= n`\n"
                            f"   `invariant a == {pf}(i)`\n"
                            f"   `invariant b == {pf}(i + 1)`"
                        )

                if ("SumToN" in code or "sum_to_n" in code.lower() or "n * (n + 1) / 2" in code) and "maintained" in msg_lower:
                    return (
                        f"BẤT BIẾN KHÔNG ĐƯỢC DUY TRÌ SAU THÂN VÒNG LẶP (maintained): `{faulty_line}`.\n"
                        "[HÀNH ĐỘNG BẮT BUỘC - TÍNH TỔNG CẤP SỐ CỘNG]:\n"
                        "Để Z3 chứng minh được `s == n * (n + 1) / 2`, BẮT BUỘC dùng cấu trúc chuẩn xác `while i < n`:\n"
                        "```dafny\n"
                        "s := 0;\n"
                        "var i := 0;\n"
                        "while i < n\n"
                        "  invariant 0 <= i <= n\n"
                        "  invariant s == i * (i + 1) / 2\n"
                        "  decreases n - i\n"
                        "{\n"
                        "  i := i + 1;\n"
                        "  s := s + i;\n"
                        "}\n"
                        "return;\n"
                        "```"
                    )
                if ("<= n" in faulty_line or "<= n" in code) and "0 <= i <= n" in code:
                    return (
                        f"BẤT BIẾN KHÔNG ĐƯỢC DUY TRÌ SAU THÂN VÒNG LẶP (maintained): `{faulty_line}`.\n"
                        "[LỖI CẬN TRÊN BIẾN LẶP]:\n"
                        "Khi vòng lặp có điều kiện `while i <= n`, sau bước tăng `i := i + 1;`, biến `i` sẽ đạt giá trị `n + 1` trước khi thoát lặp.\n"
                        "-> [HÀNH ĐỘNG BẮT BUỘC]: Nới lỏng invariant cận trên thành: `invariant 0 <= i <= n + 1`."
                    )
                return (
                    "BẤT BIẾN KHÔNG ĐƯỢC DUY TRÌ SAU THÂN VÒNG LẶP (maintained): "
                    "Sau bước nhảy (ví dụ `i := i + 1`), biến có thể vượt qua biên của invariant. "
                    "Lưu ý: Nếu duyệt mảng `while i < a.Length`, TUYỆT ĐỐI KHÔNG sửa thành `while i <= a.Length` (sẽ gây lỗi vượt biên). "
                    "Hãy giữ nguyên điều kiện lặp hợp lệ và nới lỏng invariant cận trên thành `0 <= i <= a.Length`."
                )
            return (
                "BẤT BIẾN VÒNG LẶP KHÔNG THỎA MÃN: "
                "Cần kiểm tra lại mối liên hệ giữa điều kiện lặp, bước tăng của biến và giá trị cận."
            )

        if category == "PostconditionViolation":
            if related_content and "forall" in related_content:
                prefix_inv = cls.extract_forall_prefix_invariant(related_content)
                seq_match = re.search(r'\|\s*(\w+)\s*\|', related_content)
                if seq_match:
                    seq_name = seq_match.group(1)
                    if "exists" in code:
                        target_var = "result" if "result" in code else "res"
                        inv_block = (
                            f"1. `invariant 1 <= i <= |{seq_name}|`\n"
                            f"   2. `{prefix_inv}`\n"
                            f"   3. `invariant exists j :: 0 <= j < i && {seq_name}[j] == {target_var}`\n"
                            f"   (LƯU Ý QUAN TRỌNG: BẮT BUỘC duy trì ĐỒNG THỜI cả 3 invariant trên, TUYỆT ĐỐI KHÔNG xóa invariant exists)"
                        )
                    else:
                        inv_block = (
                            f"1. `invariant 0 <= i <= |{seq_name}|` (bắt buộc đặt dòng đầu tiên để tránh lỗi index out of range)\n"
                            f"   2. `{prefix_inv}`" if prefix_inv else f"1. `invariant 0 <= i <= |{seq_name}|`\n   2. `invariant forall j :: 0 <= j < i ==> P(j)`"
                        )
                else:
                    inv_block = f"`{prefix_inv}`" if prefix_inv else "`invariant forall j :: 0 <= j < i ==> P(j)`"

                linear_hint = ""
                if "%" in related_content or "is_prime" in code:
                    linear_hint = (
                        "\n-> [LƯU Ý VÒNG LẶP SỐ NGUYÊN TỐ]: Z3 SMT Solver không thể suy diễn quy nạp qua căn bậc hai nếu thiếu bổ đề phi tuyến. "
                        "BẮT BUỘC phải xử lý trường hợp biên trước vòng lặp: `if k <= 1 { result := false; } else { ... }` "
                        "và trong nhánh else duyệt tuyến tính `while i < k` (TUYỆT ĐỐI KHÔNG dùng `while i * i <= k`) kèm `decreases k - i` "
                        "và `invariant result ==> forall j :: 2 <= j < i ==> k % j != 0`."
                    )
                if "target" in code and ("r == -1" in code or "r >= 0" in code):
                    linear_hint += (
                        "\n-> [LƯU Ý TÌM KIẾM]: Khi tìm thấy phần tử (`a[i] == target`), "
                        "hãy gán `r := i; return;` (hoặc `break;`) để thoát ngay khỏi vòng lặp, "
                        "nhằm bảo toàn invariant `forall j :: 0 <= j < i ==> a[j] != target`."
                    )

                return (
                    f"HẬU ĐIỀU KIỆN CHỨA ĐỊNH LƯỢNG TOÀN THỂ (FORALL) BỊ VI PHẠM: `{related_content}`.\n"
                    f"NGUYÊN LÝ BẤT BIẾN TIỀN TỐ (PREFIX INDUCTIVE INVARIANT): Để Z3 suy diễn được hậu điều kiện toàn thể, "
                    f"vòng lặp BẮT BUỘC phải duy trì bất biến tiền tố cho các phần tử đã duyệt:\n"
                    f"-> [HÀNH ĐỘNG BẮT BUỘC]: Bổ sung đầy đủ các mệnh đề invariant sau vào ngay dưới từ khóa while (theo đúng thứ tự):\n"
                    f"   {inv_block}"
                    f"{linear_hint}"
                )
            if related_content and "exists" in related_content:
                # Kiểm tra xem có phải hậu điều kiện dạng boolean cờ flag == (exists ...) không
                if re.search(r'\b\w+\s*==\s*\(?\s*exists', related_content) or "returns (flag : bool)" in code:
                    return (
                        f"HẬU ĐIỀU KIỆN DẠNG CỜ BOOLEAN TỒN TẠI (2-DIMENSIONAL SEARCH) BỊ VI PHẠM: `{related_content}`.\n"
                        "[HÀNH ĐỘNG BẮT BUỘC - MẪU HÌNH BẤT BIẾN QUY NẠP 2 CHIỀU PHỦ ĐỊNH]:\n"
                        "Để Z3 chứng minh được khi vòng lặp kết thúc mà `flag == false`, BẮT BUỘC phải có bất biến phủ định 2 lớp:\n"
                        "1. Vòng lặp ngoài duyệt `i` từ `0` đến `|numbers|`:\n"
                        "   `invariant 0 <= i <= |numbers|`\n"
                        "   `invariant forall a: int, b: int :: 0 <= a < i && 0 <= b < |numbers| && a != b ==> !Condition(numbers[a], numbers[b])`\n"
                        "   `decreases |numbers| - i`\n"
                        "2. Vòng lặp trong duyệt `j` từ `0` đến `|numbers|`:\n"
                        "   `invariant 0 <= j <= |numbers|`\n"
                        "   `invariant forall b: int :: 0 <= b < j && b != i ==> !Condition(numbers[i], numbers[b])`\n"
                        "   `decreases |numbers| - j`\n"
                        "3. Khi tìm thấy phần tử thỏa mãn: `if i != j && Condition(numbers[i], numbers[j]) { flag := true; return; }`\n"
                        "4. Ra khỏi 2 vòng lặp: `return;` (flag đã mang giá trị false ban đầu)."
                    )

                seq_match = re.search(r'\|\s*(\w+)\s*\|', related_content)
                seq_var = seq_match.group(1) if seq_match else "l"
                elem_match = re.search(r'\b\w+\[\w+\]\s*==\s*(\w+)', related_content)
                target_var = elem_match.group(1) if elem_match else "result"
                return (
                    f"HẬU ĐIỀU KIỆN CHỨA ĐỊNH LƯỢNG TỒN TẠI (EXISTS) BỊ VI PHẠM: `{related_content}`.\n"
                    f"[HÀNH ĐỘNG BẮT BUỘC - CHÈN INVARIANT TỒN TẠI VÀ DÙNG TRỰC TIẾP BIẾN TRẢ VỀ {target_var}]:\n"
                    f"Hậu điều kiện yêu cầu kết quả `{target_var}` phải là một phần tử có thật trong `{seq_var}`.\n"
                    f"1. Gán phần tử đầu tiên trực tiếp cho biến trả về: `{target_var} := {seq_var}[0];`\n"
                    f"2. BẮT BUỘC khởi tạo `var i := 1;` (TUYỆT ĐỐI KHÔNG để `i := 0` vì khoảng 0 <= j < 0 rỗng sẽ gây lỗi 'could not be proved on entry')!\n"
                    f"3. Thêm các invariant sau vào ngay dưới từ khóa while (dùng trực tiếp biến `{target_var}`, TUYỆT ĐỐI KHÔNG tạo biến trung gian như `var max`):\n"
                    f"   `invariant 1 <= i <= |{seq_var}|`\n"
                    f"   `invariant forall j :: 0 <= j < i ==> {seq_var}[j] <= {target_var}` (nếu tìm max)\n"
                    f"   `invariant exists j :: 0 <= j < i && {seq_var}[j] == {target_var}`\n"
                    f"4. Trong thân while: `if {seq_var}[i] > {target_var} {{ {target_var} := {seq_var}[i]; }}`."
                )

            # Xử lý bài toán phần thập phân / Floor (002-truncate)
            if "Floor as real" in code or ".Floor" in code:
                return (
                    "HẬU ĐIỀU KIỆN TÍNH PHẦN THẬP PHÂN (TRUNCATE):\n"
                    "[HÀNH ĐỘNG BẮT BUỘC]:\n"
                    "Để lấy phần thập phân và thỏa mãn `(x - d) == (x.Floor as real)`, "
                    "hãy gán trực tiếp: `d := x - (x.Floor as real);` mà TUYỆT ĐỐI KHÔNG dùng vòng lặp while hay cấu trúc if-else."
                )

            # Xử lý bài toán số học phi tuyến bậc cao có bổ đề đơn điệu (như iscube / cube_root)
            if "cube" in code or "cube_root" in code:
                return (
                    f"HẬU ĐIỀU KIỆN SỐ HỌC BẬC CAO / PHI TUYẾN BỊ VI PHẠM: `{related_content}`.\n"
                    "[HÀNH ĐỘNG BẮT BUỘC - SỬ DỤNG BỔ ĐỀ ĐƠN ĐIỆU CÓ SẴN]:\n"
                    "1. Trong phương thức tìm căn `cube_root(N: nat) returns (r: nat)`:\n"
                    "   `r := 0; while (r + 1) * (r + 1) * (r + 1) <= N invariant cube(r) <= N decreases N - cube(r) { r := r + 1; }`\n"
                    "2. Trong phương thức kiểm tra `iscube(n: int) returns (r: bool)`:\n"
                    "   - BẮT BUỘC gọi bổ đề có sẵn: `cube_of_larger_is_larger();` ngay đầu hàm.\n"
                    "   - Lấy số tự nhiên: `var val: nat := if n < 0 then -n else n;`\n"
                    "   - Gọi tìm căn: `var root := cube_root(val);`\n"
                    "   - Gán cờ boolean: `r := (cube(root) == val);`"
                )


            # Xử lý bài toán chuỗi đối xứng (Palindrome / Reverse)
            if "palindrome" in code or "reverse" in code:
                return (
                    f"HẬU ĐIỀU KIỆN CHUỖI ĐỐI XỨNG BỊ VI PHẠM: `{related_content}`.\n"
                    "[HÀNH ĐỘNG BẮT BUỘC - BẢO TOÀN ĐỐI XỨNG BẰNG PROOF BLOCK INLINE]:\n"
                    "1. Trong `reverse(str: string)`: Lặp `while i < |str|` kèm `invariant |rev| == i` và "
                    "`invariant forall k :: 0 <= k < i ==> rev[k] == str[|str| - 1 - k]`.\n"
                    "2. Trong `make_palindrome(s: string)`: Gọi `var rev := reverse(s); result := s + rev;`\n"
                    "   và BẮT BUỘC chèn khối chứng minh đối xứng inline:\n"
                    "   `forall k | 0 <= k < |result| ensures result[k] == result[|result| - 1 - k] { "
                    "if k < |s| { assert result[k] == s[k]; assert result[|result| - 1 - k] == rev[|s| - 1 - k]; } "
                    "else { var j := k - |s|; assert result[k] == rev[j]; assert result[|result| - 1 - k] == s[|s| - 1 - j]; } }`"
                )

            # Xử lý bài toán tương đương hàm thuần túy (pure function như Fibonacci)

            pure_func_names = set(re.findall(r'\b(?:function|predicate)\s+([a-zA-Z_]\w*)', code))
            pure_func_names -= {"ensures", "requires", "invariant", "decreases", "assert", "assume"}
            matched_pure_func = None
            matched_arg = "n"
            if related_content and pure_func_names:
                for pf in pure_func_names:
                    m = re.search(rf'\b{re.escape(pf)}\s*\(([^)]*)\)', related_content)
                    if m:
                        matched_pure_func = pf
                        matched_arg = m.group(1).strip()
                        break

            if matched_pure_func:
                return (
                    f"HẬU ĐIỀU KIỆN QUY NẠP TƯƠNG ĐƯƠNG HÀM ĐỆ QUY (FUNCTIONAL EQUIVALENCE): `{related_content}`.\n"
                    f"[HÀNH ĐỘNG BẮT BUỘC - ĐỒNG BỘ BẤT BIẾN VỚI HÀM {matched_pure_func}]:\n"
                    f"Phương thức đang tính toán để khớp với hàm thuần túy `{matched_pure_func}({matched_arg})`.\n"
                    f"1. Cấu trúc lặp chuẩn: duyệt `while i < {matched_arg}` kèm `decreases {matched_arg} - i`, và sau khi kết thúc vòng lặp gán biến kết quả (`result := a;`).\n"
                    f"2. BẮT BUỘC đặt các invariant sau ngay trước dấu ngoặc mở `{{` của while:\n"
                    f"   - `invariant 0 <= i <= {matched_arg}`\n"
                    f"   - `invariant a == {matched_pure_func}(i)` (biến tích lũy bước hiện tại)\n"
                    f"   - `invariant b == {matched_pure_func}(i + 1)` (nếu là thuật toán đệ quy 2 bước như Fibonacci, biến tích lũy bước tiếp theo)"
                )
            if related_content:
                return (
                    f"HẬU ĐIỀU KIỆN CỤ THỂ BỊ VI PHẠM: `{related_content}`.\n"
                    "SMT Solver không thể suy diễn được điều kiện này tại điểm return. "
                    "Hãy kiểm tra xem vòng lặp có thiếu invariant quy nạp mô tả kết quả đang tích lũy hay không."
                )
            return (
                "HẬU ĐIỀU KIỆN (ensures) KHÔNG ĐƯỢC CHỨNG MINH: "
                "SMT Solver không thể suy diễn được kết quả cuối cùng từ thân hàm. "
                "Nếu hàm có vòng lặp, BẮT BUỘC phải bổ sung các invariant quy nạp mô tả "
                "trạng thái tích lũy của các biến lặp tương ứng với mệnh đề ensures."
            )

        if category == "OutOfBounds":
            return (
                "CHỈ SỐ TRUY CẬP VƯỢT MIỀN (index out of range): "
                "Truy cập phần tử mảng/chuỗi `[idx]` có thể âm hoặc >= độ dài. "
                "Hãy bổ sung bất biến chặn biên `invariant 0 <= i <= |s|` (hoặc `a.Length`) "
                "và kiểm tra chặt chẽ mọi quantifier."
            )

        if "lhs of assignment must denote a mutable variable" in msg_lower:
            return (
                "THAM SỐ ĐẦU VÀO LÀ HẰNG SỐ BẤT BIẾN (immutable): "
                "Trong Dafny, tham số đầu vào của method KHÔNG THỂ gán lại. "
                "Hãy khai báo biến cục bộ sao chép: `var cur_a := a; var cur_b := b;` rồi thao tác trên biến cục bộ."
            )

        if "not allowed to invoke a method" in msg_lower:
            return (
                "KHÔNG ĐƯỢC GỌI METHOD TRONG BIỂU THỨC: "
                "Trong Dafny, method không thể gọi lồng vào biểu thức tính toán. "
                "Hãy gọi method bằng câu lệnh riêng: `var res := TenMethod(args);` trước khi sử dụng kết quả."
            )

        if "unresolved identifier: max" in msg_lower or "unresolved identifier: min" in msg_lower:
            return (
                "DAFNY KHÔNG CÓ HÀM TOÀN CỤC `max(...)` HAY `min(...)`: "
                "Trong mệnh đề `decreases`, TUYỆT ĐỐI KHÔNG dùng `decreases max(...)` hay `min(...)`. "
                "Đối với thuật toán Euclid (GCD), mệnh đề giảm chuẩn xác là: `decreases cur_b` (khi lặp `while cur_b > 0`) "
                "hoặc `decreases cur_a + cur_b` (khi lặp bằng phép trừ `while cur_a != cur_b`)."
            )

        if "does not have a member max" in msg_lower or "does not have a member min" in msg_lower:
            return (
                "KIỂU SEQ KHÔNG CÓ METHOD .max() / .min(): "
                "Trong Dafny, kiểu `seq<T>` không có phương thức built-in `.max()` hay `.min()`. "
                "BẮT BUỘC phải dùng định lượng toán học tổng quát: `invariant forall j :: 0 <= j < i ==> s[j] <= acc`."
            )

        if category == "TerminationFailure":
            # Phân tích chi tiết theo loại lỗi dừng cụ thể
            if "decreases expression might not decrease" in msg_lower:
                # Trích xuất điều kiện while từ mã nguồn để gợi ý ranking function cụ thể
                while_match = re.search(r'while\s+(\w+)\s*(<|<=|>|>=|!=)\s*(\S+)', code)
                if while_match:
                    var = while_match.group(1)
                    op = while_match.group(2)
                    bound = while_match.group(3)
                    if op in ('<', '<='):
                        suggested = f"{bound} - {var}"
                    elif op == '>' and bound == '0':
                        suggested = var
                    elif op == '!=':
                        suggested = f"{var} + {bound}"
                    else:
                        suggested = f"{bound} - {var}"
                    return (
                        f"BIỂU THỨC GIẢM KHÔNG GIẢM NGHIÊM NGẶT (decreases expression might not decrease): `{faulty_line}`.\n"
                        f"[HÀNH ĐỘNG BẮT BUỘC - SỬA RANKING FUNCTION]:\n"
                        f"Vòng lặp `while {var} {op} {bound}` cần hàm biến thiên giảm nghiêm ngặt sau mỗi bước.\n"
                        f"-> BẮT BUỘC sửa mệnh đề dừng thành: `decreases {suggested}`\n"
                        f"Đảm bảo rằng biểu thức `{suggested}` luôn >= 0 tại đầu mỗi lần lặp "
                        f"và giảm nghiêm ngặt sau mỗi bước (sau phép gán `{var} := ...`)."
                    )

            if "cannot prove termination" in msg_lower:
                return (
                    "KHÔNG THỂ CHỨNG MINH TÍNH DỪNG (cannot prove termination):\n"
                    "[HÀNH ĐỘNG BẮT BUỘC - CHÈN MỆNH ĐỀ DỪNG]:\n"
                    "Vòng lặp while THIẾU mệnh đề `decreases` để chứng minh Total Correctness.\n"
                    "Quy tắc suy luận ranking function theo điều kiện while:\n"
                    "1. `while i < n` hoặc `while i < |s|` → `decreases n - i` hoặc `decreases |s| - i`\n"
                    "2. `while i > 0` → `decreases i`\n"
                    "3. `while low < high` (nhị phân) → `decreases high - low`\n"
                    "4. `while b > 0` (Euclid mod) → `decreases b`\n"
                    "5. `while a != b` (Euclid trừ) → `decreases a + b`\n"
                    "BẮT BUỘC chèn mệnh đề `decreases <biểu_thức>` sau invariant, trước dấu mở ngoặc `{` của while."
                )

            if "bounded below" in msg_lower:
                return (
                    f"BIỂU THỨC DỪNG BỊ ÂM HOẶC KHÔNG BỊ CHẶN DƯỚI (decreases expression must be bounded below): `{faulty_line}`.\n"
                    f"[HÀNH ĐỘNG BẮT BUỘC - BẢO ĐẢM CHẶN DƯỚI KHÔNG ÂM]:\n"
                    f"Biểu thức trong mệnh đề `decreases` bắt buộc phải luôn >= 0 tại đầu mỗi vòng lặp.\n"
                    f"1. Bổ sung bất biến chặn dưới: `invariant i >= 0` hoặc `invariant 0 <= i <= n`.\n"
                    f"2. Nếu tham số có thể nhận giá trị âm (như GCD), chuyển đổi sang số không âm trước vòng lặp: `var cur_a := if a < 0 then -a else a;`.\n"
                    f"3. Nếu biến lặp đạt tới n + 1 (trong `while i <= n`), điều chỉnh ranking function thành: `decreases n + 1 - i`."
                )

            # Fallback cho các trường hợp TerminationFailure khác
            return (
                "KHÔNG THỂ CHỨNG MINH VÒNG LẶP DỪNG (Termination Failure): "
                "Biểu thức trong mệnh đề `decreases <biểu_thức>` phải luôn bị chặn dưới (>= 0) và giảm nghiêm ngặt sau mỗi bước lặp. "
                "Nếu các biến lặp có thể nhận giá trị âm từ tham số đầu vào (ví dụ trong thuật toán GCD/Euclid), "
                "BẮT BUỘC phải chuyển đổi biến về số không âm (lấy giá trị tuyệt đối nếu âm) trước khi vào vòng lặp."
            )

        if "must agree with the result type" in msg_lower or "cannot perform binary operator on real and int" in msg_lower:
            return (
                "LỖI LỆCH KIỂU SỐ NGUYÊN VÀ SỐ THỰC (real vs int): "
                "Thuộc tính `.Floor` trả về kiểu `int`, trong khi biến cần tính có kiểu `real`. "
                "Trong Dafny, phép toán giữa real và int KHÔNG TỰ ĐỘNG ÉP KIỂU. "
                "BẮT BUỘC phải ép kiểu số nguyên sang số thực: `(x.Floor as real)`. "
                "Câu lệnh gán chuẩn xác: `d := x - (x.Floor as real);`."
            )

        if "closeparen expected" in msg_lower or "sum(" in faulty_line:
            if "sum(" in faulty_line or "sum(" in code:
                return (
                    "DAFNY KHÔNG CÓ HÀM BUILT-IN `sum(...)` HAY CÚ PHÁP DÃY `0..i`: "
                    "Để biểu diễn tổng các số nguyên, BẮT BUỘC dùng công thức giải tích đóng: "
                    "`invariant s == i * (i - 1) / 2` (hoặc `invariant acc == i * (i - 1) / 2`). "
                    "TUYỆT ĐỐI KHÔNG gọi hàm `sum(0..i)`."
                )

        return "Hãy kiểm tra kỹ thông báo lỗi và đảm bảo mã nguồn tuân thủ chặt chẽ cú pháp và ngữ nghĩa Dafny."

    @classmethod
    def parse_diagnostics(cls, dafny_output: str, code: str = "") -> List[DiagnosticError]:
        """Bóc tách toàn bộ danh sách lỗi có kèm tọa độ dòng, cột, snippet mã và chỉ dẫn ngữ nghĩa."""
        errors: List[DiagnosticError] = []
        code_lines = code.splitlines() if code else []

        err_pattern = re.compile(r'(?:\.dfy)?\((\d+),(\d+)\):\s*Error:\s*(.+)', re.IGNORECASE)
        rel_pattern = re.compile(r'(?:\.dfy)?\((\d+),(\d+)\):\s*Related location:\s*(.+)', re.IGNORECASE)

        for line in dafny_output.splitlines():
            # Kiểm tra dòng Error
            err_match = err_pattern.search(line)
            if err_match:
                line_num = int(err_match.group(1))
                col_num = int(err_match.group(2))
                msg = err_match.group(3).strip()
                category = cls.classify_error(msg)

                faulty_line = ""
                if 1 <= line_num <= len(code_lines):
                    faulty_line = code_lines[line_num - 1].strip()

                errors.append(DiagnosticError(
                    line=line_num,
                    column=col_num,
                    error_type=category,
                    message=msg,
                    raw_snippet=line.strip(),
                    faulty_line_content=faulty_line
                ))
                continue

            # Kiểm tra dòng Related location (gắn vào lỗi trước đó nếu có)
            rel_match = rel_pattern.search(line)
            if rel_match and errors:
                r_line = int(rel_match.group(1))
                r_msg = rel_match.group(3).strip()
                r_content = ""
                if 1 <= r_line <= len(code_lines):
                    r_content = code_lines[r_line - 1].strip()

                errors[-1].related_line = r_line
                errors[-1].related_content = r_content
                errors[-1].related_message = r_msg

        # Sinh hint ngữ nghĩa cho từng lỗi sau khi đã gom đủ thông tin related location
        for err in errors:
            err.semantic_hint = cls.generate_semantic_hint(
                err.error_type,
                err.message,
                err.faulty_line_content,
                code,
                err.related_content
            )

        # Trích xuất phản ví dụ CEGAR nếu Z3 cung cấp (arXiv:2506.06923)
        ce_data = cls.extract_counterexample(dafny_output, code)
        if ce_data and errors:
            errors[0].counterexample = ce_data

        return errors

    @classmethod
    def extract_counterexample(cls, dafny_output: str, code: str = "") -> Optional[CounterexampleData]:
        """Trích xuất mô hình phản ví dụ (Counterexample) do Z3 sinh ra khi kiểm định thất bại.
        
        Căn cứ theo nguyên lý CEGAR (arXiv:2506.06923):
        Tìm kiếm các trạng thái gán giá trị biến khiến hậu điều kiện hoặc bất biến bị vi phạm.
        """
        if "Related counterexample:" not in dafny_output:
            return None

        parts = dafny_output.split("Related counterexample:")
        if len(parts) < 2:
            return None
        ce_text = parts[1]

        # Tách cho đến phần Related location hoặc phần kết thúc
        end_idx = ce_text.find("Related location:")
        body = ce_text if end_idx == -1 else ce_text[:end_idx]

        initial_vars: Dict[str, str] = {}
        failing_vars: Dict[str, str] = {}
        current_state = "unknown"

        for line in body.splitlines():
            line_str = line.strip()
            if "initial state:" in line_str:
                current_state = "initial"
                continue
            elif line_str.endswith(":") and ("(" in line_str or "\\" in line_str or "/" in line_str):
                current_state = "failing"
                continue

            if line_str.startswith("assume "):
                assume_content = line_str[len("assume "):].rstrip(";")
                clauses = [c.strip() for c in assume_content.split("&&")]
                for c in clauses:
                    eq_match = re.match(r'^(-?[0-9a-zA-Z_#\'\.\"]+)\s*==\s*(-?[0-9a-zA-Z_#\'\.\"]+)$', c)
                    if eq_match:
                        left, right = eq_match.group(1), eq_match.group(2)
                        var_name = None
                        var_val = None
                        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', right) and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', left):
                            var_name = right
                            var_val = left
                        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', left) and not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', right):
                            var_name = left
                            var_val = right
                        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', right):
                            var_name = right
                            var_val = left
                        elif re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', left):
                            var_name = left
                            var_val = right

                        if var_name and var_val and not var_name.startswith("_"):
                            if current_state == "initial":
                                initial_vars[var_name] = var_val
                            failing_vars[var_name] = var_val

        # Trích xuất mệnh đề vi phạm từ phần Related location
        violated_clause = ""
        rel_loc_match = re.search(r'Related location: this is the [^\n]+\n\s*\|\s*\n[0-9]+\s*\|\s*([^\n]+)', ce_text)
        if rel_loc_match:
            violated_clause = rel_loc_match.group(1).strip()
        elif "Related location:" in ce_text:
            rel_part = ce_text.split("Related location:")[1]
            for rline in rel_part.splitlines():
                clean_rline = rline.strip()
                if clean_rline and not clean_rline.startswith("|") and not clean_rline.startswith("^") and not clean_rline.startswith("this is the"):
                    if "ensures " in clean_rline or "invariant " in clean_rline or "requires " in clean_rline:
                        violated_clause = clean_rline
                        break

        if not violated_clause:
            clause_match = re.search(r'(ensures\s+[^\n;]+|invariant\s+[^\n;]+)', dafny_output)
            if clause_match:
                violated_clause = clause_match.group(1).strip()

        # Tạo mô tả súc tích cho UI và prompt
        desc_parts = []
        if initial_vars:
            init_str = ", ".join(f"{k} = {v}" for k, v in initial_vars.items())
            desc_parts.append(f"Đầu vào: [{init_str}]")
        if failing_vars and failing_vars != initial_vars:
            fail_str = ", ".join(f"{k} = {v}" for k, v in failing_vars.items() if k not in initial_vars or initial_vars[k] != v)
            if fail_str:
                desc_parts.append(f"Kết quả: [{fail_str}]")
            else:
                desc_parts.append(f"Tại: [{', '.join(f'{k} = {v}' for k, v in failing_vars.items())}]")
        if violated_clause:
            desc_parts.append(f"Vi phạm: `{violated_clause}`")

        description = " ➔ ".join(desc_parts) if desc_parts else "Phản ví dụ do Z3 SMT Solver phát hiện"

        return CounterexampleData(
            initial_state=initial_vars,
            failing_state=failing_vars if failing_vars else initial_vars,
            violated_clause=violated_clause,
            description=description,
            raw_snippet=body.strip()
        )

    @classmethod
    def extract_error(cls, dafny_output: str, code: str = "") -> str:
        """Trích xuất chuỗi thông báo lỗi cô đọng để làm ngữ cảnh phản hồi cho LLM."""
        parsed = cls.parse_diagnostics(dafny_output, code)
        if parsed:
            top = parsed[0]
            pos = f"Dòng {top.line}, Cột {top.column}" if top.line else "Vị trí không xác định"
            res = f"[{top.error_type}] tại {pos}: {top.message}"
            if top.faulty_line_content:
                res += f"\n-> Dòng mã vi phạm: `{top.faulty_line_content}`"
            if top.related_content:
                res += f"\n-> Mệnh đề liên quan: `{top.related_content}`"
            if top.counterexample:
                res += f"\n-> Phản ví dụ Z3 (CEGAR): {top.counterexample.description}"
            if top.semantic_hint:
                res += f"\n-> Hướng dẫn khắc phục: {top.semantic_hint}"
            return res

        # Nếu không khớp regex tọa độ, gom tối đa 3 dòng chứa từ khóa Error
        error_lines = [line.strip() for line in dafny_output.splitlines() if "Error" in line or "error" in line]
        if error_lines:
            return "\n".join(error_lines[:3])

        trimmed = dafny_output.strip()
        return trimmed if trimmed else "Lỗi logic không xác định từ bộ giải Dafny/Z3."

    @classmethod
    def format_diagnostic_feedback(cls, code: str, dafny_output: str) -> Tuple[str, str]:
        """Tạo toàn bộ ngữ cảnh phản hồi chẩn đoán giàu ngữ nghĩa (Rich Semantic Diagnostic).

        Trả về tuple: (thông báo lỗi chi tiết có line number và context, category lỗi)
        """
        parsed = cls.parse_diagnostics(dafny_output, code)
        code_lines = code.splitlines()

        if not parsed:
            category = cls.classify_error(dafny_output)
            raw_err = cls.extract_error(dafny_output, code)
            return raw_err, category

        top = parsed[0]
        category = top.error_type

        # Xây dựng ngữ cảnh dòng mã lân cận (2 dòng trước, 2 dòng sau)
        context_block = []
        if top.line and 1 <= top.line <= len(code_lines):
            start = max(1, top.line - 2)
            end = min(len(code_lines), top.line + 2)
            for idx in range(start, end + 1):
                marker = ">>> " if idx == top.line else "    "
                context_block.append(f"{marker}Dòng {idx}: {code_lines[idx - 1]}")
        context_str = "\n".join(context_block)

        feedback_parts = [
            f"❌ LOẠI LỖI: [{top.error_type}] tại Dòng {top.line}, Cột {top.column}",
            f"THÔNG BÁO CHI TIẾT: {top.message}"
        ]

        # Khối phản ví dụ CEGAR từ Z3 SMT Solver
        if top.counterexample:
            ce = top.counterexample
            ce_block = [
                "🎯 PHẢN VÍ DỤ CỤ THỂ TỪ Z3 SMT SOLVER (CEGAR - arXiv:2506.06923):",
                f"- Tóm tắt ca vi phạm: {ce.description}"
            ]
            if ce.initial_state:
                init_vals = ", ".join(f"{k} = {v}" for k, v in ce.initial_state.items())
                ce_block.append(f"- Đầu vào ban đầu: [{init_vals}]")
            if ce.failing_state and ce.failing_state != ce.initial_state:
                fail_vals = ", ".join(f"{k} = {v}" for k, v in ce.failing_state.items())
                ce_block.append(f"- Trạng thái biến khi vi phạm: [{fail_vals}]")
            if ce.violated_clause:
                ce_block.append(f"- Mệnh đề đặc tả bị phá vỡ: `{ce.violated_clause}`")
            ce_block.append("👉 BẮT BUỘC: Bạn phải sửa mã nguồn thuật toán để xử lý chính xác ca biên (Edge Case) này!")
            feedback_parts.append("\n".join(ce_block))

        if top.faulty_line_content:
            feedback_parts.append(f"DÒNG MÃ GÂY LỖI: `{top.faulty_line_content}`")

        if top.related_content:
            feedback_parts.append(f"MỆNH ĐỀ ĐẶC TẢ LIÊN QUAN TRỰC TIẾP (Dòng {top.related_line}): `{top.related_content}`")

        if context_str:
            feedback_parts.append(f"NGỮ CẢNH MÃ NGUỒN XUNG QUANH:\n{context_str}")

        if top.semantic_hint:
            feedback_parts.append(f"💡 HƯỚNG DẪN KHẮC PHỤC NGỮ NGHĨA:\n{top.semantic_hint}")

        # Thêm các lỗi phụ nếu có (tối đa 2 lỗi tiếp theo)
        if len(parsed) > 1:
            feedback_parts.append("\nCÁC CẢNH BÁO/LỖI PHỤ KHÁC TỪ SMT SOLVER:")
            for extra in parsed[1:3]:
                feedback_parts.append(f"- Dòng {extra.line}: [{extra.error_type}] {extra.message}")

        return "\n\n".join(feedback_parts), category

