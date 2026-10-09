datatype List = Nil | Cons(head: int, tail: List)

function list_len(l: List): nat {
  match l
  case Nil => 0
  case Cons(_, t) => 1 + list_len(t)
}

function list_sum(l: List): int {
  match l
  case Nil => 0
  case Cons(h, t) => h + list_sum(t)
}
// pure-end

method compute_list_stats(l: List) returns (len: nat, s: int)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures len == list_len(l)
  ensures s == list_sum(l)
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM sinh mã tính độ dài và tổng danh sách
  // impl-end
}
