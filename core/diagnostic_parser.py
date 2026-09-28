"""Module phân tích và bóc tách lỗi chẩn đoán từ Dafny / Z3 SMT Solver.

Phân loại lỗi theo hệ thống danh mục (Error Taxonomy) và cung cấp
hướng dẫn sửa lỗi ngữ nghĩa toán học chi tiết (Semantic Diagnostic Engine).
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


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

        if category == "LoopInvariantViolation":
            if "on entry" in msg_lower:
                return (
                    "BẤT BIẾN KHÔNG ĐÚNG KHI BẮT ĐẦU VÒNG LẶP (on entry): "
                    "Giá trị khởi tạo trước vòng lặp không thỏa mãn bất biến này. "
                    "Nếu dùng định lượng tồn tại `exists j :: 0 <= j < i`, khi i = 0 miền rỗng sẽ gây lỗi; "
                    "hãy đổi thành điều kiện bảo vệ `(i > 0 ==> exists ...)` hoặc bắt đầu biến đếm từ `i := 1`."
                )
            elif "maintained" in msg_lower:
                return (
                    "BẤT BIẾN KHÔNG ĐƯỢC DUY TRÌ SAU THÂN VÒNG LẶP (maintained): "
                    "Sau bước nhảy (ví dụ `i := i + 1`), biến có thể vượt qua biên của invariant. "
                    "Ví dụ: Với vòng lặp `while i <= n`, sau bước lặp `i` sẽ đạt tới `n + 1`, "
                    "do đó invariant cận trên cần nới lỏng thành `i <= n + 1` thay vì `i <= n`."
                )
            return (
                "BẤT BIẾN VÒNG LẶP KHÔNG THỎA MÃN: "
                "Cần kiểm tra lại mối liên hệ giữa điều kiện lặp, bước tăng của biến và giá trị cận."
            )

        if category == "PostconditionViolation":
            if related_content and "forall" in related_content:
                return (
                    f"HẬU ĐIỀU KIỆN CHỨA ĐỊNH LƯỢNG FORALL BỊ VI PHẠM: `{related_content}`.\n"
                    "NGUYÊN LÝ QUY NẠP (INDUCTIVE INVARIANT): Khi hậu điều kiện đòi hỏi tính chất đúng cho toàn bộ tập hợp "
                    "(`forall x :: 0 <= x < |s| ==> P(x)`), vòng lặp duyệt đến biến đếm `i` BẮT BUỘC phải có bất biến tiền tố "
                    "mô tả tính chất đúng cho các phần tử đã duyệt: `invariant forall j :: 0 <= j < i ==> P(j)` "
                    "(trong đó P(j) phản ánh đúng điều kiện ensures, ví dụ: `l[j] <= max`, `l[j] < t`, hoặc `a[j] != target`)."
                )
            if related_content and "exists" in related_content:
                return (
                    f"HẬU ĐIỀU KIỆN CHỨA ĐỊNH LƯỢNG TỒN TẠI (EXISTS) BỊ VI PHẠM: `{related_content}`.\n"
                    "NGUYÊN LÝ QUY NẠP CHO EXISTS: Khi hậu điều kiện yêu cầu kết quả phải tồn tại trong danh sách "
                    "(`exists x :: 0 <= x < |s| && s[x] == result`), vòng lặp BẮT BUỘC phải có bất biến chứng minh "
                    "giá trị tích lũy hiện tại luôn là một phần tử hợp lệ đã duyệt: "
                    "`invariant exists j :: 0 <= j < i && l[j] == max` (với vòng lặp bắt đầu từ `i := 1`)."
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

        if "does not have a member max" in msg_lower or "does not have a member min" in msg_lower:
            return (
                "KIỂU SEQ KHÔNG CÓ METHOD .max() / .min(): "
                "Trong Dafny, kiểu `seq<T>` không có phương thức built-in `.max()` hay `.min()`. "
                "BẮT BUỘC phải dùng định lượng toán học: "
                "`invariant forall j :: 0 <= j < i ==> l[j] <= max` (và `invariant exists j :: 0 <= j < i && l[j] == max`)."
            )

        if category == "TerminationFailure":
            return (
                "KHÔNG THỂ CHỨNG MINH VÒNG LẶP DỪNG: "
                "Hãy thêm mệnh đề `decreases <biểu_thức>` giảm nghiêm ngặt sau mỗi bước lặp và luôn >= 0."
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

        return errors

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

