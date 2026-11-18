# Kế hoạch 75 ngày hoàn thiện nghiên cứu và bài báo CYSG 2027

**Đề tài:** Formal Verification-in-the-Loop  
**Thời gian:** 18/11/2026–01/02/2027 (75 ngày, tính từ ngày bắt đầu đến hạn nộp)  
**Mục tiêu nộp:** Bản thảo tham dự Hội nghị Nghiên cứu Khoa học Người học HUTECH 2027 (CYSG2027)  
**Phân ban dự kiến:** Công nghệ thông tin – Trí tuệ nhân tạo

## 1. Mục tiêu và nguyên tắc điều hành

### Mục tiêu chính

1. Mở rộng benchmark từ Core-30 hiện có lên **80–100 bài toán Dafny hợp lệ** nếu qua được các cổng chất lượng bên dưới.
2. Đánh giá có đối chứng tác động của phản hồi verifier và pipeline đề xuất, trên tập bài và ngân sách thống nhất.
3. Phân tích kết quả theo độ khó, cấu trúc bài toán, loại lỗi, thời gian, số vòng sửa và mức sử dụng mô hình.
4. Hoàn tất bản thảo đúng mẫu CYSG, nhận góp ý GVHD và nộp trước **01/02/2027**.

### Quy ước về kết quả hiện có

- Ghi nhận kết quả hiện có **29/30** là kết quả đã chạy để làm điểm xuất phát của kế hoạch.
- Không dành tuần đầu để chạy lại chỉ nhằm xác minh con số này. Giữ nguyên log và cấu hình cũ; chỉ kiểm tra bổ sung khi phát hiện sai lệch cụ thể hoặc cần thống nhất giao thức mở rộng.
- Không ghép số liệu từ các cấu hình/mô hình khác nhau thành một kết quả tổng hợp. Kết quả mới phải gắn với manifest, cấu hình và log riêng.

### Nguyên tắc kiểm soát phạm vi

- Mục tiêu mở rộng là **80–100 bài hợp lệ**, không phải đủ số bất kể chất lượng. Báo cáo đúng số bài đạt tiêu chí và nêu lý do loại phần còn lại.
- Ưu tiên benchmark Dafny có thể kiểm chứng bằng công cụ; phần Python/SWE-bench chỉ là nhánh thăm dò riêng, không gộp vào tỷ lệ chứng minh Dafny.
- Giữ tối đa hai cấu hình mô hình chính trên toàn bộ benchmark; cấu hình thứ ba chỉ chạy trên tập con nếu lịch và ngân sách còn đủ.
- “Sửa thành công trong tối đa K vòng” được báo cáo là **repair@K** nếu các lượt sửa nối tiếp nhận phản hồi verifier; chỉ dùng Pass@K khi đúng với định nghĩa lấy mẫu độc lập của benchmark.
- Không tuyên bố “loại bỏ ảo giác”, “đúng tuyệt đối” hoặc “vượt Clover” nếu thiết kế và bằng chứng không hỗ trợ các kết luận đó.

## 2. Định nghĩa một bài toán được tính vào benchmark

Một task chỉ được đưa vào mẫu số đánh giá chính khi đáp ứng tất cả điều kiện:

1. Có nguồn, phiên bản/revision và quyền sử dụng được ghi lại.
2. Đặc tả, chữ ký hàm và đầu ra mong đợi được lưu trong manifest.
3. Bản tham chiếu hoặc đặc tả nền tảng qua được phiên bản Dafny đã khóa.
4. Bài toán có thể chạy độc lập, thời hạn và tài nguyên chạy nằm trong giới hạn đã định.
5. Không trùng với task khác sau chuẩn hóa; tập phát triển và tập đánh giá được gắn nhãn riêng.
6. Các task tự tạo hoặc chuyển đổi có ghi rõ nguồn gốc, cách chuyển và trạng thái rà soát.

Task không đạt cổng được lưu trong danh sách loại/treo, không xóa dấu vết và không tính vào tỷ lệ thành công. Với benchmark ngoài, giữ nguyên phần tham chiếu cần thiết và không đưa lời giải kiểm thử kín vào prompt.

## 3. Giao thức thực nghiệm cần khóa

