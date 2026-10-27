# Đánh giá agent coding trên dự án Python thực tế

**Cập nhật theo mốc v1.7.0 (18/10/2026).** Bộ dữ liệu và runner đã có trong dự án; 10 thuộc tính Python vẫn là bản nháp chờ người dùng rà soát. Chưa có kết quả chấm Docker cho toàn bộ 30 issue hoặc số đo tăng tốc toàn bộ suite. Xem [README](../README.md) để cài đặt và [CHANGELOG](../CHANGELOG.md) để xem thay đổi theo phiên bản.

## Ba tập thử, ba câu hỏi khác nhau

| Tập | Quy mô | Đánh giá | Cách chấm |
| --- | ---: | --- | --- |
| DafnyBench20 | 20 | Khôi phục gợi ý chứng minh trong mã Dafny đã có | `dafny verify` và `dafny audit`; giữ nguyên mã gốc |
| Python pilot | 30 issue từ Django, Xarray, Sphinx | Agent tạo bản vá cho dự án Python nhiều tệp | Bộ chấm Docker chính thức của SWE-bench Verified |
| Spec traps | 10 | Bắt sửa đặc tả, giả định không chứng minh, và nhận diện đặc tả quá yếu | Khóa hợp đồng, Dafny audit, ba ca chạy phản ví dụ ngữ nghĩa |

35 bài Dafny ban đầu vẫn là tập hồi quy riêng. Không cộng kết quả của bốn tập thành một tỷ lệ “đúng”. Mười thuộc tính Python được đề xuất trong `data/benchmarks/python_projects/formal_candidates.json` có [bản nháp Dafny và bảng câu hỏi rà soát](FORMAL_DRAFT_REVIEW.md); chúng đang **chờ người dùng rà soát** và chưa được tính là chứng minh hình thức.

## Chạy bộ bài mới

Tại thư mục gốc dự án, dùng môi trường Python đã cài `requirements.txt`. Các lệnh sinh mã đòi hỏi chọn mô hình rõ ràng; Ollama không bắt buộc.

Nếu muốn thao tác trực quan, chạy `streamlit run app.py` rồi mở tab **Bộ thử nghiệm mới**. Tab này cho xem từng case, chạy một bài DafnyBench hoặc issue Python, chạy một hoặc cả 10 ca bẫy đặc tả, xem riêng kết quả kiểm tra Python/Dafny/đặc tả và tải báo cáo JSON. Nhập tên mô hình LiteLLM trong tab khi chạy DafnyBench/Python; bật chấm Docker cho issue Python chỉ khi đã có CLI `swebench` và Docker đang chạy. Các lượt chạy từ giao diện được lưu dưới `artifacts/results/new_benchmarks/`.

Muốn chạy cả tập bằng một nút, chọn nhóm **DafnyBench20** để thấy **Chạy cả 20 bài DafnyBench**, hoặc chọn **Python pilot** để thấy **Chạy cả 30 issue Python**. Mỗi nút chỉ xuất hiện trong nhóm tương ứng, cạnh nút chạy từng case; không có nút gộp 50 case. Chọn mô hình trong danh sách **Mô hình LiteLLM**; nếu tên mong muốn chưa có, chọn **Mô hình khác…** rồi nhập mã LiteLLM. Cấu hình API key hoặc Ollama tương ứng, sau đó chọn số lượt sửa tối đa và số bài chạy song song trước khi bấm. Giao diện theo dõi tiến độ, lưu nhật ký và tổng kết dưới `artifacts/results/new_benchmarks/suite_runs/`. Tập Python chạy cả baseline và framework (60 lượt xử lý cho 30 issue); nếu không bật chấm Docker, báo cáo chỉ xác nhận đã tạo bản vá, không ghi pass bài kiểm tra ẩn.

