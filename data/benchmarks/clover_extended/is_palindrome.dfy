method IsPalindrome(x: seq<char>) returns (result: bool)
  // post-conditions-start
  ensures result <==> (forall i :: 0 <= i < |x| ==> x[i] == x[|x| - i - 1])
  // post-conditions-end
{
  // impl-start
  // impl-end
}