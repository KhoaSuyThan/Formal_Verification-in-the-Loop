"""Module phân loại ảo giác mã nguồn hình thức (Formal Code Hallucination Classifier).

Căn cứ học thuật:
- Nature (HSSC 2024): AI hallucination: towards a comprehensive classification of distorted information.
- Z3 SMT Solver & Dafny 4.x Verification Diagnostics.
"""

from typing import Dict, Any, Optional


class FormalHallucinationType:
    """Định nghĩa 5 nhóm phân loại ảo giác hình thức chuẩn mực."""
    H0_ZERO = "H0"            # Không ảo giác (Z3 Verified 100%)
    H1_SPEC_TAMPER = "H1"     # Can thiệp làm lỏng/xóa bỏ đặc tả đề bài
    H2_INDUCTIVE = "H2"       # Ngụy biện quy nạp (vi phạm Invariant)
    H3_BOUNDARY = "H3"        # Vi phạm biên mảng / chỉ số / tràn số
    H4_SEMANTIC_DRIFT = "H4"  # Trôi dạt ngữ nghĩa (vi phạm hậu điều kiện ensures)


# Ánh xạ nhãn hiển thị trực quan kèm biểu tượng và mô tả học thuật
HALLUCINATION_META: Dict[str, Dict[str, str]] = {
    FormalHallucinationType.H0_ZERO: {
        "code": "H0",
        "badge": "✅ H0: Zero-Hallucination",
        "name": "Tuyệt Đối Không Ảo Giác",
        "color": "#22c55e",
        "description": "Mã nguồn được Z3 SMT Solver chứng minh toán học đúng đắn 100% trên toàn bộ không gian biến."
    },
    FormalHallucinationType.H1_SPEC_TAMPER: {
        "code": "H1",
        "badge": "⚠️ H1: Can Thiệp Đặc Tả",
        "name": "Can Thiệp Đặc Tả (Spec-Tampering)",
        "color": "#ef4444",
        "description": "Mô hình tự ý xóa bỏ, bình luận hóa hoặc nới lỏng tiền/hậu điều kiện requires/ensures của đề bài."
    },
    FormalHallucinationType.H2_INDUCTIVE: {
        "code": "H2",
        "badge": "🌀 H2: Ngụy Biện Quy Nạp",
        "name": "Ngụy Biện Quy Nạp (Inductive Fallacy)",
        "color": "#f97316",
        "description": "Bất biến vòng lặp (invariant) bị sai bước cơ sở (base case) hoặc không bảo toàn qua bước quy nạp."
    },
    FormalHallucinationType.H3_BOUNDARY: {
        "code": "H3",
        "badge": "⚡ H3: Vi Phạm Biên/Chỉ Số",
        "name": "Vi Phạm Biên (Boundary Overflow)",
        "color": "#eab308",
        "description": "Vi phạm an toàn bộ nhớ: truy xuất chỉ số vượt kích thước (out of bounds), chỉ số âm hoặc chia cho 0."
    },
    FormalHallucinationType.H4_SEMANTIC_DRIFT: {
        "code": "H4",
        "badge": "🌊 H4: Trôi Dạt Ngữ Nghĩa",
        "name": "Trôi Dạt Ngữ Nghĩa (Semantic Drift)",
        "color": "#a855f7",
        "description": "Code có thể chạy được ca mẫu nhưng vi phạm hậu điều kiện tổng quát (ensures) trong không gian vô hạn."
    }
}


def classify_hallucination(
    is_success: bool,
    is_tampered: bool = False,
    error_message: Optional[str] = None
) -> Dict[str, str]:
    """Phân loại kết quả kiểm định thành một trong 5 nhóm ảo giác hình thức H0 - H4.
    
    Args:
        is_success: Kết quả Z3 xác minh thành công hay không.
        is_tampered: Cờ phát hiện vi phạm băm toàn vẹn đặc tả từ SpecLocker.
        error_message: Chuỗi thông báo lỗi bóc tách từ trình biên dịch Dafny/Z3.
        
    Returns:
        Dict chứa 'code', 'badge', 'name', 'color', và 'description'.
    """
    # 1. Nhóm H0: Chứng minh toán học thành công 100%
    if is_success:
        return HALLUCINATION_META[FormalHallucinationType.H0_ZERO]

    # 2. Nhóm H1: Xâm phạm đặc tả đề bài (SpecLocker bắt bằng băm SHA-256)
    if is_tampered:
        return HALLUCINATION_META[FormalHallucinationType.H1_SPEC_TAMPER]

    err = (error_message or "").lower()

    # 3. Nhóm H2: Sai bất biến quy nạp vòng lặp
    if "invariant" in err:
        return HALLUCINATION_META[FormalHallucinationType.H2_INDUCTIVE]

    # 4. Nhóm H3: Lỗi biên, truy xuất chỉ số ngoài mảng, chia cho 0
    if any(k in err for k in ["out of bounds", "index", "indices", "division by zero", "divisor"]):
        return HALLUCINATION_META[FormalHallucinationType.H3_BOUNDARY]

    # 5. Nhóm H4: Mặc định vi phạm hậu điều kiện ensures hoặc assertion logic
    return HALLUCINATION_META[FormalHallucinationType.H4_SEMANTIC_DRIFT]
