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


def test_preserve_datatype_and_ghost_predicate():
    raw_spec = """datatype Tree = Leaf | Node(left: Tree, val: int, right: Tree)

ghost predicate is_bst(t: Tree) {
  match t
  case Leaf => true
  case Node(l, v, r) => is_bst(l) && is_bst(r)
}
// pure-end

method bst_insert(t: Tree, x: int) returns (res: Tree)
  requires is_bst(t)
  ensures is_bst(res)
{
}
"""
    # LLM chỉ sinh method mà quên cả datatype Tree và ghost predicate is_bst
    llm_code = """method bst_insert(t: Tree, x: int) returns (res: Tree)
  requires is_bst(t)
  ensures is_bst(res)
{
  res := Node(Leaf, x, Leaf);
}
"""
    result = TemplatePreserver.preserve_code(raw_spec, llm_code)
    assert "datatype Tree" in result
    assert "ghost predicate is_bst" in result
    assert "res := Node(Leaf, x, Leaf);" in result
    # Đảm bảo datatype Tree đứng trước ghost predicate và method
    pos_data = result.find("datatype Tree")
    pos_pred = result.find("ghost predicate is_bst")
    pos_meth = result.find("method bst_insert")
    assert pos_data < pos_pred < pos_meth
    print("[OK] Test preserve datatype & ghost predicate: PASS")


if __name__ == "__main__":
    test_preserve_000_abs()
    test_preserve_077_cube()
    test_preserve_datatype_and_ghost_predicate()
    print("All tests passed!")
