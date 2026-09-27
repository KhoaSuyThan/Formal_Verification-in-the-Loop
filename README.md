# Khung Sinh Mã Nguồn và Tự Sửa Lỗi Khép Kín Dựa Trên Kiểm Định Hình Thức (Formal Verification-in-the-Loop)

Dự án này là mã nguồn thực nghiệm cho đề tài Nghiên cứu Khoa học: **"Nghiên cứu khung sinh mã nguồn và tự sửa lỗi tự động loại bỏ ảo giác dựa trên kiểm định logic hình thức (Formal Verification-in-the-Loop)"**. Hệ thống triển khai đường ống Actor-Critic khép kín kết hợp các mô hình ngôn ngữ lớn (LLM) với bộ giải logic toán học tất định Dafny 4.x và Z3 SMT Solver.

---

## 1. Tổng Quan Kiến Trúc

Quy trình vận hành theo cơ chế 5 pha tự động khép kín:

```mermaid
flowchart TD
    A["[Đề bài & Đặc tả hình thức (.dfy)]"] --> B["1. Generator Agent (Sinh mã thuật toán)"]
    B --> C["2. Spec-Locking Guard (SHA-256 Hash Ensures)"]
    C -->|Hợp lệ| D["3. Dafny / Z3 Engine (Kiểm định logic hình thức)"]
    C -->|Gian lận / Đổi spec| G["Hủy kết quả / Báo vi phạm"]
    D -->|Passed 100%| E["🏆 Verified Code (Zero-Hallucination)"]
    D -->|Vi phạm Invariant / Postcondition| F["4. Diagnostic Parser (Bóc tách AST & phân loại lỗi Z3)"]
    F --> H["5. Repair Agent (Tự vá mã nguồn)"]
    H -->|Nạp lại mã đã sửa (Pass@K)| C
```

### Các nguyên lý cốt lõi:
* **Spec-Locking Protocol**: Khóa cứng toàn bộ các mệnh đề `ensures` gốc bằng mã băm SHA-256, ngăn chặn việc LLM tự ý sửa đổi hoặc nới lỏng yêu cầu bài toán để đánh lừa bộ kiểm định.
* **Deterministic Verification**: Thay thế toàn bộ các cơ chế tự chấm điểm bằng xác suất của LLM bằng công cụ toán học hình thức Dafny/Z3.
* **Error Taxonomy Parsing**: Phân loại lỗi trả về từ Z3 Solver thành các nhóm cụ thể (`PostconditionViolation`, `LoopInvariantViolation`, `TerminationFailure`, `OutOfBounds`).

---

## 2. Cấu Trúc Thư Mục Dự Án

```text
Formal_Verification-in-the-Loop/
├── configs/
│   ├── experiment_config.yaml   # Cấu hình K_max, timeout, tham số lấy mẫu
│   └── models_config.yaml       # Danh sách API endpoints và keys
├── core/
│   ├── __init__.py
│   ├── dafny_engine.py          # Wrapper tương tác với Dafny CLI qua subprocess
│   ├── spec_locker.py           # Module SHA-256 bảo vệ đặc tả toán học
│   ├── diagnostic_parser.py     # Parser bóc tách trace lỗi SMT sang JSON
│   └── pipeline_controller.py   # Bộ điều khiển vòng lặp kín Pass@K
├── agents/
│   ├── __init__.py
│   ├── base_agent.py            # Giao diện lớp cơ sở cho các LLM
│   ├── llm_agent.py             # Agent giao tiếp LiteLLM đa mô hình
│   ├── generator_agent.py       # Bộ sinh mã và chứng chỉ ban đầu
│   └── repair_agent.py          # Bộ phân tích log Z3 và vá mã nguồn
├── data/
│   ├── benchmarks/
│   │   ├── clover/              # 60 bài toán từ CloverBench (Stanford)
│   │   └── humaneval_dafny/     # 129 bài toán từ HumanEval-Dafny (JetBrains)
│   └── raw/                     # Dữ liệu đầu vào chuẩn hóa JSONL
├── experiments/
│   ├── __init__.py
│   ├── run_single_task.py       # Script chạy 1 bài toán đơn lẻ
│   ├── run_benchmark.py         # Script chạy thực nghiệm tự động hàng loạt
│   └── evaluate_metrics.py      # Module tính toán Pass@1, Pass@K, tỷ lệ hội tụ
├── artifacts/
│   ├── logs/                    # Trace chi tiết của từng lượt chứng minh Z3
│   └── results/                 # Dữ liệu xuất ra (CSV/JSON) phục vụ vẽ biểu đồ
├── run_single.py                # Script chạy thử nghiệm nhanh ở thư mục gốc
├── requirements.txt             # Danh sách thư viện phụ thuộc
├── CHANGELOG.md                 # Nhật ký thay đổi của hệ thống
└── README.md
```

---

## 3. Yêu Cầu Hệ Thống & Cài Đặt

### 3.1. Yêu cầu môi trường
* Hệ điều hành: Linux (Ubuntu 20.04+), macOS hoặc Windows 10/11.
* Python: Phiên bản 3.10 trở lên (khuyên dùng Python 3.11 - 3.13).
* Dafny: Phiên bản 4.x (tích hợp sẵn Z3 Solver).

### 3.2. Cài đặt Dafny CLI
Dafny là thành phần bắt buộc để biên dịch và kiểm định hình thức:

