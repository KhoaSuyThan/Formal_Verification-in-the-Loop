method all_unique(s: seq<int>) returns (unique: bool)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures unique <==> forall i, j :: 0 <= i < j < |s| ==> s[i] != s[j]
  // post-conditions-end
{
  // impl-start
  // Thân hàm để trống cho LLM tự sinh mã thuật toán
  // impl-end
}
