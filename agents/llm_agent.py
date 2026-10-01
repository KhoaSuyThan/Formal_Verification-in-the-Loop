"""Module điều khiển Agent LLM tương tác qua thư viện LiteLLM.

Hỗ trợ mô hình chạy cục bộ (Ollama) và các mô hình trên đám mây (DeepSeek, OpenAI, Claude).
"""

import os
import re
from typing import Optional
# pyrefly: ignore [missing-import]
import litellm
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env nếu có
load_dotenv()


class LLMAgent:
    """Agent LLM thực hiện sinh mã và sửa lỗi logic Dafny."""

    def __init__(
        self,
        model_name: str = "ollama/qwen2.5-coder:7b",
        api_base: Optional[str] = None,
        temperature: float = 0.0
    ):
        """Khởi tạo agent với model và cấu hình kết nối."""
        self.model = model_name
        self.temperature = temperature
        # Mặc định cấu hình api_base cho Ollama nếu model bắt đầu bằng ollama/
        if api_base:
            self.api_base = api_base
        elif model_name.startswith("ollama/"):
            self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        else:
            self.api_base = None

    def _call_model(self, system_prompt: str, user_prompt: str, timeout_sec: int = 240) -> str:
        """Thực hiện gọi API thông qua litellm.completion có giới hạn thời gian và số token an toàn."""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 2048,
            "timeout": timeout_sec
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            response = litellm.completion(**kwargs)
            raw_text = response.choices[0].message.content or ""
            return self._clean_markdown(raw_text)
        except Exception as e:
            print(f"\n[CẢNH BÁO LLM]: Gặp lỗi/timeout khi gọi mô hình {self.model}: {e}")
            # Trả về chuỗi rỗng để hệ thống ghi nhận lỗi logic thay vì làm sập chương trình
            return ""

    def generate_code(self, prompt: str) -> str:
        """Sinh mã nguồn thuật toán Dafny từ đặc tả bài toán ban đầu."""
        system_prompt = (
            "Bạn là chuyên gia lập trình và kiểm định hình thức Dafny 4.x. "
            "Nhiệm vụ của bạn là hoàn thiện thân hàm Dafny sao cho thỏa mãn 100% các điều kiện ensures.\n"
            "QUY TẮC CÚ PHÁP VÀ NGỮ NGHĨA DAFNY 4.X BẮT BUỘC:\n"
            "- Biến ngõ ra (returns out-parameters): Mọi biến trong `returns (name: Type)` ĐÃ ĐƯỢC KHAI BÁO SẴN trong phạm vi hàm. "
            "TUYỆT ĐỐI KHÔNG khai báo lại bằng `var name: Type := ...` (sẽ bị lỗi Duplicate local-variable name). "
            "Chỉ dùng phép gán trực tiếp: `name := giá_trị;`. Có thể dùng câu lệnh `return;` đơn lẻ (không kèm tham số) hoặc `break;` để sớm thoát khỏi vòng lặp khi đã tìm thấy kết quả. TUYỆT ĐỐI KHÔNG dùng câu lệnh `return name;`.\n"
            "- Tham số đầu vào (in-parameters): Mọi tham số đầu vào trong khai báo `method (a: int, b: int)` là HẰNG SỐ BẤT BIẾN (immutable). "
            "TUYỆT ĐỐI KHÔNG gán lại giá trị cho tham số đầu vào (như `a := -a;`). "
            "Nếu cần thay đổi, BẮT BUỘC phải tạo biến cục bộ sao chép: `var cur_a := a; var cur_b := b;` rồi thao tác trên biến cục bộ.\n"
            "- Giữ nguyên vẹn toàn bộ các mệnh đề ensures gốc và tất cả các hàm phụ trợ (function, predicate, lemma).\n"
            "- Câu lệnh rẽ nhánh: Dùng `if điều_kiện { ... } else { ... }` (KHÔNG dùng từ khóa `then` trong method).\n"
            "- Vòng lặp: Bắt buộc dùng `while` (KHÔNG dùng từ khóa `loop` hoặc `for`).\n"
            "- Mệnh đề `invariant` và `decreases` BẮT BUỘC phải đặt ngay TRƯỚC dấu mở ngoặc `{` của vòng lặp `while` (KHÔNG đặt bên trong thân vòng lặp).\n"
            "- Biên của vòng lặp và bất biến: Khi duyệt `while i < n` (hoặc `while i < |s|`), sau khi vòng lặp kết thúc thì `i == n`. "
            "Bất biến cận trên BẮT BUỘC là `invariant 0 <= i <= n` (hoặc `0 <= i <= |s|`). "
            "Biến kết quả thường được gán sau khi vòng lặp kết thúc (`result := a;`).\n"
            "- Khi duyệt mảng/chuỗi: Luôn luôn có `invariant 0 <= i <= |s|` (hoặc `a.Length`) để Z3 đảm bảo an toàn truy xuất chỉ số (tránh OutOfBounds).\n"
            "- Nguyên lý Bất biến Quy nạp Song hành (Co-existing Invariants): Khi method có đồng thời cả hậu điều kiện toàn thể `forall` và tồn tại `exists`, "
            "vòng lặp duyệt mảng/chuỗi bắt buộc cần CẢ 3 invariant song song: "
            "1) bất biến chặn biên chỉ số (`invariant 1 <= i <= |s|`), "
            "2) bất biến tiền tố `forall` chứng minh tính chất đúng trên các phần tử đã duyệt (`invariant forall j :: 0 <= j < i ==> P(j)`), "
            "3) bất biến `exists` chứng minh giá trị tích lũy hiện tại luôn thuộc tập đã duyệt (`invariant exists j :: 0 <= j < i && s[j] == acc`, với `i` khởi tạo từ 1).\n"
            "- Không có method .max() hay .min() trên seq: Trong Dafny, kiểu `seq<T>` KHÔNG CÓ phương thức built-in `.max()` hay `.min()`. "
            "Để biểu diễn giá trị tích lũy lớn nhất/nhỏ nhất, BẮT BUỘC dùng định lượng toán học tổng quát: `invariant forall j :: 0 <= j < i ==> s[j] <= acc`.\n"
            "- Ép kiểu số thực (real) và số nguyên (int): Thuộc tính `.Floor` trả về kiểu `int`. Nếu trừ với `real`, BẮT BUỘC phải ép kiểu: `(x.Floor as real)`.\n"
            "- Chỉ trả về duy nhất khối mã nguồn Dafny hoàn chỉnh nằm trong cặp thẻ ```dafny ... ```.\n"
            "- Không thêm bất kỳ lời giải thích văn bản nào bên ngoài mã nguồn."
        )
        return self._call_model(system_prompt, prompt)

    def repair_code(self, code: str, error_msg: str, original_spec: str) -> str:
        """Sửa mã nguồn Dafny dựa trên phản hồi lỗi từ Z3 Solver."""
        system_prompt = (
            "Bạn là chuyên gia vá lỗi và chứng minh tính đúng đắn cho mã nguồn Dafny 4.x. "
            "Nhiệm vụ của bạn là phân tích nguyên nhân lỗi logic toán học và sửa triệt để mã nguồn. "
            "Chỉ trả về duy nhất khối mã Dafny hoàn chỉnh đã được sửa trong thẻ ```dafny ... ```, "
            "không giải thích gì thêm."
        )

        # Đánh số dòng để LLM dễ dàng định vị vị trí lỗi mà bộ chẩn đoán chỉ ra
        numbered_lines = [f"{idx + 1:3d} | {line}" for idx, line in enumerate(code.splitlines())]
        code_with_numbers = "\n".join(numbered_lines)

        user_prompt = (
            f"Mã nguồn Dafny sau đây đã thất bại khi kiểm định với Z3 Solver:\n\n"
            f"```dafny\n{code_with_numbers}\n```\n\n"
            f"CHI TIẾT CHẨN ĐOÁN VÀ HƯỚNG DẪN KHẮC PHỤC TỪ Z3 FORMAL VERIFIER:\n"
            f"{error_msg}\n\n"
            f"YÊU CẦU SỬA MÃ:\n"
            f"1. BẮT BUỘC đọc và thực hiện chính xác '[HÀNH ĐỘNG BẮT BUỘC]' trong thông báo chẩn đoán ở trên.\n"
            f"2. Bổ sung các mệnh đề `invariant` và `decreases` cần thiết vào TRƯỚC dấu mở ngoặc `{{` của vòng lặp `while`.\n"
            f"3. TUYỆT ĐỐI KHÔNG thay đổi hoặc xóa bỏ các hàm pure function, predicate, requires, và ensures sau:\n{original_spec}\n\n"
            f"Hãy trả về toàn bộ mã Dafny hoàn chỉnh ĐÃ ĐƯỢC SỬA LỖI (lưu ý: KHÔNG bao gồm tiền tố số dòng `1 | `) trong cặp thẻ ```dafny ... ```."
        )
        return self._call_model(system_prompt, user_prompt)

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Loại bỏ các định dạng markdown và thẻ suy nghĩ <think> để trích xuất mã thuần."""
        # Loại bỏ chuỗi suy luận trong thẻ <think>...</think> nếu có
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # Bóc tách thẻ ```dafny ... ``` (hỗ trợ cả 3 hoặc nhiều hơn dấu backtick)
        match_dafny = re.search(r'`{3,}dafny\s*(.*?)(?:`{3,}|$)', text, flags=re.DOTALL | re.IGNORECASE)
        if match_dafny:
            cleaned = match_dafny.group(1).strip()
            # Xóa các dòng ``` còn sót nếu có
            cleaned = re.sub(r'^`{3,}.*$', '', cleaned, flags=re.MULTILINE)
            return cleaned.strip()

        # Thử bóc tách thẻ ``` thông thường
        match_generic = re.search(r'`{3,}\w*\s*(.*?)(?:`{3,}|$)', text, flags=re.DOTALL)
        if match_generic:
            cleaned = match_generic.group(1).strip()
            cleaned = re.sub(r'^`{3,}.*$', '', cleaned, flags=re.MULTILINE)
            return cleaned.strip()

        # Dọn dẹp dòng mở đầu nếu có dạng ```dafny
        text = re.sub(r'^`{3,}\w*\s*', '', text.strip())
        text = re.sub(r'`{3,}\s*$', '', text.strip())
        return text.strip()