Trước lượt chạy chính thức, chốt và ghi vào `protocol.yaml` hoặc tài liệu tương đương:

- phiên bản model, nhà cung cấp/endpoint, ngày truy cập và tham số sinh;
- prompt hệ thống, prompt task và phiên bản mã pipeline;
- phiên bản Dafny, Z3 và môi trường chạy;
- số vòng sửa tối đa, timeout mỗi task, giới hạn token và chính sách retry;
- cách tính verified, repair@K, thời gian, token/cost và lỗi hạ tầng;
- quy tắc cache, xử lý task lỗi, và số lượt lặp nếu có;
- hash manifest, prompt, cấu hình và commit mã nguồn.

Thiết kế so sánh tối thiểu trên cùng task:

| Nhánh | Cấu hình | Câu hỏi được trả lời |
|---|---|---|
| A | Sinh một lần, sau đó chạy verifier | Năng lực nền khi không có sửa theo phản hồi |
| B | Sửa tối đa K vòng với thông báo verifier | Tác động của vòng feedback |
| C | Pipeline đầy đủ | Hiệu quả của hệ thống đề xuất |
| D, nếu đủ nguồn lực | Ablation một thành phần tại một thời điểm | Thành phần nào đóng góp đáng kể |

Giữ model, task, đặc tả, ngân sách và timeout giống nhau trong từng đối chiếu. SpecLocker được đánh giá riêng bằng các trường hợp thử thay đổi đặc tả; không suy ra hiệu quả của nó chỉ từ tỷ lệ verify.

## 4. Lịch thực hiện theo ngày

| Ngày | Khoảng ngày | Trọng tâm | Công việc và đầu ra bắt buộc |
|---:|---|---|---|
| 1–3 | 18–20/11 | Khởi động, khóa mục tiêu | Chốt câu hỏi nghiên cứu, tiêu chí benchmark, diện kỷ yếu và người phụ trách. Tải template/hướng dẫn CYSG hiện hành; xác nhận quy trình với Khoa/Viện. Tạo bảng theo dõi task, rủi ro và quyết định. |
| 4–7 | 21–24/11 | Chuẩn bị dữ liệu | Kiểm kê 35 task đang có; Core-30 và kết quả 29/30 được đánh dấu riêng. Tạo manifest thống nhất với ID, nguồn, nhóm, độ khó, trạng thái Dafny, hash và trạng thái đưa vào tập chính. |
| 8–10 | 25–27/11 | Chốt protocol | Khóa phiên bản Dafny/Z3, prompt, model chính, timeout, giới hạn sửa và định nghĩa metric. Chạy pilot nhỏ trên 5–8 task mới để ước lượng tốc độ nhập/chạy, không dùng pilot để kết luận. |
| 11–17 | 28/11–04/12 | Thu thập benchmark ngoài đợt 1 | Chọn nguồn benchmark công khai; tải/import theo revision cố định; tự động kiểm tra cấu trúc, trùng lặp và xác minh bản tham chiếu. Mục tiêu sàng lọc thêm 25–35 task. |
| 18–24 | 05–11/12 | Thu thập benchmark ngoài đợt 2 | Bổ sung 25–35 task nữa; phân tầng theo mảng, vòng lặp/invariant, đệ quy, cấu trúc quy nạp và nhiều hàm. Ghi nguyên nhân loại từng task. Mục tiêu cộng dồn: 80–100 task ứng viên tính cả Core-30. |
| 25–27 | 12–14/12 | Cổng chất lượng benchmark | Chạy kiểm tra nền trên toàn bộ ứng viên. Rà thủ công mẫu theo từng nhóm và tất cả task có cảnh báo. Khóa danh sách task hợp lệ v1; nếu chưa đủ 80, ưu tiên tìm nguồn/nhóm thiếu thay vì nới tiêu chí. |
| 28–35 | 15–22/12 | Chạy thực nghiệm chính đợt 1 | Chạy nhánh A/B/C trên khoảng một nửa tập đã khóa với model chính. Lưu từng lần gọi, phản hồi verifier, trạng thái cuối, thời gian và token. Theo dõi lỗi hạ tầng riêng. |
| 36–42 | 23–29/12 | Chạy thực nghiệm chính đợt 2 | Hoàn tất nhánh A/B/C trên toàn tập bằng model chính. Chạy model thứ hai trên cùng tập nếu giới hạn thời gian/ngân sách cho phép; nếu không, ưu tiên hoàn tất đủ đối chứng model chính. |
| 43–47 | 30/12–03/01 | Hoàn tất và làm sạch kết quả | Xử lý task bị gián đoạn theo chính sách retry; không thay đổi prompt giữa chừng. Khóa raw logs, xuất bảng dữ liệu phân tích, rà mẫu thủ công và ghi mọi ngoại lệ. |
| 48–52 | 04–08/01 | Phân tích và ablation | Tính verified rate và repair@K; phân tích theo nhóm task, độ khó, loại lỗi, thời gian, số vòng và token. Chạy ablation cho các module ưu tiên trên tập phân tầng nếu còn đủ thời gian. |
| 53–57 | 09–13/01 | Viết bản thảo v1 | Hoàn tất Introduction, Related Work, Method, Experimental Setup, Results, Limitations và References. Dùng bảng/biểu đồ lấy trực tiếp từ dữ liệu đã khóa. Gửi GVHD bản v1 chậm nhất ngày 13/01. |
| 58–62 | 14–18/01 | GVHD phản biện và sửa | Thu nhận góp ý, chỉnh lập luận và giới hạn tuyên bố. Kiểm tra nguồn từng số liệu, trích dẫn APA, tính nhất quán giữa bảng, phần văn bản và log. Chốt nội dung khoa học v2. |
| 63–67 | 19–23/01 | Chuẩn hóa theo CYSG | Đưa bài vào mẫu chính thức; bảo đảm tối đa 5 trang A4 theo thông báo hiện hành. Kiểm tra tiêu đề/tóm tắt/từ khóa/tác giả, hình bảng, APA và tỷ lệ trùng lặp theo quy định. |
| 68–71 | 24–27/01 | Rà soát nộp bài | Rà lỗi nội dung, định dạng và tệp đính kèm; xác nhận đúng hội nghị/track, thông tin tác giả, GVHD và tài khoản hệ thống. Xin GVHD duyệt bản cuối. |
| 72–75 | 28/01–01/02 | Dự phòng và nộp | Khóa bản cuối; nộp sớm khi được duyệt, không đợi ngày cuối. Lưu xác nhận nộp, bản PDF/Word cuối, metadata và mã bài. Dành thời gian xử lý lỗi hệ thống hoặc yêu cầu bổ sung. |

