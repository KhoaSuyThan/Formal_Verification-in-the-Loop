method onlineMax(a: array<int>, x: int) returns (ghost m:int, p:int)
  // pre-conditions-start
  requires 1<=x<a.Length
  requires a.Length!=0
  // pre-conditions-end
  // post-conditions-start
  ensures x<=p<a.Length
  ensures forall i::0<=i<x==> a[i]<=m
  ensures exists i::0<=i<x && a[i]==m
  ensures x<=p<a.Length-1 ==> (forall i::0<=i<p ==> a[i]<a[p])
  ensures (forall i::x<=i<a.Length && a[i]<=m) ==> p==a.Length-1
  // post-conditions-end
{
  // impl-start
  // impl-end
}