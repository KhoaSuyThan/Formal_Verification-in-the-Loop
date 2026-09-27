// Bài toán: Tính giá trị tuyệt đối của số nguyên x
// Đặc tả ensures được khóa cứng bằng SHA-256 qua SpecLocker

method Abs(x: int) returns (y: int)
    ensures x >= 0 ==> y == x
    ensures x < 0 ==> y == -x
    ensures y >= 0
{
    // Thân hàm để trống cho LLM hoàn thiện
}
