function prod(s: seq<int>): int
  decreases |s|
{
  if |s| == 0 then 1
  else s[0] * prod(s[1..])
}
// pure-end

method product_of_array(s: seq<int>) returns (p: int)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures p == prod(s)
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