Ví dụ nếu dùng DeepSeek API, thêm `DEEPSEEK_API_KEY` vào `.env` và chọn `deepseek/deepseek-flash` trong danh sách mô hình. Tập Python pilot 30 issue chạy trọn bộ qua CLI bằng `python -m experiments.run_project_suite --model deepseek/deepseek-flash --output-dir artifacts/results/python_pilot_deepseek`; không có `--grade` thì trạng thái bài kiểm tra Python vẫn chờ bộ chấm Docker.

```bash
# Kiểm tra 10 ca đặc tả, không gọi mô hình
python -m experiments.run_spec_traps --output artifacts/results/spec_traps.json

# Chạy riêng một ca đặc tả
python -m experiments.run_spec_traps --case weak_gcd_nonzero \
  --output artifacts/results/spec_trap_gcd.json

# Chạy một bài khôi phục chứng minh Dafny
python -m experiments.run_dafnybench20 --model <litellm-model-id> \
  --task DafnyProjects_tmp_tmp2acw_s4s_partitionOddEven_no_hints \
  --output artifacts/results/dafnybench20.json

# Chạy cả 20 bài đồng thời có giới hạn; kết quả vẫn xuất theo thứ tự manifest
python -m experiments.run_dafnybench20 --model <litellm-model-id> \
  --workers 2 --output artifacts/results/dafnybench20_all.json

# Tạo bản vá cho một issue Python, chưa chấm bằng Docker
python -m experiments.run_project_task \
  data/benchmarks/python_projects/pydata__xarray-3095.json \
  --model <litellm-model-id> --output artifacts/results/xarray-3095.json

# Chạy pilot 30 bài ở cả baseline và framework
python -m experiments.run_project_suite --model <litellm-model-id> \
  --workers 2 --output-dir artifacts/results/python_pilot
```

Mỗi manifest Python ghim commit gốc và issue. Script nhập tập từ revision cố định của SWE-bench Verified, **không lưu bản vá đáp án**. Từng lượt chạy clone vào thư mục tạm, gửi context có giới hạn cho mô hình, áp dụng diff và lưu bằng chứng các tệp đã cung cấp. Baseline và framework cùng giới hạn tối đa ba lượt: baseline không nhận phản hồi kiểm tra, framework nhận lỗi áp dụng bản vá hoặc lỗi cú pháp. Với tác vụ SWE-bench, vòng sửa chỉ dùng phản hồi cú pháp công khai. **Không đưa kết quả bài kiểm tra ẩn cho agent trong vòng sửa.**

`--workers` chỉ chạy song song các case độc lập (DafnyBench: 1–8, Python pilot: 1–4, tập Dafny cũ qua `run_benchmark`: 1–8); mặc định CLI là `1` để giữ cách chạy tuần tự cũ. Trên giao diện, chế độ **Hàng loạt** của 35 bài Dafny cũ có thanh **Số bài chạy song song** (1–4), mặc định `2` cho cloud và `1` cho Ollama. Hãy giảm về `1` nếu gặp giới hạn lượt gọi; song song không rút ngắn thời gian của một case đơn lẻ và có thể tăng tải CPU/API. Kết quả xuất theo thứ tự manifest; bộ đếm token Gemini/Groq được đồng bộ khi nhiều worker cùng ghi.

Khi đo lại thời gian của pilot Python, dùng `--output-dir` mới: lệnh suite sẽ tiếp tục từ báo cáo đã có trong thư mục cũ thay vì gọi mô hình lại. Báo cáo có sẵn chỉ được tái sử dụng nếu task, mô hình, mode và giới hạn lượt sửa trùng khớp.

