function sum_pos(s: seq<int>): int
  decreases |s|
{
  if |s| == 0 then 0
  else (if s[0] > 0 then s[0] else 0) + sum_pos(s[1..])
}
// pure-end

method sum_positive(s: seq<int>) returns (total: int)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures total == sum_pos(s)
  ensures total >= 0
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
