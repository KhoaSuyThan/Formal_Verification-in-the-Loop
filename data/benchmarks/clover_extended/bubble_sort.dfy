method BubbleSort(a: array<int>)
  // post-conditions-start
  ensures forall i,j::0<= i < j < a.Length ==> a[i] <= a[j]
  ensures multiset(a[..])==multiset(old(a[..]))
  // post-conditions-end
  modifies a
{
  // impl-start
  // impl-end
}