method find_first_negative(s: seq<int>) returns (index: int)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures -1 <= index < |s|
  ensures index >= 0 ==> s[index] < 0 && (forall k :: 0 <= k < index ==> s[k] >= 0)
  ensures index == -1 ==> forall k :: 0 <= k < |s| ==> s[k] >= 0
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
