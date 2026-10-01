method linear_search_last(s: seq<int>, key: int) returns (index: int)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures -1 <= index < |s|
  ensures index >= 0 ==> s[index] == key && (forall k :: index < k < |s| ==> s[k] != key)
  ensures index == -1 ==> forall k :: 0 <= k < |s| ==> s[k] != key
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
