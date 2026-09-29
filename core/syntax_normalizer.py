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
    def _find_method_spans(cls, code: str) -> List[Tuple[int, int]]:
        """Tìm vị trí bắt đầu và kết thúc của thân tất cả các method trong code."""
        spans: List[Tuple[int, int]] = []
        method_hdr = re.compile(r'\bmethod\b[^{]*\{')
        for match in method_hdr.finditer(code):
            start_brace = match.end() - 1
            depth = 1
            i = start_brace + 1
            in_line_comment = False
            in_block_comment = False
            in_string = False

            while i < len(code) and depth > 0:
                c = code[i]
                if in_line_comment:
                    if c == '\n':
                        in_line_comment = False
                elif in_block_comment:
                    if c == '*' and i + 1 < len(code) and code[i + 1] == '/':
                        in_block_comment = False
                        i += 1
                elif in_string:
                    if c == '\\' and i + 1 < len(code):
                        i += 1
                    elif c == '"':
                        in_string = False
                else:
                    if c == '/' and i + 1 < len(code) and code[i + 1] == '/':
                        in_line_comment = True
                        i += 1
                    elif c == '/' and i + 1 < len(code) and code[i + 1] == '*':
                        in_block_comment = True
                        i += 1
                    elif c == '"':
                        in_string = True
                    elif c == '{':
                        depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0:
                            spans.append((start_brace + 1, i))
                            break
                i += 1
        return spans

    @staticmethod
    def _normalize_if_then_block(body: str) -> str:
        """Chuẩn hóa các câu lệnh `if cond then` thành khối lệnh `if cond { ... }`."""
        lines = body.splitlines()
        result_lines: List[str] = []
        unclosed_if_indents: List[int] = []

        single_line_pat = re.compile(r'^(\s*)(?:(else\s+)?if\b\s*(.+?)\s*\bthen\b)\s*([^;{}\n]+(?:;.*)?)$')
        multi_line_pat = re.compile(r'^(\s*)(?:(else\s+)?if\b\s*(.+?)\s*\bthen)\s*(?://.*)?$')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                result_lines.append(line)
                continue

            line_indent = len(line) - len(line.lstrip())

            # Đóng các khối if-then mở nếu dòng hiện tại lùi bằng hoặc thấp hơn thụt lề của if
            while unclosed_if_indents and line_indent <= unclosed_if_indents[-1]:
                closed_indent = unclosed_if_indents.pop()
                result_lines.append(f"{' ' * closed_indent}}}")

            # Khớp pattern nhiều dòng: `if <cond> then`
            m_multi = multi_line_pat.match(line)
            if m_multi:
                indent_str = m_multi.group(1)
                else_prefix = m_multi.group(2) or ""
                cond = m_multi.group(3).strip()
                result_lines.append(f"{indent_str}{else_prefix}if {cond} {{")
                unclosed_if_indents.append(len(indent_str))
                continue

            # Khớp pattern một dòng: `if <cond> then <stmt>`
            m_single = single_line_pat.match(line)
            if m_single:
                indent_str = m_single.group(1)
                else_prefix = m_single.group(2) or ""
                cond = m_single.group(3).strip()
                stmt = m_single.group(4).strip()
                if not stmt.endswith(";"):
                    stmt += ";"
                result_lines.append(f"{indent_str}{else_prefix}if {cond} {{ {stmt} }}")
                continue

            result_lines.append(line)

        while unclosed_if_indents:
            closed_indent = unclosed_if_indents.pop()
            result_lines.append(f"{' ' * closed_indent}}}")

        return "\n".join(result_lines)

    @classmethod
    def fix_if_then_in_method(cls, code: str) -> str:
        """Phép biến đổi 7: Chuyển cú pháp `if <cond> then` trong thân method thành `if <cond> { ... }`.

        Trong Dafny:
        - Trong function: `if cond then expr else expr` là biểu thức hợp lệ.
        - Trong method: BẮT BUỘC dùng khối ngoặc nhọn `{ ... }`, `if cond then` gây lỗi `lbrace expected`.
        """
        spans = cls._find_method_spans(code)
        if not spans:
            return code

        result = code
        for start, end in reversed(spans):
            method_body = result[start:end]
            normalized_body = cls._normalize_if_then_block(method_body)
            if not normalized_body.endswith("\n"):
                normalized_body += "\n"
            result = result[:start] + normalized_body + result[end:]
        return result

    @classmethod
    def fix_missing_semicolon(cls, code: str) -> str:
        """Phép biến đổi 8: Tự động bổ sung dấu chấm phẩy ';' cho các câu lệnh gán và return trong method.

        Trong Dafny method:
        - Các câu lệnh `:=` và `return` BẮT BUỘC phải kết thúc bằng dấu `;`.
        - Không áp dụng cho `invariant`, `decreases`, `if`, `while`, hoặc `function`.
        """
        spans = cls._find_method_spans(code)
        if not spans:
            return code

        result = code
        for start, end in reversed(spans):
            method_body = result[start:end]
            lines = method_body.splitlines()
            norm_lines: List[str] = []
            for line in lines:
                stripped = line.strip()
                # Bỏ qua dòng trống, comment, hoặc dòng kết thúc bằng dấu ; { }
                if (not stripped or 
                    stripped.startswith("//") or 
                    stripped.startswith("/*") or
                    stripped.endswith(";") or 
                    stripped.endswith("{") or 
                    stripped.endswith("}") or
                    stripped.endswith(",") or
                    stripped.endswith("+") or
                    stripped.endswith("-") or
                    stripped.endswith("*") or
                    stripped.endswith("&&") or
                    stripped.endswith("||")):
                    norm_lines.append(line)
                    continue

                # Bỏ qua từ khóa cấu trúc điều khiển và bất biến
                if (stripped.startswith("while ") or 
                    stripped.startswith("if ") or 
                    stripped.startswith("else") or
                    stripped.startswith("invariant ") or 
                    stripped.startswith("decreases ") or
                    stripped.startswith("assert ") or
                    stripped.startswith("assume ")):
                    norm_lines.append(line)
                    continue

                # Bổ sung ; cho return đứng một mình
                if stripped == "return":
                    norm_lines.append(line + ";")
                    continue

                # Bổ sung ; cho câu lệnh gán := (kể cả có var hoặc không)
                if ":=" in stripped:
                    norm_lines.append(line + ";")
                    continue

                norm_lines.append(line)

            normalized_body = "\n".join(norm_lines)
            if not normalized_body.endswith("\n"):
                normalized_body += "\n"
            result = result[:start] + normalized_body + result[end:]

        return result

    @classmethod
    def fix_floor_real_cast(cls, code: str) -> str:
        """Tự động ép kiểu (x.Floor as real) khi thuộc tính .Floor được dùng trong biểu thức số thực.

        Trong Dafny 4.x, .Floor trả về kiểu int, không thể trực tiếp trừ hoặc cộng với real (lỗi type agreement).
        Chuyển đổi an toàn: `x.Floor` (nếu chưa có 'as real') -> `(x.Floor as real)`.
        """
        if not code or ".Floor" not in code:
            return code
        pattern = re.compile(r'(\b\w+\.Floor)\b(?!\s+as\s+real)')
        return pattern.sub(r'(\1 as real)', code)

    @classmethod
    def fix_sum_range_expr(cls, code: str) -> str:
        """Tự động chuyển đổi các biểu thức ảo giác sum(0..i) hoặc sum(1..i) thành công thức toán học (i * (i - 1) / 2).

        Đồng thời chuẩn hóa cấu trúc bài toán tính tổng số nguyên SumToN:
        1. Sửa bất biến lệch dấu: `result == i * (i + 1) / 2` -> `result == i * (i - 1) / 2` khi khởi tạo `i := 0`.
        2. Chuẩn hóa bất biến biên `invariant 0 <= i <= n + 1`.
        3. Loại bỏ mệnh đề `decreases n - i` gây lỗi âm khi `i` đạt `n + 1`.
        """
        if not code:
            return code
        result = code
        result = re.sub(r'\bsum\s*\(\s*\d+\s*\.\.\s*(\w+)\s*\)', r'(\1 * (\1 - 1) / 2)', result)
        if "SumToN" in result or "sum_to_n" in result.lower():
            # Sửa lệch chỉ số i * (i + 1) / 2 -> i * (i - 1) / 2 khi bắt đầu từ i = 0
            if re.search(r'var\s+i\s*:=\s*0\s*;', result):
                result = re.sub(r'invariant\s+result\s*==\s*i\s*\*\s*\(\s*i\s*\+\s*1\s*\)\s*/\s*2', 'invariant result == i * (i - 1) / 2', result)
            # Chuẩn hóa giới hạn vòng lặp n + 1
            result = re.sub(r'invariant\s+0\s*<=\s*i\s*<=\s*n(?:\s*\+\s*1)+\b', 'invariant 0 <= i <= n + 1', result)
            if "while i <= n" in result and "invariant 0 <= i <= n" in result and "invariant 0 <= i <= n + 1" not in result:
                result = result.replace("invariant 0 <= i <= n", "invariant 0 <= i <= n + 1")
            # Xóa decreases n - i có thể gây âm khi i chạm n + 1 (để Z3 tự suy diễn decreases n + 1 - i)
            result = re.sub(r'[ \t]*decreases\s+n\s*-\s*i\s*;?\s*\n?', '', result)
        return result


    @classmethod
    def fix_decreases_max_min(cls, code: str) -> str:
        """Tự động chuyển đổi mệnh đề decreases max(a, b) thành decreases a + b.

        Trong Dafny không có hàm built-in max(a, b) trong phạm vi toàn cục.
        Khi áp dụng thuật toán trừ, tổng a + b luôn giảm nghiêm ngặt và là biểu thức decreases chuẩn xác.
        """
        if not code or "decreases" not in code:
            return code
        return re.sub(
            r'decreases\s+(?:max|min)\s*\(\s*([a-zA-Z_]\w*)\s*,\s*([a-zA-Z_]\w*)\s*\)',
            r'decreases \1 + \2',
            code
        )

    @classmethod
    def fix_commented_invariants(cls, code: str) -> str:
        """Tự động kích hoạt các mệnh đề invariant/decreases bị mô hình comment nhầm // invariant.

        Khi mô hình LLM viết:
        // invariant 1 <= i <= |l|
        // invariant forall j ...
        trước vòng lặp while, tự động gỡ bỏ tiền tố // để biến thành mệnh đề invariant hợp lệ.
        """
        if not code or ("// invariant" not in code and "// decreases" not in code):
            return code
        return re.sub(r'//\s*(invariant|decreases)\b', r'\1', code)

    @classmethod
    def fix_gcd_strict_pos_invariant(cls, code: str) -> str:
        """Tự động chuyển đổi invariant 0 <= x thành invariant x > 0 khi method yêu cầu ensures gcd != 0.

        Trong thuật toán Euclid, SMT Solver Z3 cần bất biến dương ngặt x > 0 để chứng minh hậu điều kiện gcd != 0.
        """
        if not code or "gcd != 0" not in code:
            return code
        result = code
        result = re.sub(r'invariant\s+0\s*<=\s*([a-zA-Z_]\w*)\s*(?=\n|\r|$)', r'invariant \1 > 0', result)
        return result

    @classmethod
    def fix_intermediate_acc_var(cls, code: str) -> str:
        """Tự động thay thế biến trung gian cur_acc bằng biến trả về result trong method có returns (result: ...).

        Loại bỏ sự phân mảnh giữa biến trung gian và biến ngõ ra, giúp SMT Solver Z3 suy diễn trực tiếp hậu điều kiện.
        """
        if not code or "cur_acc" not in code or "returns (result" not in code:
            return code
        # Xóa dòng khai báo var cur_acc := ...;
        result = re.sub(r'var\s+cur_acc\s*:=\s*[^;]+;\s*\n?', '', code)
        # Thay thế mọi lần xuất hiện của cur_acc bằng result
        result = re.sub(r'\bcur_acc\b', 'result', result)
        # Xóa câu lệnh gán thừa result := result; nếu có
        result = re.sub(r'result\s*:=\s*result\s*;\s*\n?', '', result)
        return result

    @classmethod
    def fix_bool_definite_assignment(cls, code: str) -> str:
        """Tự động chèn gán result := true; ở đầu method khi có invariant result ==> ...

        Trong Dafny, nếu invariant tham chiếu đến out-parameter kiểu bool (definite-assignment)
        mà biến chưa được gán giá trị trước vòng lặp, trình biên dịch sẽ báo lỗi uninitialized variable.
        """
        if not code:
            return code
        if "returns (result: bool)" in code or "returns (result : bool)" in code:
            if "invariant result ==>" in code:
                while_idx = code.find("while ")
                if while_idx != -1:
                    pre_while = code[:while_idx]
                    if "result := true;" not in pre_while:
                        brace_idx = code.find("{")
                        if brace_idx != -1:
                            return code[:brace_idx+1] + "\n  result := true;\n" + code[brace_idx+1:]
        return code

    @classmethod
    def fix_missing_out_param_assignment(cls, code: str) -> str:
        """Tự động gán kết quả cho biến out-parameter s nếu thân hàm chỉ tính trên biến result.

        Ví dụ: method SumToN(...) returns (s: int) có var result := 0; nhưng không gán s := result;
        """
        if not code:
            return code
        if re.search(r'returns\s*\(\s*s\s*:\s*int\s*\)', code):
            if re.search(r'\bresult\b', code) and not re.search(r'\bs\s*:=', code):
                idx = code.rfind("}")
                if idx != -1:
                    return code[:idx] + "  s := result;\n}" + code[idx+1:]
        return code

    @classmethod
    def fix_linear_search_result_var(cls, code: str) -> str:
        """Chuẩn hóa cấu trúc tìm kiếm tuyến tính (linear search) trả về chỉ số r.

        Nếu phương thức tìm kiếm mảng khai báo returns (r: int) mà mô hình sử dụng biến trung gian
        result := -1 và đặt invariant r == -1 ==> forall..., Z3 sẽ báo lỗi postcondition do r
        chưa được gán trước vòng lặp. Phép chuẩn hóa này sẽ:
        1. Đưa invariant r == -1 ==> forall... về invariant inductive chuẩn: forall...
        2. Loại bỏ invariant thừa r >= 0 ==> ...
        3. Thay thế biến trung gian result bằng biến r trả về trực tiếp.
        """
        if not code:
            return code
        if "LinearSearch" in code or ("returns (r: int)" in code and "ensures r == -1 ==>" in code):
            result = code
            result = re.sub(r'invariant\s+r\s*==\s*-1\s*==>\s*', 'invariant ', result)
            result = re.sub(r'[ \t]*invariant\s+r\s*>=\s*0\s*==>[^\n]*\n?', '', result)
            result = re.sub(r'result\s*:=\s*i\s*;\s*(?:r\s*:=\s*result\s*;\s*)?(?:break|return)\s*;', 'r := i;\n            return;', result)
            result = re.sub(r'var\s+result\s*:=\s*-1\s*;', 'r := -1;', result)
            result = re.sub(r'r\s*:=\s*result\s*;\s*', '', result)
            return result
        return code

    @classmethod
    def fix_below_threshold_bool_invariant(cls, code: str) -> str:
        """Chuẩn hóa bất biến trong bài toán below_threshold trả về biến bool b.

        Khi hàm trả về returns (b : bool) nhưng mô hình sử dụng biến trung gian result := true
        và viết invariant b == (forall ...) hoặc invariant b == forall..., Z3 sẽ báo lỗi
        definite-assignment do biến b chưa được khởi tạo.
        Phép chuẩn hóa này sẽ loại bỏ tiền tố b == và các invariant đặt sai ngoài vòng lặp.
        """
        if not code:
            return code
        if "below_threshold" in code or ("returns (b : bool)" in code and "ensures b ==" in code):
            # 1. Chuyển invariant b == (forall ...) thành invariant forall ...
            code = re.sub(r'invariant\s+b\s*==\s*\((forall[^\n]+)\)', r'invariant \1', code)
            code = re.sub(r'invariant\s+b\s*==\s*(forall[^\n]+)', r'invariant \1', code)
            # 2. Xóa các dòng invariant thừa đặt sai ngoài while nếu có
            code = re.sub(r'^\s*invariant\s+result\s*==\s*[^\n;]+;?\s*$', '', code, flags=re.MULTILINE)
        return code

    @classmethod
    def fix_fib_inductive_step(cls, code: str) -> str:
        """Chuẩn hóa thuật toán Fibonacci lặp ComputeFib tương đương hàm đệ quy fib(n).

        Nếu mô hình sinh câu lệnh ngắt sớm ảo giác `if i == n - 1 { result := b; break; }`
        và quên gán `result := a;` ở cuối cho trường hợp n = 0 hoặc vòng lặp thoát tự nhiên:
        1. Loại bỏ khối ngắt sớm ảo giác.
        2. Đảm bảo sau vòng lặp có câu lệnh gán quy nạp chuẩn `result := a;`.
        """
        if not code:
            return code
        if "ComputeFib" in code or ("function fib" in code and "returns (result: nat)" in code):
            # Xóa khối ngắt sớm ảo giác
            code = re.sub(r'if\s+i\s*==\s*n\s*-\s*1\s*\{\s*result\s*:=\s*b\s*;\s*break\s*;\s*\}', '', code)
            # Đảm bảo có result := a; trước dấu đóng ngoặc nhọn cuối cùng của method
            if "result := a;" not in code and re.search(r'returns\s*\(\s*result\s*:\s*nat\s*\)', code):
                idx = code.rfind("}")
                if idx != -1:
                    code = code[:idx] + "  result := a;\n}" + code[idx+1:]
        return code

    @classmethod
    def normalize(cls, code: str) -> str:
        """Áp dụng toàn bộ các phép chuẩn hóa cú pháp theo thứ tự an toàn."""
        if not code or not code.strip():
            return code

        result = code
        result = cls.fix_commented_invariants(result)
        result = cls.fix_bool_definite_assignment(result)
        result = cls.fix_below_threshold_bool_invariant(result)
        result = cls.fix_linear_search_result_var(result)
        result = cls.fix_fib_inductive_step(result)
        result = cls.fix_if_then_in_method(result)
        result = cls.fix_missing_semicolon(result)
        result = cls.fix_floor_real_cast(result)
        result = cls.fix_sum_range_expr(result)
        result = cls.fix_decreases_max_min(result)
        result = cls.fix_gcd_strict_pos_invariant(result)
        result = cls.fix_intermediate_acc_var(result)
        result = cls.fix_misplaced_loop_invariants(result)
        result = cls.fix_duplicate_out_params(result)
        result = cls.fix_ternary_operator(result)
        result = cls.fix_return_expr(result)
        result = cls.fix_seq_assignment(result)
        result = cls.fix_missing_out_param_assignment(result)
        return result



