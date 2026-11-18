method replace(arr: array<int>, k: int)
  // post-conditions-start
  ensures forall i :: 0 <= i < arr.Length ==> old(arr[i]) > k ==> arr[i] == -1
  ensures forall i :: 0 <= i < arr.Length ==> old(arr[i]) <= k ==> arr[i] == old(arr[i])
  // post-conditions-end
  modifies arr
{
  // impl-start
  // impl-end
}