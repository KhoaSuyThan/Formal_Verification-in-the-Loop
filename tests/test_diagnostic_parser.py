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


def test_extract_forall_prefix_invariant():
    clause1 = "ensures r == -1 ==> forall i :: 0 <= i < a.Length ==> a[i] != target"
    inv1 = DiagnosticParser.extract_forall_prefix_invariant(clause1)
    assert inv1 == "invariant forall j :: 0 <= j < i ==> a[j] != target"

    clause2 = "ensures b == (forall i : int :: i >= 0 && i < |l| ==> l[i] < t)"
    inv2 = DiagnosticParser.extract_forall_prefix_invariant(clause2)
    assert inv2 == "invariant forall j :: 0 <= j < i ==> l[j] < t"

    clause3 = "ensures forall i : int :: i >= 0 && i < |l| ==> l[i] <= result"
    inv3 = DiagnosticParser.extract_forall_prefix_invariant(clause3)
    assert inv3 == "invariant forall j :: 0 <= j < i ==> l[j] <= result"
    print("[OK] Test extract_forall_prefix_invariant: PASS")


def test_actionable_directives():
    # 1. Test exists directive
    hint_exists = DiagnosticParser.generate_semantic_hint(
        "PostconditionViolation",
        "a postcondition could not be proved on this return path",
        "{",
        "",
        "ensures exists i : int :: i >= 0 && i < |l| && l[i] == result"
    )
    assert "CHÈN INVARIANT TỒN TẠI" in hint_exists
    assert "invariant exists j :: 0 <= j < i && l[j] ==" in hint_exists

    # 2. Test pure function directive
    hint_pure = DiagnosticParser.generate_semantic_hint(
        "PostconditionViolation",
        "a postcondition could not be proved on this return path",
        "{",
        "",
        "ensures result == fib(n)"
    )
    assert "ĐỒNG BỘ BẤT BIẾN VỚI HÀM fib" in hint_pure
    assert "invariant a == fib(i)" in hint_pure

    # 3. Test on entry directive
    hint_entry = DiagnosticParser.generate_semantic_hint(
        "LoopInvariantViolation",
        "this invariant could not be proved on entry",
        "invariant cur_a > 0",
        ""
    )
    assert "XỬ LÝ SỐ ÂM" in hint_entry
    assert "var cur_a := if a < 0 then -a else a" in hint_entry

    # 4. Test on entry with exists invariant
    hint_entry_exists = DiagnosticParser.generate_semantic_hint(
        "LoopInvariantViolation",
        "this invariant could not be proved on entry",
        "invariant exists j :: 0 <= j < i && l[j] == result",
        ""
    )
    assert "KHỞI TẠO BIẾN LẶP" in hint_entry_exists
    assert "var i := 1;" in hint_entry_exists
    print("[OK] Test actionable directives: PASS")


if __name__ == "__main__":
    test_classify_error()
    test_parse_diagnostics_with_code_context()
    test_format_diagnostic_feedback()
    test_extract_forall_prefix_invariant()
    test_actionable_directives()
    print("ALL TESTS PASSED!")

