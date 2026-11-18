method Match(s: string, p: string) returns (b: bool)
  // pre-conditions-start
  requires |s| == |p|
  // pre-conditions-end
  // post-conditions-start
  ensures b <==> forall n :: 0 <= n < |s| ==> s[n] == p[n] || p[n] == '?'
  // post-conditions-end
{
  // impl-start
  // impl-end
}