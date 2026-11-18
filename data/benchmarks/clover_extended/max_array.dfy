method maxArray(a: array<int>) returns (m: int)
  // pre-conditions-start
  requires a.Length >= 1
  // pre-conditions-end
  // post-conditions-start
  ensures forall k :: 0 <= k < a.Length ==> m >= a[k]
  ensures exists k :: 0 <= k < a.Length && m == a[k]
  // post-conditions-end
{
  // impl-start
  // impl-end
}