Để chấm bản vá Python, cài SWE-bench và chạy Docker. Có thể dùng `--grade` ở lệnh suite hoặc `--swebench-eval` ở lệnh một bài; trên máy ARM nên cung cấp `--swebench-task-repo` theo hướng dẫn của SWE-bench. Với kết quả nghiên cứu tái lập, xuất dataset đánh giá đúng revision đã ghim rồi truyền đường dẫn đó qua `--swebench-dataset`. Tệp riêng này có đáp án và test patch, nằm trong `artifacts/private/` (Git bỏ qua) và **không được gửi cho agent**. Giá trị mặc định `verified` dùng phiên bản do SWE-bench cài đặt cung cấp, có thể thay đổi theo thời gian. Bộ chấm chính thức có thể cần nhiều bộ nhớ và dung lượng đĩa. Khi chưa chạy Docker, báo cáo ghi `python_tests: pending_swebench_harness`, không ghi `passed`. Báo cáo phân biệt bài thất bại với lỗi bộ chấm, bản vá rỗng và bài chưa chạy.

```bash
python -m experiments.export_pinned_swebench_eval

python -m experiments.run_project_suite --model <litellm-model-id> \
  --output-dir artifacts/results/python_pilot --grade \
  --swebench-dataset artifacts/private/swebench_verified_pinned30.jsonl \
  --swebench-task-repo /path/to/swe-bench-tasks

python -m experiments.evaluate_project_reports \
  artifacts/results/python_pilot --output artifacts/results/python_pilot_summary.json
```

Chỉ so sánh hai cấu hình khi cùng mô hình, commit, bộ chấm và giới hạn thời gian. Báo cáo lưu thời gian, token, chi phí nếu nhà cung cấp trả dữ liệu, checksum prompt và context. Ba cột `python_tests`, `dafny_verification`, `spec_audit` có mẫu số riêng.

## Mức độ đã kiểm tra ở mốc hiện tại

- Bộ kiểm thử phần mềm: `python -m pytest tests -q` đạt 125 bài ngày 18/10/2026; giao diện được chạy smoke test với đủ 5 tab.
- Bài Dafny đơn lẻ: [`abs_val`](../artifacts/results/benchmark_clover_20261018_005909.csv) trên Clover với `gemini-2.5-flash`, K=1, worker=1 đạt kiểm chứng trong 5,82 giây; đây là một mẫu chạy, không đại diện cho toàn bộ 35 bài. Ca `weak_gcd_nonzero` cho phản ví dụ như mong đợi.
- Chưa có báo cáo chạy đầy đủ 20 bài DafnyBench, 30 issue Python qua mô hình và Docker, hoặc phép đo so sánh thời gian trước/sau khi bật nhiều worker. Không suy ra tỷ lệ thành công hay mức tăng tốc từ các smoke test.

## Đặc tả Dafny cho mã Python

Dafny không kiểm chứng trực tiếp mã Python. Nếu một tác vụ có mô hình Dafny được chuyên gia duyệt, manifest mới được thêm `formal_files`, `protected_files` và `formal_review_status: "reviewed"`. Khi đó framework chạy `dafny verify` và `dafny audit` riêng trên mô hình. Kết quả chỉ chứng minh thuộc tính của mô hình Dafny; muốn tuyên bố tương đương với bản vá Python phải bổ sung cầu nối ngữ nghĩa được kiểm chứng. Các thuộc tính chưa duyệt không được tính vào tỷ lệ chứng minh.

## Tái lập dữ liệu

- `python -m experiments.import_swebench_subset` tải lại 30 manifest từ revision đã ghim của SWE-bench Verified.
- `python -m experiments.export_pinned_swebench_eval` tạo tập dữ liệu chấm riêng cùng revision và ghi SHA-256 để đối chiếu; không đưa tệp này vào mã nguồn hoặc prompt.
- `python -m experiments.import_dafnybench20` tải lại 20 file thiếu gợi ý từ commit đã ghim và kiểm tra mỗi bản gốc xác minh được bằng Dafny.
- Dùng `python -m unittest tests.test_project_framework -v` để kiểm tra luồng bản vá nhiều tệp mà không gọi API.

Nguồn dữ liệu và cách chấm: [DafnyBench](https://github.com/sun-wendy/DafnyBench), [SWE-bench](https://github.com/SWE-bench/SWE-bench), [Dafny Reference](https://dafny.org/latest/DafnyRef/DafnyRef.html).
