"""Module khóa cứng đặc tả toán học (Spec-Locking Protocol).

Sử dụng mã băm SHA-256 trên các mệnh đề ensures để ngăn LLM nới lỏng hoặc thay đổi đặc tả.
"""

import hashlib
import re


from typing import Optional, Set


class SpecLocker:
    """Quản lý trích xuất và xác thực tính toàn vẹn của mệnh đề ensures trong Dafny."""

    @staticmethod
    def extract_clauses(dafny_code: str) -> Set[str]:
        """Trích xuất tập hợp tất cả các mệnh đề ensures đã chuẩn hóa trong mã nguồn Dafny.

        - Loại bỏ comment (// ... và /* ... */).
        - Chuẩn hóa khoảng trắng và dấu chấm phẩy để không bị sai lệch do định dạng.
        """
        # Loại bỏ block comment /* ... */
        clean_code = re.sub(r'/\*.*?\*/', '', dafny_code, flags=re.DOTALL)
        # Loại bỏ line comment // ...
        clean_code = re.sub(r'//.*', '', clean_code)

        # Bắt từng mệnh đề ensures: từ sau từ khóa ensures đến dấu chấm phẩy hoặc ký tự xuống dòng / mở ngoặc nhọn
        pattern = re.compile(r'\bensures\s+([^;{\n]+)(?:;)?', re.MULTILINE)
        matches = pattern.findall(clean_code)

        clauses = set()
        for m in matches:
            norm = re.sub(r'[\s;]+', '', m)
            if norm:
                clauses.add(norm)
        return clauses

    @classmethod
    def extract_ensures(cls, dafny_code: str) -> str:
        """Trích xuất và chuẩn hóa tất cả các mệnh đề ensures nối thành chuỗi theo thứ tự."""
        clauses = sorted(list(cls.extract_clauses(dafny_code)))
        return ";".join(clauses)

    @classmethod
    def get_hash(cls, dafny_code: str) -> str:
        """Tính mã băm SHA-256 đại diện cho tập mệnh đề ensures."""
        ensures_str = cls.extract_ensures(dafny_code)
        return hashlib.sha256(ensures_str.encode("utf-8")).hexdigest()

    @classmethod
    def is_valid(cls, original_hash: str, new_code: str, raw_spec: Optional[str] = None) -> bool:
        """Kiểm tra mã nguồn mới có bảo toàn đúng đặc tả ensures ban đầu hay không.

        - Nếu có raw_spec: Kiểm tra tập mệnh đề gốc BẮT BUỘC là tập con của mã mới (Subset Preservation).
          Mô hình không được phép xóa/sửa bất kỳ ensures gốc nào, nhưng được phép viết thêm helper lemma/method.
        - Nếu không có raw_spec: Fallback so sánh mã băm SHA-256 trực tiếp.
        """
        if raw_spec:
            orig_clauses = cls.extract_clauses(raw_spec)
            new_clauses = cls.extract_clauses(new_code)
            # Toàn bộ ensures gốc bắt buộc phải có mặt đầy đủ trong mã mới
            return orig_clauses.issubset(new_clauses)

        return cls.get_hash(new_code) == original_hash
