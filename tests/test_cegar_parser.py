"""Kiểm thử tính năng bóc tách Phản ví dụ Z3 SMT (CEGAR - arXiv:2506.06923).

Bao phủ các trường hợp:
1. Trích xuất phản ví dụ số âm và dương
2. Trích xuất phản ví dụ đa biến (Initial state vs Failing state)
3. Xử lý an toàn khi output không có phản ví dụ
4. Tích hợp phản ví dụ vào prompt phản hồi giàu ngữ nghĩa (Rich Semantic Diagnostic)
"""

import sys
import unittest
from pathlib import Path

# Đảm bảo đường dẫn gốc của dự án nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.diagnostic_parser import DiagnosticParser, CounterexampleData


class TestCegarParser(unittest.TestCase):
    """Bộ kiểm thử cho bộ bóc tách phản ví dụ SMT."""

    def test_extract_counterexample_negative_numbers(self):
        """Kiểm tra trích xuất phản ví dụ số âm gây vi phạm hậu điều kiện abs_val."""
        dafny_output = """
scratch/test_cegar.dfy(5,0): Error: a postcondition could not be proved on this return path
 Related counterexample:
 WARNING: the following counterexample may be inconsistent or invalid. See dafny.org/dafny/DafnyRef/DafnyRef#sec-counterexamples
 scratch/test_cegar.dfy(5,0): initial state:
 assume -1 == x;
 scratch/test_cegar.dfy(7,10):
 assume -1 == x && -1 == y;
 
  |
5 | {
  | ^

scratch/test_cegar.dfy(2,14): Related location: this is the postcondition that could not be proved
  |
2 |     ensures y >= 0
  |               ^^


Dafny program verifier finished with 0 verified, 1 error
"""
        ce = DiagnosticParser.extract_counterexample(dafny_output)
        self.assertIsNotNone(ce)
        self.assertIsInstance(ce, CounterexampleData)
        self.assertEqual(ce.initial_state.get("x"), "-1")
        self.assertEqual(ce.failing_state.get("y"), "-1")
        self.assertIn("ensures y >= 0", ce.violated_clause)
        self.assertIn("x = -1", ce.description)
        self.assertIn("y = -1", ce.description)

    def test_extract_counterexample_multiple_variables(self):
        """Kiểm tra trích xuất phản ví dụ có nhiều biến đầu vào và biến trung gian."""
        dafny_output = """
test.dfy(12,4): Error: a postcondition could not be proved on this return path
 Related counterexample:
 test.dfy(12,4): initial state:
 assume 10 == a && 0 == b;
 test.dfy(15,8):
 assume 10 == a && 0 == b && -5 == res;

test.dfy(3,10): Related location: this is the postcondition that could not be proved
  |
3 |     ensures res > 0
  |             ^^^^^^^
"""
        ce = DiagnosticParser.extract_counterexample(dafny_output)
        self.assertIsNotNone(ce)
        self.assertEqual(ce.initial_state.get("a"), "10")
        self.assertEqual(ce.initial_state.get("b"), "0")
        self.assertEqual(ce.failing_state.get("res"), "-5")
        self.assertIn("ensures res > 0", ce.violated_clause)

    def test_extract_counterexample_none_when_no_ce(self):
        """Kiểm tra trả về None an toàn khi output Dafny không chứa khối phản ví dụ."""
        dafny_output = """
test.dfy(10,2): Error: syntax error, unexpected token
Dafny program verifier finished with 0 verified, 1 error
"""
        ce = DiagnosticParser.extract_counterexample(dafny_output)
        self.assertIsNone(ce)

    def test_format_diagnostic_feedback_includes_cegar_block(self):
        """Kiểm tra prompt phản hồi cho LLM tự động chèn khối CEGAR khi có phản ví dụ."""
        code = "method Abs(x: int) returns (y: int) ensures y >= 0 { y := x; }"
        dafny_output = """
test.dfy(1,0): Error: a postcondition could not be proved on this return path
 Related counterexample:
 test.dfy(1,0): initial state:
 assume -42 == x;
 test.dfy(1,10):
 assume -42 == x && -42 == y;

test.dfy(1,40): Related location: this is the postcondition that could not be proved
  |
1 | ensures y >= 0
"""
        feedback, cat = DiagnosticParser.format_diagnostic_feedback(code, dafny_output)
        self.assertEqual(cat, "PostconditionViolation")
        self.assertIn("PHẢN VÍ DỤ CỤ THỂ TỪ Z3 SMT SOLVER (CEGAR", feedback)
        self.assertIn("-42", feedback)
        self.assertIn("ensures y >= 0", feedback)

    def test_parse_diagnostics_attaches_counterexample(self):
        """Kiểm tra parse_diagnostics tự động gắn counterexample vào đối tượng DiagnosticError đầu tiên."""
        code = "method Abs(x: int) returns (y: int) ensures y >= 0 { y := x; }"
        dafny_output = """
test.dfy(1,0): Error: a postcondition could not be proved on this return path
 Related counterexample:
 test.dfy(1,0): initial state:
 assume -2 == x;
 test.dfy(1,10):
 assume -2 == x && -2 == y;

test.dfy(1,40): Related location: this is the postcondition that could not be proved
  |
1 | ensures y >= 0
"""
        errors = DiagnosticParser.parse_diagnostics(dafny_output, code)
        self.assertTrue(len(errors) > 0)
        self.assertIsNotNone(errors[0].counterexample)
        self.assertEqual(errors[0].counterexample.initial_state.get("x"), "-2")

    def test_live_dafny_extracts_counterexample(self):
        """Kiểm thử trực tiếp trên engine Dafny 4.x thật để chứng minh khả năng sinh phản ví dụ."""
        from core.dafny_engine import DafnyEngine
        engine = DafnyEngine(timeout_sec=10)
        if not engine.is_available():
            self.skipTest("Dafny CLI không có sẵn.")
        buggy_code = """
method Abs(x: int) returns (y: int)
    ensures y >= 0
{
    y := x;
}
"""
        res = engine.verify(buggy_code, extract_counterexample=True)
        self.assertFalse(res.is_verified)
        self.assertIn("Related counterexample:", res.output)
        ce = DiagnosticParser.extract_counterexample(res.output)
        self.assertIsNotNone(ce)
        self.assertIn("x", ce.initial_state)
        self.assertIn("y >= 0", ce.violated_clause)


if __name__ == "__main__":
    unittest.main()
