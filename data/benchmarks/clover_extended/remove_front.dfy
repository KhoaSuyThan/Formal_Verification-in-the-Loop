method remove_front(a:array<int>) returns (c:array<int>)
  // pre-conditions-start
  requires a.Length>0
  // pre-conditions-end
  // post-conditions-start
  ensures  a[1..] == c[..]
  // post-conditions-end
{
  // impl-start
  // impl-end
}