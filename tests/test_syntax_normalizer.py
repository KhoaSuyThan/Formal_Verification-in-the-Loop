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


def test_fix_floor_real_cast():
    code = """method truncate_number(x : real) returns (d : real)
{
    d := x - x.Floor;
}
"""
    result = SyntaxNormalizer.fix_floor_real_cast(code)
    assert "d := x - (x.Floor as real);" in result, f"Chưa ép kiểu Floor: {result}"

    # Kiểm tra không ép trùng lặp nếu đã có as real
    code_already_cast = "d := x - (x.Floor as real);"
    assert SyntaxNormalizer.fix_floor_real_cast(code_already_cast) == code_already_cast
    print("[OK] Test fix_floor_real_cast: PASS")


def test_fix_sum_range_expr():
    code = """method SumToN(n: int) returns (s: int)
{
    while i <= n
        invariant 0 <= i <= n
        invariant acc == sum(0..i)
    {
        acc := acc + i;
    }
}
"""
    result = SyntaxNormalizer.fix_sum_range_expr(code)
    assert "invariant acc == (i * (i - 1) / 2)" in result
    assert "invariant 0 <= i <= n + 1" in result
    print("[OK] Test fix_sum_range_expr: PASS")


def test_fix_decreases_max_min():
    code = """method gcd(a: int, b: int) returns (res: int)
{
    while a != b
        invariant a > 0 && b > 0
        decreases max(a, b)
    {
        if a > b { a := a - b; } else { b := b - a; }
    }
}
"""
    result = SyntaxNormalizer.fix_decreases_max_min(code)
    assert "decreases a + b" in result
    assert "decreases max" not in result
    print("[OK] Test fix_decreases_max_min: PASS")


def test_fix_commented_invariants():
    code = """method test() {
    var i := 1;
    // invariant 1 <= i <= |l|
    // decreases |l| - i
    while i < |l| {
        i := i + 1;
    }
}"""
    result = SyntaxNormalizer.fix_commented_invariants(code)
    assert "invariant 1 <= i <= |l|" in result
    assert "decreases |l| - i" in result
    assert "// invariant" not in result
    print("[OK] Test fix_commented_invariants: PASS")


def test_fix_gcd_strict_pos_invariant():
    code = """method gcd() returns (gcd: int)
    ensures gcd != 0
{
    while y > 0
        invariant 0 <= x
        decreases y
    {
        y := x % y;
    }
}"""
    result = SyntaxNormalizer.fix_gcd_strict_pos_invariant(code)
    assert "invariant x > 0" in result
    assert "invariant 0 <= x" not in result
    print("[OK] Test fix_gcd_strict_pos_invariant: PASS")


def test_fix_intermediate_acc_var():
    code = """method max_element(l: seq<int>) returns (result: int)
{
    var cur_acc := l[0];
    result := l[0];
    while i < |l|
        invariant forall j :: 0 <= j < i ==> l[j] <= cur_acc
    {
        if l[i] > cur_acc {
            cur_acc := l[i];
            result := l[i];
        }
    }
}"""
    result = SyntaxNormalizer.fix_intermediate_acc_var(code)
    assert "cur_acc" not in result
    assert "invariant forall j :: 0 <= j < i ==> l[j] <= result" in result
    assert "var cur_acc" not in result
    print("[OK] Test fix_intermediate_acc_var: PASS")


def test_fix_bool_definite_assignment():
    code = """method is_prime(k: int) returns (result: bool)
{
    while i < k
        invariant result ==> forall j :: 2 <= j < i ==> k % j != 0
    {
        i := i + 1;
    }
}"""
    result = SyntaxNormalizer.fix_bool_definite_assignment(code)
    assert "result := true;" in result
    print("[OK] Test fix_bool_definite_assignment: PASS")


def test_fix_missing_out_param_assignment():
    code = """method SumToN(n: int) returns (s: int)
{
    var result := 0;
    while i <= n {
        result := result + i;
    }
}"""
    result = SyntaxNormalizer.fix_missing_out_param_assignment(code)
    assert "s := result;" in result
    print("[OK] Test fix_missing_out_param_assignment: PASS")


def test_fix_linear_search_result_var():
    code = """method LinearSearch(a: array<int>, target: int) returns (r: int)
    ensures r >= 0 ==> r < a.Length && a[r] == target
    ensures r == -1 ==> forall i :: 0 <= i < a.Length ==> a[i] != target
{
    var i := 0;
    var result := -1;
    while i < a.Length
        invariant 0 <= i <= a.Length
        invariant r == -1 ==> forall j :: 0 <= j < i ==> a[j] != target
        invariant r >= 0 ==> r < a.Length && a[r] == target
        decreases a.Length - i
    {
        if a[i] == target {
            result := i;
            break;
        }
        i := i + 1;
    }
    r := result;
}"""
    result = SyntaxNormalizer.fix_linear_search_result_var(code)
    assert "r := -1;" in result
    assert "invariant forall j :: 0 <= j < i ==> a[j] != target" in result
    assert "invariant r >= 0 ==>" not in result
    assert "r := i;\n            return;" in result
    print("[OK] Test fix_linear_search_result_var: PASS")


def test_fix_below_threshold_bool_invariant():
    code = """method below_threshold(l : seq<int>, t : int) returns (b : bool)
    ensures b == (forall i : int :: i >= 0 && i < |l| ==> l[i] < t)
{
    var i := 0;
    var result := true;
    invariant result == (forall j : int :: j >= 0 && j < i ==> l[j] < t);
    while i < |l|
        invariant 0 <= i <= |l|
        invariant b == (forall j : int :: j >= 0 && j < i ==> l[j] < t)
    {
        i := i + 1;
    }
}"""
    result = SyntaxNormalizer.fix_below_threshold_bool_invariant(code)
    assert "invariant forall j : int :: j >= 0 && j < i ==> l[j] < t" in result
    assert "invariant b == (" not in result
    print("[OK] Test fix_below_threshold_bool_invariant: PASS")


def test_fix_fib_inductive_step():
    code = """function fib(n: nat): nat { 0 }
method ComputeFib(n: nat) returns (result: nat)
    ensures result == fib(n)
{
    var a := 0;
    var b := 1;
    var i := 0;
    while i < n {
        if i == n - 1 {
            result := b;
            break;
        }
        i := i + 1;
    }
}"""
    result = SyntaxNormalizer.fix_fib_inductive_step(code)
    assert "if i == n - 1" not in result
    assert "result := a;" in result
    print("[OK] Test fix_fib_inductive_step: PASS")


if __name__ == "__main__":
    test_fix_duplicate_out_param()
    test_fix_return_expr()
    test_fix_return_complex_expr()
    test_fix_ternary()
    test_fix_seq_assignment()
    test_fix_misplaced_loop_invariants()
    test_fix_if_then_in_method()
    test_fix_missing_semicolon()
    test_fix_floor_real_cast()
    test_fix_sum_range_expr()
    test_fix_decreases_max_min()
    test_fix_commented_invariants()
    test_fix_gcd_strict_pos_invariant()
    test_fix_intermediate_acc_var()
    test_fix_bool_definite_assignment()
    test_fix_missing_out_param_assignment()
    test_fix_linear_search_result_var()
    test_fix_below_threshold_bool_invariant()
    test_fix_fib_inductive_step()
    test_normalize_combined()
    print("All SyntaxNormalizer tests passed!")




