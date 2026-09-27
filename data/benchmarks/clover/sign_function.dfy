// Bài toán: Tính dấu của một số nguyên x (-1 nếu âm, 0 nếu bằng 0, 1 nếu dương)
// Đặc tả ensures được khóa cứng bằng SHA-256 qua SpecLocker

method Sign(x: int) returns (s: int)
    ensures x < 0 ==> s == -1
    ensures x == 0 ==> s == 0
    ensures x > 0 ==> s == 1
{
    // Thân hàm để trống cho LLM hoàn thiện
}
