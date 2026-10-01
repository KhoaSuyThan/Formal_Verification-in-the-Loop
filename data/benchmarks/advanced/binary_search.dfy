predicate is_sorted(s: seq<int>) {
  forall i, j :: 0 <= i < j < |s| ==> s[i] <= s[j]
}
// pure-end

method binary_search(s: seq<int>, key: int) returns (index: int)
  // pre-conditions-start
  requires is_sorted(s)
  // pre-conditions-end
  // post-conditions-start
  ensures -1 <= index < |s|
  ensures index >= 0 ==> s[index] == key
  ensures index == -1 ==> forall k :: 0 <= k < |s| ==> s[k] != key
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
