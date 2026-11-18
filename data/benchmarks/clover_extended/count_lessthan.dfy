method CountLessThan(numbers: set<int>, threshold: int) returns (count: int)
  // post-conditions-start
  ensures count == |set i | i in numbers && i < threshold|
  // post-conditions-end
{
  // impl-start
  // impl-end
}