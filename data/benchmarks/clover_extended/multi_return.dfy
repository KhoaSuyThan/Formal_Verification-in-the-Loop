method MultipleReturns(x: int, y: int) returns (more: int, less: int)
  // post-conditions-start
  ensures more == x+y
  ensures less == x-y
  // post-conditions-end
{
  // impl-start
  // impl-end
}