datatype Tree = Leaf | Node(left: Tree, val: int, right: Tree)

predicate tree_contains(t: Tree, x: int) {
  match t
  case Leaf => false
  case Node(l, v, r) => v == x || tree_contains(l, x) || tree_contains(r, x)
}

predicate is_bst(t: Tree) {
  match t
  case Leaf => true
  case Node(l, v, r) =>
    is_bst(l) && is_bst(r) &&
    (forall x :: tree_contains(l, x) ==> x <= v) &&
    (forall y :: tree_contains(r, y) ==> y > v)
}
// pure-end

method bst_insert(t: Tree, x: int) returns (res: Tree)
  // pre-conditions-start
  requires is_bst(t)
  // pre-conditions-end
  // post-conditions-start
  ensures is_bst(res)
  ensures tree_contains(res, x)
  ensures forall k :: tree_contains(t, k) ==> tree_contains(res, k)
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM sinh mã chèn vào cây BST
  // impl-end
}
