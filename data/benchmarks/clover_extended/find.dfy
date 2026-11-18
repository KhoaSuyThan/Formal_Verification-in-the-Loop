method Find(a: array<int>, key: int) returns (index: int)
  // post-conditions-start
  ensures -1<=index<a.Length
  ensures index!=-1 ==> a[index]==key && (forall i :: 0 <= i < index ==> a[i] != key)
  ensures index == -1 ==> (forall i::0 <= i < a.Length ==> a[i] != key)
  // post-conditions-end
{
  // impl-start
  // impl-end
}