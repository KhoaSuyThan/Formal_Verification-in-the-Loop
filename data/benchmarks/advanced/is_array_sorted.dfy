method is_array_sorted(s: seq<int>) returns (sorted: bool)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures sorted <==> forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
