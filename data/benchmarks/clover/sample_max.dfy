// Bài toán mẫu từ tập CloverBench: Tìm giá trị lớn nhất giữa hai số nguyên a và b
// Đặc tả ensures được khóa cứng bằng SHA-256 qua SpecLocker

method Max(a: int, b: int) returns (m: int)
    ensures m >= a && m >= b
    ensures m == a || m == b
{
    // Thân hàm để trống cho LLM sinh mã thuật toán
}
