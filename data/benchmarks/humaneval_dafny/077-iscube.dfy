method cube_root(N: nat) returns (r: nat)
  // post-conditions-start
  ensures cube(r) <= N < cube(r + 1)
  ensures r <= N
  // post-conditions-end
{
  // impl-start
    // Thân hàm để trống cho LLM tự sinh mã thuật toán
    // impl-end
}

method iscube(n: int) returns (r: bool)
  // pre-conditions-start
  // pre-conditions-end
  // post-conditions-start
  ensures r && n >= 0 ==> exists r :: 0 <= r <= n && n == cube(r)
  ensures !r && n >= 0 ==> forall r :: 0 <= r <= n ==> n != cube(r)
  ensures r && n < 0 ==> exists r :: 0 <= r <= -n && n == -cube(r)
  ensures !r && n < 0 ==> forall r :: 0 <= r <= -n ==> n != -cube(r)
  // post-conditions-end
{
    // impl-start
    // Thân hàm để trống cho LLM tự sinh mã thuật toán
    // impl-end
}

function cube(n: int): int { n * n * n }
// pure-end
lemma cube_of_larger_is_larger()
    ensures forall smaller : int, larger : int :: smaller <= larger ==> cube(smaller) <= cube(larger)
{}
// pure-end
