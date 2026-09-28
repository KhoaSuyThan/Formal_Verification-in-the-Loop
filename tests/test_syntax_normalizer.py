"""Unit test kiem thu module SyntaxNormalizer."""

from core.syntax_normalizer import SyntaxNormalizer


def test_fix_duplicate_out_param():
    code = """method below_threshold(l : seq<int>, t : int) returns (b : bool)
    ensures b == true
{
    var b := true;
    var i := 0;
    b := false;
}
"""
    result = SyntaxNormalizer.fix_duplicate_out_params(code)
    assert "var b :=" not in result, f"var b van con: {result}"
    assert "b := true;" in result
    assert "var i := 0;" in result  # bien khac khong bi anh huong
    print("[OK] Test fix_duplicate_out_param: PASS")


def test_fix_return_expr():
    code = """method has_close(numbers: seq<real>) returns (flag : bool)
    ensures flag == true
{
    flag := true;
    return flag;
}
"""
    result = SyntaxNormalizer.fix_return_expr(code)
    assert "return flag;" not in result
    assert "return;" in result
    print("[OK] Test fix_return_expr: PASS")


def test_fix_return_complex_expr():
    code = """method truncate(x: real) returns (d : real)
    ensures d >= 0.0
{
    return x - (x.Floor as real);
}
"""
    result = SyntaxNormalizer.fix_return_expr(code)
    assert "return x -" not in result
    assert "d := x - (x.Floor as real);" in result
    assert "return;" in result
    print("[OK] Test fix_return_complex_expr: PASS")


def test_fix_ternary():
    code = """method iscube(n: int) returns (r: bool)
    ensures r == true
{
    r := n >= 0 ? cube_root(n) == n : cube_root(-n) == -n;
}
"""
    result = SyntaxNormalizer.fix_ternary_operator(code)
    assert "?" not in result.split("ensures")[1] if "ensures" in result else "?" not in result
    assert "if n >= 0" in result
    assert "} else {" in result
    print("[OK] Test fix_ternary: PASS")


def test_fix_seq_assignment():
    code = """method sort(s: seq<int>) returns (sorted: seq<int>)
{
    var l := s;
    l[i] := l[i + 1];
    l[i + 1] := temp;
}
"""
    result = SyntaxNormalizer.fix_seq_assignment(code)
    assert "l[i] :=" not in result
    assert "l := l[i := l[i + 1]];" in result
    assert "l := l[i + 1 := temp];" in result
    print("[OK] Test fix_seq_assignment: PASS")


def test_normalize_combined():
    code = """method below_threshold(l : seq<int>, t : int) returns (b : bool)
    ensures b == (forall i : int :: i >= 0 && i < |l| ==> l[i] < t)
{
    var b := true;
    var i := 0;
    while (i < |l|)
    {
        if (l[i] >= t) {
            b := false;
        }
        i := i + 1;
    }
    return b;
}
"""
    result = SyntaxNormalizer.normalize(code)
    assert "var b :=" not in result, f"var b van con: {result}"
    assert "return b;" not in result
    assert "return;" in result or "return b;" not in result
def test_fix_misplaced_loop_invariants():
    code = """method max_element(l : seq<int>) returns (result : int)
{
    var max := l[0];
    var i := 1;
    while i < |l|
    {
        invariant 1 <= i <= |l|;
        invariant forall j :: 0 <= j < i ==> l[j] <= max;
        if l[i] > max {
            max := l[i];
        }
        i := i + 1;
    }
    result := max;
}
"""
    result = SyntaxNormalizer.normalize(code)
    assert "invariant 1 <= i <= |l|;" not in result
    assert "invariant 1 <= i <= |l|" in result
    assert "invariant forall j :: 0 <= j < i ==> l[j] <= max" in result
    # Invariant phải nằm TRƯỚC dấu {
    while_pos = result.find("while i < |l|")
    inv_pos = result.find("invariant 1 <= i <= |l|")
    brace_pos = result.find("{", while_pos + len("while i < |l|"))
    assert while_pos < inv_pos < brace_pos, "Invariant phải nằm giữa while và dấu {"
    print("[OK] Test fix_misplaced_loop_invariants: PASS")


def test_fix_if_then_in_method():
    code = """function abs(val : real): real
{
  if (val < 0.0) then
    -val
  else
    val
}
// pure-end

method has_close_elements(numbers: seq<real>, threshold: real) returns (flag : bool)
{
  var n := |numbers|;
  if n <= 1 then
    flag := false;

    return;

  var i := 0;
  while i < n
  {
    if abs(numbers[i]) < threshold then
      flag := true;
      return;
    i := i + 1;
  }
}
"""
    result = SyntaxNormalizer.fix_if_then_in_method(code)
    # Hàm function abs phải giữ nguyên biểu thức if ... then
    assert "if (val < 0.0) then" in result, "Function pure expression không được bị thay đổi!"
    # Method phải được chuyển sang khối ngoặc nhọn
    assert "if n <= 1 {" in result, f"if n <= 1 then chưa được chuyển: {result}"
    assert "if abs(numbers[i]) < threshold {" in result, f"if trong loop chưa được chuyển: {result}"
    assert "if n <= 1 then" not in result
    print("[OK] Test fix_if_then_in_method: PASS")


def test_fix_missing_semicolon():
    code = """method has_close_elements(numbers: seq<real>) returns (flag : bool)
{
  var n := |numbers|;
  if n <= 1 {
    flag := false
  }
  else {
    var i := 0
    return
  }
}
"""
    result = SyntaxNormalizer.fix_missing_semicolon(code)
    assert "flag := false;" in result, f"flag := false; chưa có chấm phẩy: {result}"
    assert "var i := 0;" in result, f"var i := 0; chưa có chấm phẩy: {result}"
    assert "return;" in result, f"return; chưa có chấm phẩy: {result}"
    print("[OK] Test fix_missing_semicolon: PASS")


if __name__ == "__main__":
    test_fix_duplicate_out_param()
    test_fix_return_expr()
    test_fix_return_complex_expr()
    test_fix_ternary()
    test_fix_seq_assignment()
    test_fix_misplaced_loop_invariants()
    test_fix_if_then_in_method()
    test_fix_missing_semicolon()
    test_normalize_combined()
    print("All SyntaxNormalizer tests passed!")


