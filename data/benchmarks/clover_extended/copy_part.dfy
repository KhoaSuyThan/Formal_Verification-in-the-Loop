method copy( src: array<int>, sStart: nat, dest: array<int>, dStart: nat, len: nat) returns (r: array<int>)
  // pre-conditions-start
  requires src.Length >= sStart + len
  requires dest.Length >= dStart + len
  // pre-conditions-end
  // post-conditions-start
  ensures r.Length == dest.Length
  ensures r[..dStart] == dest[..dStart]
  ensures r[dStart + len..] == dest[dStart + len..]
  ensures r[dStart..len+dStart] == src[sStart..len+sStart]
  // post-conditions-end
{
  // impl-start
  // impl-end
}