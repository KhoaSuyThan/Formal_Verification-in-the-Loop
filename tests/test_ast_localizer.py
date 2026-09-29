"""Unit test cho module ASTLocalizer."""

from core.ast_localizer import ASTLocalizer


def test_extract_and_patch_invariants():
    code = """method max_element(l : seq<int>) returns (result : int)
    requires |l| > 0
    ensures forall i : int :: i >= 0 && i < |l| ==> l[i] <= result
    ensures exists i : int :: i >= 0 && i < |l| && l[i] == result
{
    var i := 1;
    result := l[0];
    while i < |l|
        invariant 1 <= i <= |l|
        decreases |l| - i
    {
        if l[i] > result {
            result := l[i];
        }
        i := i + 1;
    }
}
"""
    struct = ASTLocalizer.extract_loop_structure(code)
    assert struct is not None
    assert struct["while_guard"] == "while i < |l|"
    assert len(struct["invariants"]) == 2
    assert "invariant 1 <= i <= |l|" in struct["invariants"][0]

    # Vá invariants mới
    new_invariants = [
        "invariant 1 <= i <= |l|",
        "invariant forall j :: 0 <= j < i ==> l[j] <= result",
        "invariant exists j :: 0 <= j < i && l[j] == result",
        "decreases |l| - i"
    ]
    patched = ASTLocalizer.patch_loop_invariants(code, new_invariants)
    assert "invariant exists j :: 0 <= j < i && l[j] == result" in patched
    assert "var i := 1;" in patched
    assert "if l[i] > result {" in patched
    print("[OK] Test extract_and_patch_invariants: PASS")


def test_inject_intermediate_assert():
    code = """method sum_to_n(n: int) returns (s: int)
    requires n >= 0
    ensures s >= 0
{
    var i := 0;
    s := 0;
    while i < n
        invariant 0 <= i <= n
    {
        s := s + i;
        i := i + 1;
    }
}
"""
    injected = ASTLocalizer.inject_intermediate_assert(code, "assert i == n")
    assert "assert i == n;" in injected
    # Vị trí assert phải nằm sau thân while và trước dấu đóng ngoặc } cuối
    while_pos = injected.find("while i < n")
    assert_pos = injected.find("assert i == n;")
    assert while_pos < assert_pos
    print("[OK] Test inject_intermediate_assert: PASS")


if __name__ == "__main__":
    test_extract_and_patch_invariants()
    test_inject_intermediate_assert()
    print("ALL ASTLocalizer TESTS PASSED!")
