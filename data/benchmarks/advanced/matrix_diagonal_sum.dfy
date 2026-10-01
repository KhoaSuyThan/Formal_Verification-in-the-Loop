function diag_sum(m: seq<seq<int>>, k: nat): int
  requires forall i :: 0 <= i < |m| ==> |m[i]| == |m|
  requires k <= |m|
  decreases k
{
  if k == 0 then 0
  else diag_sum(m, k - 1) + m[k - 1][k - 1]
}
// pure-end

method matrix_diagonal_sum(m: seq<seq<int>>) returns (sum: int)
  // pre-conditions-start
  requires forall i :: 0 <= i < |m| ==> |m[i]| == |m|
  // pre-conditions-end
  // post-conditions-start
  ensures sum == diag_sum(m, |m|)
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
