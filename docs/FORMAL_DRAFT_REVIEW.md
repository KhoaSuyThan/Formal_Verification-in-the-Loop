# Mười thuộc tính Dafny đề xuất để rà soát

**Mốc v1.7.0, 18/10/2026:** người dùng sẽ rà soát ý nghĩa nghiệp vụ của các bản nháp này; chưa có thuộc tính nào được ghi nhận là đã duyệt. Xem [hướng dẫn pilot](REAL_WORLD_BENCHMARKS.md) để hiểu cách tách kết quả Dafny và Python.

**Trạng thái: bản nháp, chưa được duyệt.** Mã ở [`draft_properties.dfy`](../data/benchmarks/python_projects/formal_drafts/draft_properties.dfy) là các *vị từ trên dữ liệu trừu tượng*. Lệnh `dafny verify` chỉ kiểm tra tệp Dafny hợp lệ; vì không có hiện thực Python hoặc cầu nối ngữ nghĩa, kết quả đó **không chứng minh bản vá Python đúng**. Mười manifest giữ `formal_review_status: "draft_pending_human_review"` và `formal_files: []`; tỷ lệ chứng minh Dafny của pilot Python không tính các mục này.

| Issue | Điều cần xác nhận trong bản nháp | Khoảng trống mô hình cần xử lý trước khi duyệt |
| --- | --- | --- |
| `django__django-10554` | Đánh giá truy vấn union dẫn xuất không làm đổi tập bản ghi và thứ tự của truy vấn gốc cho lần đánh giá sau. | `QuerySnapshot` chưa mô hình hóa SQL, cache, thứ tự khi khóa bằng nhau và việc đánh giá lại. Xác nhận liệu truy vấn dẫn xuất có luôn cùng tập ID. |
| `django__django-11400` | Thứ tự `ModelAdmin` được ưu tiên, nếu trống dùng `Meta.ordering`; lựa chọn không bỏ bản ghi hợp lệ. | `orderRank` là trừu tượng; cần xác định duplicate, `NULL`, thứ tự nhiều cột và hai loại filter có cùng chính sách hay không. |
| `pydata__xarray-2905` | Gán một object có thuộc tính `.values` vào mảng `object` phải giữ chính object đó. | `objectId` chỉ mô hình hóa identity; cần giới hạn ở phép gán scalar không broadcast và cách xác định dtype sau gán. |
| `pydata__xarray-3095` | `copy(deep=True)` giữ giá trị và dtype Unicode của index, tách vùng nhớ. | `storageId` là mô hình alias; cần xác nhận cả `DataArray`, `Dataset`, shallow copy, tọa độ khác và data variables. |
| `pydata__xarray-3305` | `quantile(..., keep_attrs=True)` giữ nguyên attrs. | Cần chốt áp dụng cho `DataArray`, `Dataset`, biến trung gian và attrs ở cấp nào. |
| `pydata__xarray-4687` | `where` giữ attrs khi người gọi yêu cầu giữ. | Issue gốc nêu cả lựa chọn API chưa có; cần chốt hành vi mặc định, `keep_attrs`, precedence khi các nhánh có attrs khác nhau và dtype có thuộc phạm vi hay không. |
| `pydata__xarray-6938` | `swap_dims()` không thay đổi dataset đầu vào. | Snapshot cần phản ánh thêm index, encoding, attrs hoặc identity của các biến nếu đây là phần của bất biến mong muốn. |
| `pydata__xarray-6992` | Danh sách data variables bằng keys của variables trừ coordinate names, dù coordinate names có phần tử không nằm trong variables. | Cần chốt invariant sau `set_index(...).reset_index(..., drop=True)` và các đối tượng quan sát (`repr`, `len`, iterator). |
| `pydata__xarray-7393` | `stack` giữ dtype của tọa độ `int32`. | Cần xét nhiều tọa độ, pandas MultiIndex, signed/unsigned, và chỉ giữ dtype trong điều kiện nào. |
| `sphinx-doc__sphinx-7462` | Phân tích `Tuple[()]` không phát sinh `IndexError` và trả biểu diễn không rỗng. | Cần chốt chuỗi/AST mong đợi, các biến thể cú pháp, và lỗi khác có được chấp nhận không. |

## Cần người rà soát quyết định

1. Với từng hàng: thuộc tính có phản ánh đúng yêu cầu của issue không? Chỉ rõ phần cần sửa hoặc loại bỏ.
2. Chốt input/output và các trường hợp biên còn thiếu, đặc biệt chính sách attrs của `where`, thứ tự Django, và cách biểu diễn tuple rỗng của Sphinx.
3. Chỉ sau khi mô hình được duyệt, xây kiểm tra nối dữ liệu quan sát từ Python sang mô hình Dafny và giữ bộ kiểm tra hồi quy ẩn độc lập. Không nâng trạng thái `reviewed` chỉ vì file `.dfy` chạy qua `dafny verify`.
