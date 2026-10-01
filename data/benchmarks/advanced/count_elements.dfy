function count(s: seq<int>, x: int): nat
  decreases |s|
{
  if |s| == 0 then 0
  else (if s[0] == x then 1 else 0) + count(s[1..], x)
}
// pure-end

method count_elements(s: seq<int>, x: int) returns (c: nat)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures c == count(s, x)
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
