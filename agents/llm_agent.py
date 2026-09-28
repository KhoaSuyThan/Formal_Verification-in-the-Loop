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
        temperature: float = 0.2
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
            "max_tokens": 1024,
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
            "Chỉ dùng phép gán trực tiếp: `name := giá_trị;`. TUYỆT ĐỐI KHÔNG dùng câu lệnh `return name;`.\n"
            "- Tham số đầu vào (in-parameters): Mọi tham số đầu vào trong khai báo `method (a: int, b: int)` là HẰNG SỐ BẤT BIẾN (immutable). "
            "TUYỆT ĐỐI KHÔNG gán lại giá trị cho tham số đầu vào (như `a := -a;`). "
            "Nếu cần thay đổi, BẮT BUỘC phải tạo biến cục bộ sao chép: `var cur_a := a; var cur_b := b;` rồi thao tác trên biến cục bộ.\n"
            "- Giữ nguyên vẹn toàn bộ các mệnh đề ensures gốc và tất cả các hàm phụ trợ (function, predicate, lemma).\n"
            "- Câu lệnh rẽ nhánh: Dùng `if điều_kiện { ... } else { ... }` (KHÔNG dùng từ khóa `then` trong method).\n"
            "- Vòng lặp: Bắt buộc dùng `while` (KHÔNG dùng từ khóa `loop` hoặc `for`).\n"
            "- Mệnh đề `invariant` và `decreases` BẮT BUỘC phải đặt ngay TRƯỚC dấu mở ngoặc `{` của vòng lặp `while` (KHÔNG đặt bên trong thân vòng lặp).\n"
            "- Biên của vòng lặp và bất biến: Với `while i <= n`, sau bước nhảy `i := i + 1` giá trị `i` sẽ đạt tới `n + 1`, "
            "do đó bất biến cận trên BẮT BUỘC phải là `invariant 0 <= i <= n + 1` (nếu để `i <= n` sẽ bị lỗi loop invariant could not be proved to be maintained).\n"
            "- Khi duyệt mảng/chuỗi: Luôn luôn có `invariant 0 <= i <= |s|` (hoặc `a.Length`) để Z3 đảm bảo an toàn truy xuất chỉ số (tránh OutOfBounds).\n"
            "- Bất biến định lượng: Nếu tìm kiếm/tính toán phần tử lớn nhất/nhỏ nhất trong chuỗi `l` (như bài tìm max), "
            "hãy khởi tạo từ phần tử đầu tiên (`var max := l[0]; var i := 1;`) và vòng lặp BẮT BUỘC cần CẢ 3 invariant song song: "
            "1) `invariant 1 <= i <= |l|` (chặn biên chỉ số), "
            "2) `invariant forall j :: 0 <= j < i ==> l[j] <= max` (chứng minh tính chất max cho các phần tử đã duyệt), "
            "3) `invariant exists j :: 0 <= j < i && l[j] == max` (chứng minh max luôn là phần tử thuộc mảng).\n"
            "- Không có method .max() hay .min() trên seq: Trong Dafny, kiểu `seq<T>` KHÔNG CÓ phương thức `.max()` hay `.min()`. "
            "BẮT BUỘC dùng định lượng `forall` như trên.\n"
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
            f"CHI TIẾT CHẨN ĐOÁN LỖI TỪ BỘ KIỂM ĐỊNH FORMAL VERIFICATION:\n"
            f"{error_msg}\n\n"
            f"QUY TẮC SỬA LỖI ĐẶC THÙ THEO NGỮ NGHĨA DAFNY:\n"
            f"1. Nếu lỗi 'LoopInvariantViolation' và 'maintained by the loop':\n"
            f"   - Bước nhảy `i := i + 1` làm vượt biên invariant. Với `while i <= n`, sửa thành `invariant 0 <= i <= n + 1`.\n"
            f"2. Nếu lỗi 'LoopInvariantViolation' và 'proved on entry':\n"
            f"   - Invariant sai ngay từ đầu. Kiểm tra giá trị khởi tạo. Nếu dùng `exists j :: 0 <= j < i`, hãy đổi thành `(i > 0 ==> exists ...)` hoặc bắt đầu từ `i := 1`.\n"
            f"3. Nếu lỗi 'LHS of assignment must denote a mutable variable':\n"
            f"   - Tham số đầu vào của method là immutable. Hãy khai báo biến cục bộ sao chép: `var cur_a := a; var cur_b := b;` rồi thao tác trên chúng.\n"
            f"4. Nếu lỗi 'a postcondition could not be proved on this return path':\n"
            f"   - Thiếu invariant quy nạp trong vòng lặp. Cần thêm invariant mô tả mối quan hệ giữa biến lặp và hậu điều kiện ensures (ví dụ fib, quy nạp duyệt mảng).\n"
            f"5. Nếu lỗi 'OutOfBounds' (index out of range):\n"
            f"   - Cần thêm `invariant 0 <= i <= |s|` (hoặc `a.Length`) trước vòng lặp.\n"
            f"6. Nếu lỗi 'type seq<?> does not have a member max':\n"
            f"   - Kiểu `seq` không có method `.max()`. Hãy dùng định lượng: `invariant forall j :: 0 <= j < i ==> l[j] <= max`.\n"
            f"7. NGUYÊN TẮC GIỮ NGUYÊN CÁC INVARIANT ĐÃ CÓ:\n"
            f"   - Khi bổ sung một invariant mới theo hướng dẫn, BẮT BUỘC PHẢI GIỮ LẠI các invariant đã có trước đó (KHÔNG được xóa hoặc thay thế invariant cũ). Vòng lặp thường cần NHIỀU invariant đồng thời (ví dụ: vừa cần invariant chặn biên `0 <= i <= |s|`, vừa cần `invariant forall ...`, vừa cần `invariant exists ...`).\n"
            f"8. TUYỆT ĐỐI KHÔNG THAY ĐỔI HOẶC XÓA BỎ các điều kiện ensures sau:\n{original_spec}\n\n"
            f"Hãy trả về toàn bộ mã Dafny hoàn chỉnh ĐÃ ĐƯỢC SỬA LỖI (lưu ý: KHÔNG bao gồm tiền tố số dòng `1 | `) trong cặp thẻ ```dafny ... ```."
        )
        return self._call_model(system_prompt, user_prompt)

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Loại bỏ các định dạng markdown và thẻ suy nghĩ <think> để trích xuất mã thuần."""
        # Loại bỏ chuỗi suy luận trong thẻ <think>...</think> nếu có
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # Ưu tiên bóc tách thẻ ```dafny
        match_dafny = re.search(r'```dafny\s*(.*?)\s*```', text, flags=re.DOTALL | re.IGNORECASE)
        if match_dafny:
            return match_dafny.group(1).strip()

        # Nếu không có thẻ dafny, thử bóc tách thẻ ``` thông thường
        match_generic = re.search(r'```\w*\s*(.*?)\s*```', text, flags=re.DOTALL)
        if match_generic:
            return match_generic.group(1).strip()

        return text.strip()
