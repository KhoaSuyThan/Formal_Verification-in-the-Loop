method append(a:array<int>, b:int) returns (c:array<int>)
  // post-conditions-start
  ensures  a[..] + [b] == c[..]
  // post-conditions-end
{
  // impl-start
  // impl-end
}