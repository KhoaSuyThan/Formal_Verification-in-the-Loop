method allDigits(s: string) returns (result: bool)
  // post-conditions-start
  ensures  result <==> (forall i :: 0 <= i < |s| ==> s[i] in "0123456789")
  // post-conditions-end
{
  // impl-start
  // impl-end
}