### Các mốc kiểm soát

- **Ngày 10 (27/11):** protocol và pilot đủ rõ để ước lượng năng lực xử lý benchmark.
- **Ngày 27 (14/12):** danh sách đánh giá chính được khóa; mục tiêu 80–100 task hợp lệ.
- **Ngày 42 (29/12):** hoàn tất lượt chạy chính hoặc có phương án thu hẹp đã ghi lý do.
- **Ngày 52 (08/01):** số liệu, bảng kết quả và phân tích thất bại được khóa.
- **Ngày 57 (13/01):** bản thảo v1 gửi GVHD.
- **Ngày 67 (23/01):** bản thảo đúng mẫu hoàn chỉnh.
- **Ngày 75 (01/02):** hạn nộp chính thức.

## 5. Mục tiêu mở rộng và phương án dự phòng

### Mục tiêu chính

- **80–100 task hợp lệ**: Core-30 cộng benchmark ngoài đã qua cổng chất lượng.
- Tối thiểu một model chạy đủ các nhánh A/B/C trên tập đã khóa.
- Model thứ hai chạy toàn bộ tập nếu ngân sách cho phép; nếu không, chạy tập con phân tầng 30–50 task và nêu rõ thiết kế.
- Báo cáo ít nhất các nhóm: mảng/vòng lặp, đệ quy/quy nạp, nhiều hàm hoặc cấu trúc phức tạp. Không tạo nhóm thống kê quá nhỏ để rút kết luận mạnh.

### Cắt giảm có kiểm soát

