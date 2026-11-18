method arrayProduct(a: array<int>, b: array<int>) returns (c: array<int> )
  // pre-conditions-start
  requires a.Length==b.Length
  // pre-conditions-end
  // post-conditions-start
  ensures c.Length==a.Length
  ensures forall i:: 0 <= i< a.Length==> a[i] * b[i]==c[i]
  // post-conditions-end
{
  // impl-start
  // impl-end
}