* **Trên Windows**:
  1. Tải bản nén `.zip` từ [Dafny Releases (GitHub)](https://github.com/dafny-lang/dafny/releases).
  2. Giải nén vào thư mục cố định (ví dụ: `C:\tools\dafny`).
  3. Thêm đường dẫn thư mục giải nén vào biến môi trường `PATH`, hoặc cấu hình trực tiếp đường dẫn qua file `.env` (`DAFNY_PATH=C:\tools\dafny\dafny.exe`).

* **Trên macOS** (Homebrew):
  ```bash
  brew install dafny
  ```

* **Trên Linux/Ubuntu**:
  ```bash
  wget https://github.com/dafny-lang/dafny/releases/download/v4.4.0/dafny-4.4.0-x64-ubuntu-20.04.zip
  unzip dafny-4.4.0-x64-ubuntu-20.04.zip
  sudo mv dafny /opt/
  sudo ln -s /opt/dafny/dafny /usr/local/bin/dafny
  ```

Kiểm tra trạng thái cài đặt:
```bash
dafny --version
# Kết quả yêu cầu: Dafny 4.x.x
```

### 3.3. Cài đặt môi trường Python
```bash
# Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate      # Trên Windows
# source venv/bin/activate # Trên Linux / macOS

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt
```

Nội dung file `requirements.txt`:
```text
litellm>=1.40.0
pydantic>=2.0.0
pyyaml>=6.0
pandas>=2.0.0
python-dotenv>=1.0.0
tqdm>=4.65.0
rich>=13.0.0
```

---

## 4. Cấu Hình Dự Án

### 4.1. Thiết lập biến môi trường API
Tạo file `.env` tại thư mục gốc (tham khảo `.env.example`):
```env
# Cloud Providers
DEEPSEEK_API_KEY="your-deepseek-api-key"
OPENAI_API_KEY="your-openai-api-key"
ANTHROPIC_API_KEY="your-claude-api-key"

# Tùy chọn đường dẫn Dafny thủ công nếu chưa thêm vào PATH
DAFNY_PATH="dafny"
```

*Lưu ý*: Nếu sử dụng mô hình local (như Qwen-2.5-Coder qua Ollama), đảm bảo Ollama daemon đang chạy ở cổng mặc định: `http://localhost:11434`.

### 4.2. File cấu hình thực nghiệm (`configs/experiment_config.yaml`)
```yaml
experiment:
  max_iterations_k: 5         # Số vòng lặp tự sửa tối đa (Pass@5)
  dafny_timeout_seconds: 15   # Giới hạn thời gian của Z3 Solver trên mỗi lượt
  random_seed: 42

models:
  generator: "deepseek/deepseek-chat"      # Hoặc: "ollama/qwen2.5-coder:7b"
  repairer: "deepseek/deepseek-chat"
  temperature: 0.2
  top_p: 0.95

dataset:
  benchmark_suite: "clover"                # Lựa chọn: "clover" hoặc "humaneval_dafny"
  sample_limit: null                       # Đặt số nguyên để test nhanh (vd: 5), để null nếu chạy full
```

---

## 5. Hướng Dẫn Vận Hành

### 5.1. Chạy thử nghiệm đơn lẻ (Single-task Verification)
Kiểm tra nhanh luồng thực thi trên 1 bài toán mẫu:
```bash
python run_single.py
```
Hoặc dùng module chi tiết:
```bash
python -m experiments.run_single_task --input_spec data/benchmarks/clover/sample_max.dfy --model deepseek/deepseek-chat --max_k 3
```

### 5.2. Chạy toàn bộ Benchmark tự động
Lệnh này duyệt qua các bài toán trong tập benchmark được chọn, tự động ghi nhận kết quả và log chẩn đoán:
```bash
python -m experiments.run_benchmark --config configs/experiment_config.yaml
```

---

## 6. Chỉ Số Đánh Giá & Báo Cáo (Metrics)

Sau khi hoàn thành thử nghiệm, chạy lệnh sau để kết xuất bảng tổng hợp:
```bash
python -m experiments.evaluate_metrics --results_dir artifacts/results/
```

Các chỉ số đầu ra bao gồm:
1. **Pass@1 (Zero-shot Mathematical Accuracy)**: Tỷ lệ bài toán vượt qua kiểm định hình thức ngay tại lần sinh đầu tiên.
2. **Pass@K (K ∈ {3, 5})**: Tỷ lệ bài toán giải quyết thành công sau tối đa K lần sửa đổi có định hướng.
3. **Repair Success Rate (RSR)**: Tỷ lệ sửa lỗi thành công trên tập các bài toán ban đầu bị Dafny từ chối.
4. **Error Distribution Matrix**: Thống kê tỷ lệ các nhóm lỗi logic xuất hiện trong quá trình thực nghiệm.

---

## 7. Tài Liệu Tham Khảo Nền Tảng

1. **Clover**: Sun, C. et al. (Stanford University, 2024). *Clover: Closed-Loop Verifiable Code Generation*. arXiv:2310.17807.
2. **HumanEval-Dafny**: JetBrains Research (2024). *Benchmark kiểm định hình thức cho các bài toán thuật toán*.
3. **Dafny Language & Z3 Solver**: Leino, K. R. M. (Microsoft Research). *Dafny: An Automatic Program Verifier for Functional Correctness*.