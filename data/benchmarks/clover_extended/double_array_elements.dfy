method double_array_elements(s: array<int>)
  // post-conditions-start
  ensures forall i :: 0 <= i < s.Length ==> s[i] == 2 * old(s[i])
  // post-conditions-end
  modifies s
{
  // impl-start
  // impl-end
}