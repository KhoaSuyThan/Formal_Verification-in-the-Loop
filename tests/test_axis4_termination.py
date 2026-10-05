"""Unit test kiểm thử Bảo chứng dừng (Trục 4) và Suy luận modifies.

Kiểm thử:
- SyntaxNormalizer.infer_loop_decreases: suy luận ranking function cho 5 mẫu hình vòng lặp
- SyntaxNormalizer.infer_array_modifies: suy luận modifies cho method thao tác mảng
- DiagnosticParser.generate_semantic_hint: các hint cho TerminationFailure
"""

from core.diagnostic_parser import DiagnosticParser
from core.syntax_normalizer import SyntaxNormalizer


def test_infer_decreases_forward_loop():
    """Kiểm tra suy luận decreases n - i cho vòng lặp tiến i < n."""
    code = """method SumToN(n: int) returns (s: int)
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
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases n - i" in result, f"Thiếu decreases n - i: {result}"
    # Đảm bảo invariant vẫn còn
    assert "invariant 0 <= i <= n" in result


def test_infer_decreases_forward_seq_length():
    """Kiểm tra suy luận decreases |s| - i cho vòng lặp duyệt sequence."""
    code = """method FindMax(s: seq<int>) returns (max_val: int)
    requires |s| > 0
{
    var i := 0;
    while i < |s|
        invariant 0 <= i <= |s|
    {
        i := i + 1;
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases |s| - i" in result, f"Thiếu decreases |s| - i: {result}"


def test_infer_decreases_backward_loop():
    """Kiểm tra suy luận decreases i cho vòng lặp lùi i > 0."""
    code = """method CountDown(n: int)
    requires n >= 0
{
    var i := n;
    while i > 0
        invariant i >= 0
    {
        i := i - 1;
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases i" in result, f"Thiếu decreases i: {result}"


def test_infer_decreases_binary_search():
    """Kiểm tra suy luận decreases high - low cho tìm kiếm nhị phân."""
    code = """method BinarySearch(a: seq<int>, key: int) returns (index: int)
{
    var low := 0;
    var high := |a|;
    while low < high
        invariant 0 <= low <= high <= |a|
    {
        var mid := (low + high) / 2;
        if a[mid] < key {
            low := mid + 1;
        } else {
            high := mid;
        }
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases high - low" in result, f"Thiếu decreases high - low: {result}"


def test_infer_decreases_euclid_mod():
    """Kiểm tra suy luận decreases b cho thuật toán Euclid với phép mod (while b > 0)."""
    code = """method Gcd(m: int, n: int) returns (res: int)
    requires m >= 0 && n > 0
{
    var a := m;
    var b := n;
    while b > 0
        invariant b >= 0
    {
        var temp := b;
        b := a % b;
        a := temp;
    }
    return a;
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases b" in result, f"Thiếu decreases b: {result}"


def test_infer_decreases_euclid_sub():
    """Kiểm tra suy luận decreases a + b cho thuật toán Euclid phép trừ (while a != b)."""
    code = """method GcdSub(x: int, y: int) returns (res: int)
    requires x > 0 && y > 0
{
    var a := x;
    var b := y;
    while a != b
        invariant a > 0 && b > 0
    {
        if a > b {
            a := a - b;
        } else {
            b := b - a;
        }
    }
    return a;
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases a + b" in result, f"Thiếu decreases a + b: {result}"


def test_no_duplicate_decreases():
    """Kiểm tra không chèn trùng nếu vòng lặp đã có decreases."""
    code = """method LoopWithDecreases(n: int)
{
    var i := 0;
    while i < n
        invariant 0 <= i <= n
        decreases n - i
    {
        i := i + 1;
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert result.count("decreases") == 1, f"Có quá nhiều decreases được sinh ra: {result}"


def test_no_decreases_complex_condition():
    """Kiểm tra điều kiện phức hợp (&&, ||) không sinh decreases sai."""
    code = """method ComplexLoop(n: int, m: int)
{
    var i := 0;
    while i < n && i < m
        invariant i >= 0
    {
        i := i + 1;
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases" not in result, f"Không nên chèn decreases cho điều kiện phức hợp: {result}"


def test_infer_modifies_array():
    """Kiểm tra tự động chèn modifies a khi method thao tác in-place trên array."""
    code = """method ZeroOut(a: array<int>)
    requires a != null
    ensures forall k :: 0 <= k < a.Length ==> a[k] == 0
{
    var i := 0;
    while i < a.Length
    {
        a[i] := 0;
        i := i + 1;
    }
}
"""
    result = SyntaxNormalizer.infer_array_modifies(code)
    assert "modifies a" in result, f"Thiếu modifies a: {result}"


def test_no_modifies_seq():
    """Kiểm tra không chèn modifies khi tham số là immutable sequence seq<T>."""
    code = """method ReadSeq(s: seq<int>) returns (res: int)
{
    var i := 0;
    return |s|;
}
"""
    result = SyntaxNormalizer.infer_array_modifies(code)
    assert "modifies" not in result, f"Không được chèn modifies cho seq: {result}"


def test_no_duplicate_modifies():
    """Kiểm tra không chèn trùng nếu method đã có modifies a."""
    code = """method SetFirst(a: array<int>)
    modifies a
{
    if a.Length > 0 {
        a[0] := 42;
    }
}
"""
    result = SyntaxNormalizer.infer_array_modifies(code)
    assert result.count("modifies") == 1, f"Trùng lặp modifies: {result}"


def test_termination_failure_hint_might_not_decrease():
    """Kiểm tra hint ngữ nghĩa cho lỗi decreases expression might not decrease."""
    code = """method Test(n: int) {
    var i := 0;
    while i < n
        decreases i
    {
        i := i + 1;
    }
}"""
    raw_error = "Error: decreases expression might not decrease"
    hint = DiagnosticParser.generate_semantic_hint(
        category="TerminationFailure",
        message=raw_error,
        faulty_line="decreases i",
        code=code,
    )
    assert "decreases n - i" in hint
    assert "BIỂU THỨC GIẢM KHÔNG GIẢM NGHIÊM NGẶT" in hint


def test_termination_failure_hint_cannot_prove():
    """Kiểm tra hint ngữ nghĩa cho lỗi cannot prove termination."""
    raw_error = "Error: cannot prove termination, try supplying a decreases clause"
    hint = DiagnosticParser.generate_semantic_hint(
        category="TerminationFailure",
        message=raw_error,
        faulty_line="while i < n",
        code="",
    )
    assert "KHÔNG THỂ CHỨNG MINH TÍNH DỪNG" in hint
    assert "decreases" in hint


def test_normalize_applies_axis4():
    """Kiểm tra normalize() tích hợp đầy đủ infer_loop_decreases và infer_array_modifies."""
    code = """method ReverseArray(a: array<int>)
    requires a != null
{
    var i := 0;
    while i < a.Length
        invariant 0 <= i <= a.Length
    {
        a[i] := 0;
        i := i + 1;
    }
}
"""
    normalized = SyntaxNormalizer.normalize(code)
    assert "modifies a" in normalized, f"Thiếu modifies a trong normalized: {normalized}"
    assert "decreases a.Length - i" in normalized, f"Thiếu decreases a.Length - i trong normalized: {normalized}"


def test_infer_decreases_same_line_brace():
    """Kiểm tra suy luận decreases khi dấu mở ngoặc { nằm cùng dòng với while."""
    code = """method LoopSameLine(n: int)
{
    var i := 0;
    while i < n {
        i := i + 1;
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases n - i" in result, f"Thiếu decreases khi ngoặc nhọn mở cùng dòng: {result}"
    assert "while i < n" in result


def test_infer_decreases_less_than_equal():
    """Kiểm tra suy luận decreases n + 1 - i cho vòng lặp có toán tử <=."""
    code = """method SumToN(n: int)
{
    var i := 0;
    while i <= n
        invariant 0 <= i <= n + 1
    {
        i := i + 1;
    }
}
"""
    result = SyntaxNormalizer.infer_loop_decreases(code)
    assert "decreases n + 1 - i" in result, f"Thiếu decreases n + 1 - i: {result}"


def test_termination_failure_hint_bounded_below():
    """Kiểm tra hint ngữ nghĩa cho lỗi decreases expression must be bounded below."""
    raw_error = "Error: decreases expression must be bounded below by 0"
    hint = DiagnosticParser.generate_semantic_hint(
        category="TerminationFailure",
        message=raw_error,
        faulty_line="decreases n - i",
        code="",
    )
    assert "BIỂU THỨC DỪNG BỊ ÂM HOẶC KHÔNG BỊ CHẶN DƯỚI" in hint
    assert "decreases" in hint
