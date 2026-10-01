method copy_array(s: seq<int>) returns (res: seq<int>)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures |res| == |s|
  ensures forall k :: 0 <= k < |s| ==> res[k] == s[k]
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
