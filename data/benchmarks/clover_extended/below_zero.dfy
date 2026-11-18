method below_zero(operations: seq<int>) returns (s:array<int>, result:bool)
  // post-conditions-start
  ensures s.Length == |operations| + 1
  ensures s[0]==0
  ensures forall i :: 0 <= i < s.Length-1 ==> s[i+1]==s[i]+operations[i]
  ensures result == true ==> (exists i :: 1 <= i <= |operations| && s[i] < 0)
  ensures result == false ==> forall i :: 0 <= i < s.Length ==> s[i] >= 0
  // post-conditions-end
{
  // impl-start
  // impl-end
}