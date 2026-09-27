// Bài toán: Tính tổng các số nguyên không âm từ 0 đến n
// Yêu cầu: Sử dụng vòng lặp và bất biến vòng lặp (loop invariant) để chứng minh
// Đặc tả ensures được khóa cứng bằng SHA-256 qua SpecLocker

method SumToN(n: int) returns (s: int)
    requires n >= 0
    ensures s == n * (n + 1) / 2
{
    // Thân hàm để trống cho LLM hoàn thiện (cần vòng lặp và loop invariant)
}
