method convert_map_key(inputs: map<nat, bool>, f: nat->nat) returns(r:map<nat, bool>)
  // pre-conditions-start
  requires forall n1: nat, n2: nat :: n1 != n2 ==> f(n1) != f(n2)
  // pre-conditions-end
  // post-conditions-start
  ensures forall k :: k in inputs <==> f(k) in r
  ensures forall k :: k in inputs ==> r[f(k)] == inputs[k]
  // post-conditions-end
{
  // impl-start
  // impl-end
}