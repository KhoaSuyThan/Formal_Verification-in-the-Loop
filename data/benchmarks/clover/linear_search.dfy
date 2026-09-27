// Bài toán: Tìm kiếm phần tử target trong mảng số nguyên
// Đặc tả ensures được khóa cứng bằng SHA-256 qua SpecLocker

method LinearSearch(a: array<int>, target: int) returns (r: int)
    ensures r >= 0 ==> r < a.Length && a[r] == target
    ensures r == -1 ==> forall i :: 0 <= i < a.Length ==> a[i] != target
{
    // Thân hàm để trống cho LLM hoàn thiện
}
