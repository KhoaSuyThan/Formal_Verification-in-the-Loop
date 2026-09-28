"""Unit test kiểm thử module SpecLocker với Subset Preservation Protocol."""

from core.spec_locker import SpecLocker


def test_spec_locker_exact_match():
    raw_spec = """method Foo(x: int) returns (y: int)
        ensures y >= x
        ensures y >= 0
    {}"""
    code = """method Foo(x: int) returns (y: int)
        ensures y >= x
        ensures y >= 0
    { y := x; }"""
    assert SpecLocker.is_valid("", code, raw_spec=raw_spec)
    print("[OK] Test exact match: PASS")


def test_spec_locker_helper_lemma_allowed():
    raw_spec = """method Foo(x: int) returns (y: int)
        ensures y >= x
    {}"""
    # LLM viết thêm helper lemma có ensures riêng
    code_with_helper = """method Foo(x: int) returns (y: int)
        ensures y >= x
    {
        LemmaHelper(x);
        y := x;
    }

    lemma LemmaHelper(n: int)
        ensures n >= 0 ==> n * 2 >= n
    {}"""
    assert SpecLocker.is_valid("", code_with_helper, raw_spec=raw_spec)
    print("[OK] Test helper lemma allowed: PASS")


def test_spec_locker_tampering_rejected():
    raw_spec = """method Foo(x: int) returns (y: int)
        ensures y >= x
        ensures y >= 0
    {}"""
    # LLM tự ý xóa bỏ ensures y >= x
    tampered_code = """method Foo(x: int) returns (y: int)
        ensures y >= 0
    { y := 0; }"""
    assert not SpecLocker.is_valid("", tampered_code, raw_spec=raw_spec)
    print("[OK] Test tampering rejected: PASS")


if __name__ == "__main__":
    test_spec_locker_exact_match()
    test_spec_locker_helper_lemma_allowed()
    test_spec_locker_tampering_rejected()
    print("All SpecLocker tests passed!")