1. Nếu đến ngày 14/12 chưa có 80 task hợp lệ, khóa tập hợp lệ thực tế (ví dụ 65–79) và tiếp tục chạy; không đưa task lỗi vào để đạt chỉ tiêu.
2. Nếu model thứ hai làm chậm tiến độ, giữ nó ở tập con phân tầng; bảo vệ trước tiên kết quả so sánh A/B/C của model chính.
3. Nếu ablation không thể hoàn tất trước 08/01, bỏ ablation khỏi kết quả chính và mô tả là hướng tiếp theo; không hy sinh thời gian viết bài.
4. Python/SWE-bench, sinh thuộc tính mới và mở rộng taxonomy không thuộc đường găng của bài CYSG lần này.

## 6. Bảng theo dõi benchmark đề xuất

Mỗi dòng là một task; tối thiểu có các trường:

`task_id`, `source`, `source_revision`, `license`, `category`, `difficulty`, `dafny_file`, `reference_status`, `spec_review_status`, `duplicate_group`, `split`, `include_status`, `exclusion_reason`, `sha256`, `run_status`.

Mỗi lượt chạy lưu riêng:

`task_id`, `model_id`, `method`, `prompt_version`, `code_commit`, `attempts_used`, `verified`, `failure_class`, `elapsed_seconds`, `input_tokens`, `output_tokens`, `estimated_cost`, `infra_error`, `raw_log_path`.

## 7. Rủi ro chính và cách xử lý

| Rủi ro | Dấu hiệu sớm | Ứng phó |
|---|---|---|
| Nguồn benchmark khó tích hợp | Nhiều task thiếu đặc tả hoặc không qua Dafny | Dùng importer/validator trước; đặt hạn cổng ngày 14/12; báo cáo task hợp lệ thực tế. |
| Model/API chậm hoặc giới hạn quota | Lượt chạy dở dang, lỗi 429/timeout tăng | Chạy tuần tự/giới hạn song song, retry theo chính sách, dự phòng một model thay thế và ghi rõ phiên bản. |
| Tập bài lệch về một dạng | Phân bố quá nhiều bài mảng đơn giản | Theo dõi phân tầng ngay trong giai đoạn nhập; tìm thêm nhóm đệ quy, invariant và nhiều hàm. |
| Rò rỉ benchmark vào prompt | Prompt chứa lời giải/đáp án tham chiếu | Tách dữ liệu chấm; rà prompt tự động và kiểm tra thủ công một mẫu trước khi chạy chính. |
| Mở rộng lấn thời gian viết | Chưa có bảng kết quả đến 08/01 | Dừng thêm task, đóng băng dữ liệu và chuyển nguồn lực sang phân tích/bản thảo. |
| Quy định hội nghị cập nhật | Template/thể lệ khác nội dung hiện có | Kiểm tra thông báo CYSG và hỏi Khoa/Phòng KHCN trước khi chốt định dạng, track và ngày tổ chức. |

## 8. Tiêu chí hoàn thành

Kế hoạch được xem là hoàn tất khi:

- Benchmark có manifest, nguồn và trạng thái xác minh cho từng task; tập đánh giá cuối cùng được khóa.
- Log thô và cấu hình đủ để tính lại các bảng chính.
- Bản thảo phản ánh đúng số liệu, cách đo, hạn chế và nguồn gốc benchmark.
- Bài đúng template/thể lệ hiện hành, được GVHD duyệt và nộp trước 01/02/2027.
- Lưu xác nhận nộp và phiên bản cuối của toàn bộ tệp gửi hội nghị.

## 9. Quy định hội nghị cần đối chiếu

Thông báo CYSG 2027 được Khoa QTKD đăng ngày 17/11/2026 nêu hạn gửi bài 01/02/2027, kết quả phản biện 01/03/2027, bài hoàn chỉnh 01/04/2027 và giới hạn bản thảo tối đa 5 trang A4, trích dẫn APA. Thông báo cũng ghi hội nghị ngày 14/05/2027 (Thứ 7); ngày này theo lịch năm 2027 là thứ Sáu. Cần xác nhận lịch chính thức với Khoa/Phòng KHCN. Quy trình đăng ký và track có thể khác theo Khoa/Viện và diện tác giả; kiểm tra lại trực tiếp trước khi nộp.

---

**Ghi chú:** Đây là kế hoạch tác nghiệp, không phải cam kết rằng số task hoặc kết quả thành công sẽ đạt một mức định trước. Ưu tiên báo cáo trung thực số bài hợp lệ và kết quả quan sát được.
