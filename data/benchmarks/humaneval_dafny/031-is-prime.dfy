method is_prime(k: int) returns (result: bool)
  // pre-conditions-start
  requires k >= 1
  // pre-conditions-end
  // post-conditions-start
  ensures result ==> forall i :: 2 <= i < k ==> k % i != 0
  ensures (k > 1 && !result) ==> exists j :: 2 <= j < k && k % j == 0
  // post-conditions-end
{
  // impl-start
    // Thân hàm để trống cho LLM tự sinh mã thuật toán
    // impl-end
}
