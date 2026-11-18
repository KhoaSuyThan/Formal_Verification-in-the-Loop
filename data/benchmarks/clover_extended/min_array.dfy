method minArray(a: array<int>) returns (r:int)
  // pre-conditions-start
  requires a.Length > 0
  // pre-conditions-end
  // post-conditions-start
  ensures forall i :: 0 <= i < a.Length ==> r <= a[i]
  ensures exists i :: 0 <= i < a.Length && r == a[i]
  // post-conditions-end
{
  // impl-start
  // impl-end
}