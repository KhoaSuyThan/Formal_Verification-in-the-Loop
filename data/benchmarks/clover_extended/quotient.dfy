method Quotient(x: nat, y:nat) returns (r:int, q:int)
  // pre-conditions-start
  requires y != 0
  // pre-conditions-end
  // post-conditions-start
  ensures q * y + r == x && 0 <= r < y && 0 <= q
  // post-conditions-end
{
  // impl-start
  // impl-end
}