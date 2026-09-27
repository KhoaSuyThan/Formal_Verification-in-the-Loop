"""Module phân tích và bóc tách lỗi chẩn đoán từ Dafny / Z3 SMT Solver.

Phân loại lỗi theo hệ thống danh mục (Error Taxonomy):
PostconditionViolation, LoopInvariantViolation, PreconditionViolation, TerminationFailure, OutOfBounds.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DiagnosticError:
    """Thông tin chi tiết về từng lỗi do bộ kiểm định phát hiện."""
    line: Optional[int]
    column: Optional[int]
    error_type: str
    message: str
    raw_snippet: str


class DiagnosticParser:
    """Bộ bóc tách và phân loại lỗi từ output của Dafny."""

    # Từ điển ánh xạ từ khóa lỗi sang phân loại chuẩn của đề tài NCKH
    ERROR_TAXONOMY_MAP = {
        "postcondition might not hold": "PostconditionViolation",
        "invariant might not hold": "LoopInvariantViolation",
        "invariant could not be proved": "LoopInvariantViolation",
        "precondition might not hold": "PreconditionViolation",
        "decreases expression might not decrease": "TerminationFailure",
        "cannot prove termination": "TerminationFailure",
        "index out of range": "OutOfBounds",
        "assertion might not hold": "AssertionViolation",
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
        return "GeneralVerificationFailure"

    @classmethod
    def parse_diagnostics(cls, dafny_output: str) -> List[DiagnosticError]:
        """Bóc tách toàn bộ danh sách lỗi có kèm tọa độ dòng và cột."""
        errors: List[DiagnosticError] = []
        # Pattern bắt định dạng lỗi chuẩn: file.dfy(line,col): Error: message
        pattern = re.compile(r'(?:\.dfy)?\((\d+),(\d+)\):\s*Error:\s*(.+)', re.IGNORECASE)

        for line in dafny_output.splitlines():
            match = pattern.search(line)
            if match:
                line_num = int(match.group(1))
                col_num = int(match.group(2))
                msg = match.group(3).strip()
                category = cls.classify_error(msg)
                errors.append(DiagnosticError(
                    line=line_num,
                    column=col_num,
                    error_type=category,
                    message=msg,
                    raw_snippet=line.strip()
                ))

        return errors

    @classmethod
    def extract_error(cls, dafny_output: str) -> str:
        """Trích xuất chuỗi thông báo lỗi cô đọng để làm ngữ cảnh phản hồi cho LLM."""
        parsed = cls.parse_diagnostics(dafny_output)
        if parsed:
            # Ưu tiên lấy lỗi đầu tiên kèm vị trí và loại lỗi
            top = parsed[0]
            pos = f"Dòng {top.line}, Cột {top.column}" if top.line else "Vị trí không xác định"
            return f"[{top.error_type}] tại {pos}: {top.message}"

        # Nếu không khớp regex tọa độ, gom tối đa 3 dòng chứa từ khóa Error
        error_lines = [line.strip() for line in dafny_output.splitlines() if "Error" in line or "error" in line]
        if error_lines:
            return "\n".join(error_lines[:3])

        # Dự phòng trường hợp output ngắn
        trimmed = dafny_output.strip()
        return trimmed if trimmed else "Lỗi logic không xác định từ bộ giải Dafny/Z3."
