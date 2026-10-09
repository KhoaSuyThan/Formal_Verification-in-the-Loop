datatype List = Nil | Cons(head: int, tail: List)

function to_seq(l: List): seq<int> {
  match l
  case Nil => []
  case Cons(h, t) => [h] + to_seq(t)
}

function reverse_seq(s: seq<int>): seq<int> {
  if |s| == 0 then [] else reverse_seq(s[1..]) + [s[0]]
}
// pure-end

method list_reverse(l: List) returns (rev: List)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures |to_seq(rev)| == |to_seq(l)|
  ensures to_seq(rev) == reverse_seq(to_seq(l))
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM sinh mã đảo ngược danh sách liên kết
  // impl-end
}
