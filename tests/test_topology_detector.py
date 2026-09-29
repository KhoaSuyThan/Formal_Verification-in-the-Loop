"""Unit test cho module TopologyDetector."""

from core.topology_detector import TopologyDetector, AlgorithmTopology


def test_detect_direct():
    truncate_spec = """method truncate_number(x : real) returns (d : real)
    requires x >= 0.0
    ensures (0.0 <= d <= 1.0)
    ensures (x - d) == (x.Floor as real)
"""
    assert TopologyDetector.detect(truncate_spec) == AlgorithmTopology.DIRECT

    abs_spec = """method abs_val(x: int) returns (y: int)
    ensures y >= 0
    ensures x >= 0 ==> y == x
    ensures x < 0 ==> y == -x
"""
    assert TopologyDetector.detect(abs_spec) == AlgorithmTopology.DIRECT


def test_detect_pure_func_equiv():
    fib_spec = """function fib(n: nat): nat
  decreases n
{
  if n == 0 then 0
  else if n == 1 then 1
  else fib(n - 1) + fib(n - 2)
}
// pure-end
method ComputeFib(n: nat) returns (result: nat)
  ensures result == fib(n)
"""
    assert TopologyDetector.detect(fib_spec) == AlgorithmTopology.PURE_FUNC_EQUIV


def test_detect_linear_loop():
    max_spec = """method max_element(l : seq<int>) returns (result : int)
    requires |l| > 0
    ensures forall i : int :: i >= 0 && i < |l| ==> l[i] <= result
    ensures exists i : int :: i >= 0 && i < |l| && l[i] == result
"""
    assert TopologyDetector.detect(max_spec) == AlgorithmTopology.LINEAR_LOOP


def test_detect_nested_loop():
    close_spec = """method has_close_elements(numbers: seq<real>, threshold: real) returns (flag : bool)
  requires threshold > 0.0
  ensures flag == (exists i: int, j: int :: i >= 0 && j >= 0 && i < |numbers| && j < |numbers| && i != j && abs(numbers[i] - numbers[j]) < threshold)
"""
    assert TopologyDetector.detect(close_spec) == AlgorithmTopology.NESTED_LOOP


def test_detect_number_theory():
    prime_spec = """method is_prime(k: int) returns (result: bool)
  requires k >= 1
  ensures result ==> forall i :: 2 <= i < k ==> k % i != 0
  ensures (k > 1 && !result) ==> exists j :: 2 <= j < k && k % j == 0
"""
    assert TopologyDetector.detect(prime_spec) == AlgorithmTopology.NUMBER_THEORY

    gcd_spec = """method greatest_common_divisor(a: int, b: int) returns (result: int)
  requires a != 0 || b != 0
  ensures result > 0
  ensures a % result == 0 && b % result == 0
"""
    assert TopologyDetector.detect(gcd_spec) == AlgorithmTopology.NUMBER_THEORY


def test_detect_non_linear():
    cube_spec = """method iscube(n: int) returns (result: bool)
  ensures result ==> exists c :: c * c * c == n
"""
    assert TopologyDetector.detect(cube_spec) == AlgorithmTopology.NON_LINEAR


def test_detect_sort():
    sort_spec = """method sort_array(a: seq<int>) returns (result: seq<int>)
  ensures multiset(result) == multiset(a)
"""
    assert TopologyDetector.detect(sort_spec) == AlgorithmTopology.PERMUTATION_SORT


if __name__ == "__main__":
    test_detect_direct()
    test_detect_pure_func_equiv()
    test_detect_linear_loop()
    test_detect_nested_loop()
    test_detect_number_theory()
    test_detect_non_linear()
    test_detect_sort()
    print("ALL TopologyDetector TESTS PASSED!")
