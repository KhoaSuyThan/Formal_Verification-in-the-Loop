method below_threshold(l : seq<int>, t : int) returns (b : bool)
    // post-conditions-start
    ensures b == (forall i : int :: i >= 0 && i < |l| ==> l[i] < t)
    // post-conditions-end
{
    // impl-start
    // Thân hàm để trống cho LLM tự sinh mã thuật toán
    // impl-end
}
