"""Module bảo toàn cấu trúc đề bài chuẩn (Template Preserver).

Tự động nhận diện và bảo toàn các hàm phụ trợ toán học (pure functions, predicates, lemmas)
từ đề bài benchmark gốc nếu mô hình LLM vô tình lược bỏ khi sinh mã.
"""

import re
from typing import List, Tuple


class TemplatePreserver:
    """Quản lý bảo tồn các định nghĩa toán học tiên đề trong đề bài Dafny."""

    @staticmethod
    def extract_auxiliary_blocks(raw_spec: str) -> List[Tuple[str, str, str]]:
        """Trích xuất các khối function, predicate, lemma từ đề bài gốc.

        Trả về danh sách tuple: (loại_khối, tên_hàm, toàn_bộ_nội_dung_khối)
        """
        blocks = []

        # Mẫu 1: Các khối được đánh dấu tường minh bằng // pure-end (chuẩn HumanEval-Dafny)
        pure_pattern = re.compile(
            r'((?:function|predicate|lemma)\s+([a-zA-Z0-9_]+)[\s\S]*?// pure-end)',
            re.MULTILINE
        )
        for match in pure_pattern.finditer(raw_spec):
            full_block = match.group(1).strip()
            name = match.group(2)
            kind = full_block.split()[0]
            blocks.append((kind, name, full_block))

        # Mẫu 2: Nếu không có // pure-end, tìm các function/predicate/lemma có ngoặc nhọn
        if not blocks:
            func_pattern = re.compile(
                r'((?:function|predicate|lemma)\s+([a-zA-Z0-9_]+)[^{]*?\{[\s\S]*?\})',
                re.MULTILINE
            )
            for match in func_pattern.finditer(raw_spec):
                full_block = match.group(1).strip()
                name = match.group(2)
                kind = match.group(1).split()[0]
                blocks.append((kind, name, full_block))

        return blocks

    @classmethod
    def preserve_code(cls, raw_spec: str, generated_code: str) -> str:
        """Kiểm tra và tự động khôi phục các khối hàm phụ trợ nếu LLM bị thiếu."""
        if not generated_code.strip():
            return generated_code

        aux_blocks = cls.extract_auxiliary_blocks(raw_spec)
        if not aux_blocks:
            return generated_code

        preserved_code = generated_code
        header_additions = []
        footer_additions = []

        for kind, name, full_block in aux_blocks:
            # Kiểm tra xem tên hàm/lemma này đã được khai báo trong generated_code chưa
            decl_pattern = re.compile(rf'\b(?:function|predicate|lemma)\s+{re.escape(name)}\b')
            if not decl_pattern.search(preserved_code):
                # Xác định xem trong raw_spec khối này nằm ở đầu hay cuối file
                pos_in_raw = raw_spec.find(full_block)
                half_len = len(raw_spec) // 2
                if pos_in_raw < half_len:
                    header_additions.append(full_block)
                else:
                    footer_additions.append(full_block)

        # Chèn các khối còn thiếu vào đầu và cuối file
        if header_additions:
            preserved_code = "\n\n".join(header_additions) + "\n\n" + preserved_code

        if footer_additions:
            preserved_code = preserved_code + "\n\n" + "\n\n".join(footer_additions)

        return preserved_code.strip()
