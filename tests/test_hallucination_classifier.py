"""Unit test cho module core/hallucination_classifier.py."""

import unittest
from core.hallucination_classifier import (
    FormalHallucinationType,
    classify_hallucination,
    HALLUCINATION_META
)


class TestHallucinationClassifier(unittest.TestCase):
    """Kiểm thử tính đúng đắn của logic phân loại ảo giác hình thức H0 - H4."""

    def test_h0_zero_hallucination(self):
        """Kiểm tra khi Z3 xác minh thành công thì phải là H0 Zero-Hallucination."""
        res = classify_hallucination(is_success=True)
        self.assertEqual(res["code"], FormalHallucinationType.H0_ZERO)
        self.assertIn("H0", res["badge"])
        self.assertEqual(res["color"], "#22c55e")

    def test_h1_spec_tampering(self):
        """Kiểm tra khi bị SpecLocker bắt lỗi can thiệp đặc tả thì là H1."""
        res = classify_hallucination(is_success=False, is_tampered=True)
        self.assertEqual(res["code"], FormalHallucinationType.H1_SPEC_TAMPER)
        self.assertIn("H1", res["badge"])
        self.assertEqual(res["color"], "#ef4444")

    def test_h2_inductive_fallacy(self):
        """Kiểm tra khi vi phạm Invariant thì được phân loại vào H2."""
        err_msg = "Error: a loop invariant might not hold on entry (line 25)"
        res = classify_hallucination(is_success=False, error_message=err_msg)
        self.assertEqual(res["code"], FormalHallucinationType.H2_INDUCTIVE)
        self.assertIn("H2", res["badge"])
        self.assertEqual(res["color"], "#f97316")

    def test_h3_boundary_overflow(self):
        """Kiểm tra khi lỗi Out of Bounds hoặc chia 0 thì được phân loại vào H3."""
        err_msg = "Error: index out of bounds on array access a[i]"
        res = classify_hallucination(is_success=False, error_message=err_msg)
        self.assertEqual(res["code"], FormalHallucinationType.H3_BOUNDARY)
        self.assertIn("H3", res["badge"])
        self.assertEqual(res["color"], "#eab308")

    def test_h4_semantic_drift(self):
        """Kiểm tra khi vi phạm hậu điều kiện ensures thì được phân loại vào H4."""
        err_msg = "Error: a postcondition might not hold on this return path (ensures a[k] <= max)"
        res = classify_hallucination(is_success=False, error_message=err_msg)
        self.assertEqual(res["code"], FormalHallucinationType.H4_SEMANTIC_DRIFT)
        self.assertIn("H4", res["badge"])
        self.assertEqual(res["color"], "#a855f7")

    def test_meta_integrity(self):
        """Đảm bảo tất cả 5 nhóm đều có đủ metadata bắt buộc."""
        for code in [
            FormalHallucinationType.H0_ZERO,
            FormalHallucinationType.H1_SPEC_TAMPER,
            FormalHallucinationType.H2_INDUCTIVE,
            FormalHallucinationType.H3_BOUNDARY,
            FormalHallucinationType.H4_SEMANTIC_DRIFT
        ]:
            self.assertIn(code, HALLUCINATION_META)
            meta = HALLUCINATION_META[code]
            self.assertTrue(all(k in meta for k in ["code", "badge", "name", "color", "description"]))


if __name__ == "__main__":
    unittest.main()
