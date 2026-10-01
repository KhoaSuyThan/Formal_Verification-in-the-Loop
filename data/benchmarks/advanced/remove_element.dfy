method remove_element(s: seq<int>, val: int) returns (res: seq<int>)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures forall k :: 0 <= k < |res| ==> res[k] != val
  ensures |res| <= |s|
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
