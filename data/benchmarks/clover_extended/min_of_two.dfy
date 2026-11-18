method Min(x: int, y:int) returns (z: int)
  // post-conditions-start
  ensures x<=y ==> z==x
  ensures x>y ==> z==y
  // post-conditions-end
{
  // impl-start
  // impl-end
}