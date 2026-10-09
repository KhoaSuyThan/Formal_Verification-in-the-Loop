datatype Tree = Leaf | Node(left: Tree, val: int, right: Tree)

function tree_size(t: Tree): nat {
  match t
  case Leaf => 0
  case Node(l, _, r) => 1 + tree_size(l) + tree_size(r)
}

function tree_height(t: Tree): nat {
  match t
  case Leaf => 0
  case Node(l, _, r) =>
    var hl := tree_height(l);
    var hr := tree_height(r);
    1 + if hl > hr then hl else hr
}

lemma size_ge_height(t: Tree)
  ensures tree_size(t) >= tree_height(t)
{
  match t {
    case Leaf => {}
    case Node(l, _, r) => {
      size_ge_height(l);
      size_ge_height(r);
    }
  }
}
// pure-end

method compute_tree_metrics(t: Tree) returns (s: nat, h: nat)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures s == tree_size(t)
  ensures h == tree_height(t)
  ensures s >= h
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM sinh mã tính toán đệ quy
  // impl-end
}
