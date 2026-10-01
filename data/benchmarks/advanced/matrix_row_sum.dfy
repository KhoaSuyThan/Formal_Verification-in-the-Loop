function row_sum(r: seq<int>): int
  decreases |r|
{
  if |r| == 0 then 0
  else r[0] + row_sum(r[1..])
}
// pure-end

method matrix_row_sum(m: seq<seq<int>>) returns (sums: seq<int>)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures |sums| == |m|
  ensures forall i :: 0 <= i < |m| ==> sums[i] == row_sum(m[i])
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
