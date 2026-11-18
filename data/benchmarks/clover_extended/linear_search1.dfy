method LinearSearch(a: array<int>, e: int) returns (n:int)
  // post-conditions-start
  ensures 0<=n<=a.Length
  ensures n==a.Length || a[n]==e
  ensures forall i::0<=i < n ==> e!=a[i]
  // post-conditions-end
{
  // impl-start
  // impl-end
}