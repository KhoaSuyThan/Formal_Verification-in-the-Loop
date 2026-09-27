// Bài toán: Tìm giá trị nhỏ nhất giữa hai số nguyên a và b
// Đặc tả ensures được khóa cứng bằng SHA-256 qua SpecLocker

method Min(a: int, b: int) returns (m: int)
    ensures m <= a && m <= b
    ensures m == a || m == b
{
    // Thân hàm để trống cho LLM hoàn thiện
}
