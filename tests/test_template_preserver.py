"""Unit test kiểm thử module TemplatePreserver."""

from core.template_preserver import TemplatePreserver


def test_preserve_000_abs():
    raw_spec = """function abs(val : real): real
{
  if (val < 0.0) then
    -val
  else
    val
}
// pure-end
method has_close_elements(numbers: seq<real>, threshold: real) returns (flag : bool)
  requires threshold > 0.0
  ensures flag == true
{
}
"""
    # Giả sử LLM chỉ sinh method mà quên function abs
    llm_code = """method has_close_elements(numbers: seq<real>, threshold: real) returns (flag : bool)
  requires threshold > 0.0
  ensures flag == true
{
  flag := true;
}
"""
    result = TemplatePreserver.preserve_code(raw_spec, llm_code)
    assert "function abs" in result
    assert "flag := true;" in result
    print("[OK] Test 000 abs: PASS")


def test_preserve_077_cube():
    raw_spec = """method iscube(n: int) returns (r: bool)
  ensures r == true
{
}

function cube(n: int): int { n * n * n }
// pure-end
lemma cube_of_larger_is_larger()
    ensures forall a: int, b: int :: a <= b ==> cube(a) <= cube(b)
{}
// pure-end
"""
    # LLM chỉ sinh iscube
    llm_code = """method iscube(n: int) returns (r: bool)
  ensures r == true
{
  r := true;
}
"""
    result = TemplatePreserver.preserve_code(raw_spec, llm_code)
    assert "function cube" in result
    assert "lemma cube_of_larger_is_larger" in result
    print("[OK] Test 077 cube & lemma: PASS")


if __name__ == "__main__":
    test_preserve_000_abs()
    test_preserve_077_cube()
    print("All tests passed!")
