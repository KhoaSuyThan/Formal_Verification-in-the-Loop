method LinearSearch(a: array<int>, e: int) returns (n:int)
  // pre-conditions-start
  requires exists i::0<=i<a.Length && a[i]==e
  // pre-conditions-end
  // post-conditions-start
  ensures 0<=n<a.Length && a[n]==e
  ensures forall k :: 0 <= k < n ==> a[k]!=e
  // post-conditions-end
{
  // impl-start
  // impl-end
}