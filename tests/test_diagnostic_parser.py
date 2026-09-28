"""Unit test kiểm thử module DiagnosticParser (Semantic Diagnostic Engine)."""

from core.diagnostic_parser import DiagnosticParser, DiagnosticError


def test_classify_error():
    assert DiagnosticParser.classify_error("Error: this invariant could not be proved on entry") == "LoopInvariantViolation"
    assert DiagnosticParser.classify_error("Error: this invariant could not be proved to be maintained by the loop") == "LoopInvariantViolation"
    assert DiagnosticParser.classify_error("Error: a postcondition could not be proved on this return path") == "PostconditionViolation"
    assert DiagnosticParser.classify_error("Error: index out of range") == "OutOfBounds"
    assert DiagnosticParser.classify_error("Error: LHS of assignment must denote a mutable variable") == "GeneralVerificationFailure"


def test_parse_diagnostics_with_code_context():
    code = (
        "method sum(n: int) returns (s: int)\n"
        "    ensures s >= 0\n"
        "{\n"
        "    var i := 0;\n"
        "    while i <= n\n"
        "        invariant 0 <= i <= n\n"
        "    {\n"
        "        i := i + 1;\n"
        "    }\n"
        "}\n"
    )
    dafny_output = "test.dfy(6,18): Error: this invariant could not be proved to be maintained by the loop\n"

    parsed = DiagnosticParser.parse_diagnostics(dafny_output, code)
    assert len(parsed) == 1
    err = parsed[0]
    assert err.line == 6
    assert err.column == 18
    assert err.error_type == "LoopInvariantViolation"
    assert "invariant 0 <= i <= n" in err.faulty_line_content
    assert "DUY TRÌ SAU THÂN VÒNG LẶP" in err.semantic_hint


def test_format_diagnostic_feedback():
    code = (
        "method sum(n: int) returns (s: int)\n"
        "    ensures s >= 0\n"
        "{\n"
        "    var i := 0;\n"
        "    while i <= n\n"
        "        invariant 0 <= i <= n\n"
        "    {\n"
        "        i := i + 1;\n"
        "    }\n"
        "}\n"
    )
    dafny_output = "test.dfy(6,18): Error: this invariant could not be proved to be maintained by the loop\n"

    feedback, category = DiagnosticParser.format_diagnostic_feedback(code, dafny_output)
    assert category == "LoopInvariantViolation"
    assert ">>> Dòng 6:         invariant 0 <= i <= n" in feedback
    assert "Dòng 5:     while i <= n" in feedback
    assert "HƯỚNG DẪN KHẮC PHỤC NGỮ NGHĨA" in feedback


if __name__ == "__main__":
    test_classify_error()
    test_parse_diagnostics_with_code_context()
    test_format_diagnostic_feedback()
    print("ALL TESTS PASSED!")
