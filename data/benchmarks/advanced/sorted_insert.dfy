predicate is_sorted(s: seq<int>) {
  forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]
}
// pure-end

method sorted_insert(s: seq<int>, x: int) returns (res: seq<int>)
  // pre-conditions-start
  requires is_sorted(s)
  // pre-conditions-end
  // post-conditions-start
  ensures |res| == |s| + 1
  ensures multiset(res) == multiset(s) + multiset{x}
  ensures is_sorted(res)
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
