"""Module chuẩn hóa cú pháp Dafny tự động (Dafny Syntax Normalizer).

Thực hiện các phép biến đổi Source-to-Source bảo toàn ngữ nghĩa (semantics-preserving)
để sửa các lỗi cú pháp hệ thống mà mô hình LLM nhỏ (7B) thường mắc phải do khoảng cách
giữa ngôn ngữ huấn luyện (Python/Java/C++) và ngôn ngữ đích (Dafny 4.x).
"""

import re
from typing import List, Set, Tuple


class SyntaxNormalizer:
    """Bộ chuẩn hóa cú pháp Dafny tự động áp dụng tổng quát cho mọi bài toán."""

    @staticmethod
    def _extract_method_signatures(code: str) -> List[Tuple[List[str], List[str]]]:
        """Trích xuất danh sách (input_params, output_params) của mỗi method trong mã nguồn.

        Trả về danh sách tuple: ([tên_input_1, ...], [tên_output_1, ...])
        """
        signatures = []
        # Bắt khai báo method với cả input và output parameters
        method_pattern = re.compile(
            r'method\s+\w+\s*\(([^)]*)\)\s*returns\s*\(([^)]*)\)',
            re.MULTILINE
        )
        for match in method_pattern.finditer(code):
            raw_inputs = match.group(1).strip()
            raw_outputs = match.group(2).strip()

            # Trích xuất tên biến từ danh sách tham số "name1: Type1, name2: Type2"
            input_names = []
            for param in raw_inputs.split(','):
                param = param.strip()
                if ':' in param:
                    name = param.split(':')[0].strip()
                    if name:
                        input_names.append(name)

            output_names = []
            for param in raw_outputs.split(','):
                param = param.strip()
                if ':' in param:
                    name = param.split(':')[0].strip()
                    if name:
                        output_names.append(name)

            signatures.append((input_names, output_names))

        return signatures

    @classmethod
    def _get_all_out_params(cls, code: str) -> Set[str]:
        """Lấy tập hợp tất cả tên biến ngõ ra (out-parameters) trong mã nguồn."""
        out_params = set()
        for _, outputs in cls._extract_method_signatures(code):
            out_params.update(outputs)
        return out_params

    @classmethod
    def _get_all_input_params(cls, code: str) -> Set[str]:
        """Lấy tập hợp tất cả tên tham số đầu vào (input parameters) trong mã nguồn."""
        input_params = set()
        for inputs, _ in cls._extract_method_signatures(code):
            input_params.update(inputs)
        return input_params

    @classmethod
    def fix_duplicate_out_params(cls, code: str) -> str:
        """Phép biến đổi 1: Loại bỏ khai báo trùng biến ngõ ra.

        Dafny: Biến trong `returns (name: Type)` đã tồn tại trong scope.
        LLM sai: `var name := expr;` hoặc `var name : Type := expr;`
        Sửa:     `name := expr;`
        """
        out_params = cls._get_all_out_params(code)
        if not out_params:
            return code

        result = code
        for param in out_params:
            # Mẫu 1: var name : Type := expr;
            result = re.sub(
                rf'(\s+)var\s+{re.escape(param)}\s*:\s*\w+\s*:=',
                rf'\1{param} :=',
                result
            )
            # Mẫu 2: var name := expr;
            result = re.sub(
                rf'(\s+)var\s+{re.escape(param)}\s*:=',
                rf'\1{param} :=',
                result
            )
        return result

    @classmethod
    def fix_return_expr(cls, code: str) -> str:
        """Phép biến đổi 2: Chuyển `return <expr>;` thành phép gán + `return;`.

        Dafny method: Không hỗ trợ `return expr;`, chỉ hỗ trợ `return;`.
        """
        out_params = cls._get_all_out_params(code)
        if not out_params:
            return code

        result = code
        # Xử lý `return <out_param>;` → chỉ giữ return; (giá trị đã gán sẵn)
        for param in out_params:
            result = re.sub(
                rf'(\s+)return\s+{re.escape(param)}\s*;',
                r'\1return;',
                result
            )

        # Xử lý `return <expr khác>;` → gán vào out_param đầu tiên rồi return;
        # Chỉ áp dụng nếu có đúng 1 biến ngõ ra
        if len(out_params) == 1:
            single_param = list(out_params)[0]
            # Tìm return <expr>; nhưng không phải return; (đã xử lý ở trên)
            def replace_return_expr(match):
                indent = match.group(1)
                expr = match.group(2).strip()
                if not expr or expr == single_param:
                    return f"{indent}return;"
                return f"{indent}{single_param} := {expr};\n{indent}return;"

            result = re.sub(
                r'(\s+)return\s+(.+?)\s*;',
                replace_return_expr,
                result
            )
        return result

    @staticmethod
    def fix_ternary_operator(code: str) -> str:
        """Phép biến đổi 3: Chuyển toán tử ternary `? :` thành `if/else` block.

        Dafny method: Không hỗ trợ biểu thức `cond ? a : b` trong method body.
        """
        # Mẫu: <var> := <condition> ? <expr_true> : <expr_false>;
        ternary_pattern = re.compile(
            r'(\s+)(\w+)\s*:=\s*(.+?)\s*\?\s*(.+?)\s*:\s*(.+?)\s*;',
            re.MULTILINE
        )

        def replace_ternary(match):
            indent = match.group(1)
            var_name = match.group(2)
            condition = match.group(3).strip()
            expr_true = match.group(4).strip()
            expr_false = match.group(5).strip()
            return (
                f"{indent}if {condition} {{\n"
                f"{indent}    {var_name} := {expr_true};\n"
                f"{indent}}} else {{\n"
                f"{indent}    {var_name} := {expr_false};\n"
                f"{indent}}}"
            )

        return ternary_pattern.sub(replace_ternary, code)

    @classmethod
    def fix_immutable_input_params(cls, code: str) -> str:
        """Phép biến đổi 4: Sao chép tham số đầu vào thành biến cục bộ khi bị gán lại.

        Dafny: Input parameters là immutable, không thể gán lại giá trị.
        """
        signatures = cls._extract_method_signatures(code)
        result = code

        for input_params, _ in signatures:
            for param in input_params:
                # Kiểm tra xem param có bị gán lại trong thân hàm không
                # Tìm pattern: <indent><param> := (không phải trong khai báo method/ensures)
                assign_pattern = re.compile(
                    rf'^\s+{re.escape(param)}\s*:=\s*',
                    re.MULTILINE
                )
                if assign_pattern.search(result):
                    local_name = f"{param}_local"
                    # Chèn khai báo biến cục bộ ngay sau dấu mở ngoặc { đầu tiên của method tương ứng
                    # Tìm vị trí method chứa param này
                    method_body_pattern = re.compile(
                        rf'(method\s+\w+\s*\([^)]*\b{re.escape(param)}\b[^)]*\)\s*'
                        rf'(?:returns\s*\([^)]*\)\s*)?'
                        rf'(?:requires[^\n]*\n\s*)*'
                        rf'(?:ensures[^\n]*\n\s*)*'
                        rf'(?://[^\n]*\n\s*)*'
                        rf')\{{',
                        re.MULTILINE
                    )
                    match = method_body_pattern.search(result)
                    if match:
                        insert_pos = match.end()
                        # Chèn khai báo biến cục bộ
                        result = (
                            result[:insert_pos] +
                            f"\n    var {local_name} := {param};" +
                            result[insert_pos:]
                        )
                        # Thay thế tất cả phép gán/sử dụng của param thành local_name
                        # Nhưng chỉ trong thân hàm, không phải trong khai báo method/ensures
                        # Sử dụng cách đơn giản: thay thế trong phần thân sau dấu {
                        body_start = insert_pos
                        body_text = result[body_start:]
                        body_text = re.sub(
                            rf'\b{re.escape(param)}\b',
                            local_name,
                            body_text
                        )
                        result = result[:body_start] + body_text

        return result

    @staticmethod
    def fix_seq_assignment(code: str) -> str:
        """Phép biến đổi 5: Chuyển phép gán trên seq thành cú pháp functional update.

        Dafny: seq là kiểu bất biến, `s[i] := val` sai cú pháp.
        Sửa:   `s := s[i := val];`
        """
        # Mẫu: <var>[<index>] := <expr>;
        seq_assign_pattern = re.compile(
            r'(\s+)(\w+)\[([^\]]+)\]\s*:=\s*(.+?)\s*;',
            re.MULTILINE
        )

        def replace_seq_assign(match):
            indent = match.group(1)
            var_name = match.group(2)
            index = match.group(3).strip()
            value = match.group(4).strip()
            return f"{indent}{var_name} := {var_name}[{index} := {value}];"

        return seq_assign_pattern.sub(replace_seq_assign, code)

    @staticmethod
    def fix_misplaced_loop_invariants(code: str) -> str:
        """Phép biến đổi 6: Di chuyển invariant/decreases đặt sai bên trong thân while ra trước dấu {.

        Trong Dafny, mệnh đề invariant/decreases BẮT BUỘC nằm TRƯỚC dấu { của while.
        Nếu LLM đặt chúng ngay sau dấu { (kèm dấu ;), tự động bóc tách và đưa ra trước {.
        """
        pattern = re.compile(
            r'(\bwhile\b[^{]+)\{\s*([\r\n]+(?:\s*(?:invariant|decreases)\s+[^\r\n;]+;?\s*)+)',
            re.MULTILINE
        )

        def move_invariants(match):
            while_header = match.group(1).rstrip()
            raw_clauses = match.group(2)
            clauses = []
            for line in raw_clauses.splitlines():
                line_str = line.strip()
                if line_str.startswith("invariant") or line_str.startswith("decreases"):
                    # Xóa dấu chấm phẩy thừa ở cuối nếu có
                    clean_clause = line_str.rstrip(";").strip()
                    clauses.append("        " + clean_clause)

            if not clauses:
                return match.group(0)

            joined_clauses = "\n".join(clauses)
            return f"{while_header}\n{joined_clauses}\n    {{"

        return pattern.sub(move_invariants, code)

    @classmethod
    def normalize(cls, code: str) -> str:
        """Áp dụng toàn bộ các phép chuẩn hóa cú pháp theo thứ tự an toàn.

        Thứ tự áp dụng:
        1. Sửa vị trí đặt invariant/decreases bên trong thân while
        2. Loại bỏ khai báo trùng biến ngõ ra
        3. Chuyển đổi toán tử ternary
        4. Chuyển đổi return <expr>
        5. Chuyển đổi phép gán trên seq
        """
        if not code or not code.strip():
            return code

        result = code
        result = cls.fix_misplaced_loop_invariants(result)
        result = cls.fix_duplicate_out_params(result)
        result = cls.fix_ternary_operator(result)
        result = cls.fix_return_expr(result)
        result = cls.fix_seq_assignment(result)
        return result

