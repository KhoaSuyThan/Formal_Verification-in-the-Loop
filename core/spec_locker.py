"""Module khóa cứng đặc tả toán học (Spec-Locking Protocol).

Sử dụng mã băm SHA-256 trên các mệnh đề ensures để ngăn LLM nới lỏng hoặc thay đổi đặc tả.
"""

import hashlib
import re


class SpecLocker:
    """Quản lý trích xuất và xác thực tính toàn vẹn của mệnh đề ensures trong Dafny."""

    @staticmethod
    def extract_ensures(dafny_code: str) -> str:
        """Trích xuất và chuẩn hóa tất cả các mệnh đề ensures trong mã nguồn Dafny.

        - Loại bỏ comment (// ... và /* ... */).
        - Chuẩn hóa khoảng trắng và dấu chấm phẩy để không bị lệch băm do định dạng.
        """
        # Loại bỏ block comment /* ... */
        clean_code = re.sub(r'/\*.*?\*/', '', dafny_code, flags=re.DOTALL)
        # Loại bỏ line comment // ...
        clean_code = re.sub(r'//.*', '', clean_code)

        # Bắt từng mệnh đề ensures: từ sau từ khóa ensures đến dấu chấm phẩy hoặc ký tự xuống dòng / mở ngoặc nhọn
        # Hỗ trợ cả trường hợp kết thúc bằng ';' hoặc xuống dòng
        pattern = re.compile(r'\bensures\s+([^;{\n]+)(?:;)?', re.MULTILINE)
        matches = pattern.findall(clean_code)

        normalized_clauses = []
        for m in matches:
            # Loại bỏ khoảng trắng và dấu chấm phẩy nếu còn sót
            norm = re.sub(r'[\s;]+', '', m)
            if norm:
                normalized_clauses.append(norm)

        # Nối lại theo thứ tự xác định để tạo chữ ký chuỗi duy nhất
        return ";".join(normalized_clauses)

    @classmethod
    def get_hash(cls, dafny_code: str) -> str:
        """Tính mã băm SHA-256 đại diện cho tập mệnh đề ensures."""
        ensures_str = cls.extract_ensures(dafny_code)
        return hashlib.sha256(ensures_str.encode("utf-8")).hexdigest()

    @classmethod
    def is_valid(cls, original_hash: str, new_code: str) -> bool:
        """Kiểm tra mã nguồn mới có bảo toàn đúng đặc tả ensures ban đầu hay không."""
        return cls.get_hash(new_code) == original_hash
