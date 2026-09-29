"""Module định vị và vá cục bộ cấp độ AST (AST-Level Localized Patching).

Khắc phục triệt để lỗi sinh toàn văn (Whole-Method Regeneration Flaw).
Khi thuật toán đã có thân lệnh cơ bản đúng, cơ chế này chỉ sửa hoặc thay thế
phân vùng Proof (khối invariant/decreases/assert) mà giữ nguyên 100% thân hàm.
"""

import re
from typing import Dict, List, Optional, Tuple


class ASTLocalizer:
    """Bộ bóc tách và vá cục bộ các khối chú thích hình thức trong phương thức Dafny."""

    @classmethod
    def extract_loop_structure(cls, code: str) -> Optional[Dict[str, str]]:
        """Bóc tách cấu trúc vòng lặp while thành các phân vùng độc lập.

        Trả về dictionary gồm:
        - 'prefix': Mã nguồn từ đầu đến trước từ khóa while
        - 'while_guard': 'while <điều_kiện>'
        - 'invariants': Danh sách các dòng invariant và decreases hiện có
        - 'loop_body_with_braces': '{ ... }' của vòng lặp
        - 'suffix': Phần mã sau dấu đóng ngoặc } của vòng lặp đến hết hàm
        """
        # Regex tìm khối while:
        # while <guard>
        #   (invariant / decreases)*
        # { <body> }
        pattern = re.compile(
            r'^(?P<prefix>.*?)(?P<while_hdr>\bwhile\b[^{\n]+)(?P<clauses>(?:\s*(?:invariant|decreases)[^\n]+)*)\s*(?P<body>\{.*)',
            re.DOTALL | re.MULTILINE
        )
        match = pattern.search(code)
        if not match:
            return None

        prefix = match.group('prefix')
        while_hdr = match.group('while_hdr').strip()
        clauses_raw = match.group('clauses')
        body_and_rest = match.group('body')

        # Tìm closing brace tương ứng của vòng lặp while
        depth = 0
        end_idx = -1
        for i, char in enumerate(body_and_rest):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            return None

        loop_body = body_and_rest[:end_idx]
        suffix = body_and_rest[end_idx:]

        # Bóc tách từng mệnh đề invariant/decreases
        invariants = []
        if clauses_raw:
            for line in clauses_raw.splitlines():
                stripped = line.strip()
                if stripped.startswith("invariant") or stripped.startswith("decreases"):
                    invariants.append(stripped)

        return {
            "prefix": prefix,
            "while_guard": while_hdr,
            "invariants": invariants,
            "loop_body": loop_body,
            "suffix": suffix
        }

    @classmethod
    def patch_loop_invariants(cls, code: str, new_invariants: List[str]) -> str:
        """Thay thế hoặc bổ sung các mệnh đề invariant mà không thay đổi bất kỳ dòng lệnh nào trong thân hàm."""
        loop_struct = cls.extract_loop_structure(code)
        if not loop_struct:
            return code

        # Định dạng lại các invariant mới với thụt lề chuẩn 8 dấu cách
        formatted_invs = []
        for inv in new_invariants:
            clean_inv = inv.strip().rstrip(";")
            if clean_inv:
                formatted_invs.append(f"        {clean_inv}")

        joined_invs = "\n".join(formatted_invs)
        prefix = loop_struct["prefix"]
        while_guard = loop_struct["while_guard"]
        body = loop_struct["loop_body"]
        suffix = loop_struct["suffix"]

        if joined_invs:
            patched = f"{prefix}{while_guard}\n{joined_invs}\n    {body}{suffix}"
        else:
            patched = f"{prefix}{while_guard}\n    {body}{suffix}"

        return patched

    @classmethod
    def inject_intermediate_assert(cls, code: str, assertion: str) -> str:
        """Chèn câu lệnh assert trung gian vào ngay sau vòng lặp while để phân rã chứng minh (Proof Slicing)."""
        loop_struct = cls.extract_loop_structure(code)
        if not loop_struct:
            return code

        clean_assert = assertion.strip().rstrip(";")
        if not clean_assert.startswith("assert"):
            clean_assert = f"assert {clean_assert}"

        prefix = loop_struct["prefix"]
        while_guard = loop_struct["while_guard"]
        invs = "\n".join(f"        {inv}" for inv in loop_struct["invariants"])
        body = loop_struct["loop_body"]
        suffix = loop_struct["suffix"]

        inv_part = f"\n{invs}" if invs else ""
        assert_stmt = f"\n    {clean_assert};"

        return f"{prefix}{while_guard}{inv_part}\n    {body}{assert_stmt}{suffix}"
