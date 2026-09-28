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

    @staticmethod
    def extract_forall_prefix_invariant(ensures_clause: str) -> Optional[str]:
        """Tự động phân tích mệnh đề ensures có forall để sinh biểu thức bất biến tiền tố (Prefix Invariant).

        Áp dụng thuật toán biến đổi công thức logic hình thức tổng quát:
        Từ 'forall x ... :: ... ==> Pred(x)', trích xuất vị từ mục tiêu sau dấu '==>'
        và sinh ra 'invariant forall j :: 0 <= j < i ==> Pred(j)'.
        """
        match = re.search(r'forall\s+([a-zA-Z0-9_]+).*?::\s*(.+)', ensures_clause)
        if match:
            var_name = match.group(1).strip()
            body = match.group(2).strip()
            if '==>' in body:
                predicate = body.split('==>')[-1].strip().rstrip(')')
                # Thay thế biến định lượng bằng biến cục bộ j
                pred_with_j = re.sub(rf'\b{re.escape(var_name)}\b', 'j', predicate)
                return f"invariant forall j :: 0 <= j < i ==> {pred_with_j}"
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
                inv_suggestion = f"`{prefix_inv}`" if prefix_inv else "`invariant forall j :: 0 <= j < i ==> P(j)`"
                return (
                    f"HẬU ĐIỀU KIỆN CHỨA ĐỊNH LƯỢNG TOÀN THỂ (FORALL) BỊ VI PHẠM: `{related_content}`.\n"
                    f"NGUYÊN LÝ BẤT BIẾN TIỀN TỐ (PREFIX INDUCTIVE INVARIANT): Để Z3 suy diễn được hậu điều kiện toàn thể, "
                    f"vòng lặp BẮT BUỘC phải duy trì bất biến tiền tố cho các phần tử đã duyệt:\n"
                    f"-> [HÀNH ĐỘNG BẮT BUỘC]: Bổ sung mệnh đề sau vào ngay dưới từ khóa while:\n"
                    f"   {inv_suggestion}"
                )
            if related_content and "exists" in related_content:
                seq_match = re.search(r'\|\s*(\w+)\s*\|', related_content)
                seq_var = seq_match.group(1) if seq_match else "s"
                elem_match = re.search(r'\b\w+\[\w+\]\s*==\s*(\w+)', related_content)
                target_var = elem_match.group(1) if elem_match else "result"
                return (
                    f"HẬU ĐIỀU KIỆN CHỨA ĐỊNH LƯỢNG TỒN TẠI (EXISTS) BỊ VI PHẠM: `{related_content}`.\n"
                    f"[HÀNH ĐỘNG BẮT BUỘC - CHÈN INVARIANT TỒN TẠI]:\n"
                    f"Hậu điều kiện yêu cầu kết quả `{target_var}` phải là một phần tử có thật trong `{seq_var}`.\n"
                    f"1. Gán phần tử đầu tiên cho biến tích lũy: `{target_var} := {seq_var}[0];`\n"
                    f"2. BẮT BUỘC khởi tạo `var i := 1;` (TUYỆT ĐỐI KHÔNG để `i := 0` vì khoảng 0 <= j < 0 rỗng sẽ gây lỗi 'could not be proved on entry')!\n"
                    f"3. Thêm các invariant sau vào ngay dưới từ khóa while:\n"
                    f"   `invariant 1 <= i <= |{seq_var}|`\n"
                    f"   `invariant forall j :: 0 <= j < i ==> {seq_var}[j] <= {target_var}` (nếu tìm max)\n"
                    f"   `invariant exists j :: 0 <= j < i && {seq_var}[j] == {target_var}`"
                )
            if related_content and re.search(r'\b\w+\s*\([^)]*\)', related_content):
                func_match = re.search(r'\b([a-zA-Z_]\w*)\s*\(([^)]*)\)', related_content)
                func_name = func_match.group(1) if func_match else "f"
                arg_name = func_match.group(2).strip() if func_match else "n"
                return (
                    f"HẬU ĐIỀU KIỆN QUY NẠP TƯƠNG ĐƯƠNG HÀM ĐỆ QUY (FUNCTIONAL EQUIVALENCE): `{related_content}`.\n"
                    f"[HÀNH ĐỘNG BẮT BUỘC - ĐỒNG BỘ BẤT BIẾN VỚI HÀM {func_name}]:\n"
                    f"Phương thức đang tính toán để khớp với hàm thuần túy `{func_name}({arg_name})`.\n"
                    f"SMT Solver BẮT BUỘC cần các invariant quy nạp đồng bộ trực tiếp các biến trạng thái lặp với hàm `{func_name}`:\n"
                    f"1. `invariant 0 <= i <= {arg_name}`\n"
                    f"2. `invariant a == {func_name}(i)` (biến tích lũy bước hiện tại)\n"
                    f"3. `invariant b == {func_name}(i + 1)` (nếu là thuật toán đệ quy 2 bước như Fibonacci, biến tích lũy bước tiếp theo)"
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
                "BẮT BUỘC phải dùng định lượng toán học tổng quát: `invariant forall j :: 0 <= j < i ==> s[j] <= acc`."
            )

        if category == "TerminationFailure":
            return (
                "KHÔNG THỂ CHỨNG MINH VÒNG LẶP DỪNG (Termination Failure): "
                "Biểu thức trong mệnh đề `decreases <biểu_thức>` phải luôn bị chặn dưới (>= 0) và giảm nghiêm ngặt sau mỗi bước lặp. "
                "Nếu các biến lặp có thể nhận giá trị âm từ tham số đầu vào (ví dụ trong thuật toán GCD/Euclid), "
                "BẮT BUỘC phải chuyển đổi biến về số không âm (lấy giá trị tuyệt đối nếu âm) trước khi vào vòng lặp."
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

