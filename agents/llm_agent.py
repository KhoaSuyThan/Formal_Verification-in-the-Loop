"""Module điều khiển Agent LLM tương tác qua thư viện LiteLLM.

Hỗ trợ mô hình chạy cục bộ (Ollama) và các mô hình trên đám mây (DeepSeek, OpenAI, Claude).
"""

import os
import re
from typing import Optional
import litellm
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

    def _call_model(self, system_prompt: str, user_prompt: str, timeout_sec: int = 120) -> str:
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
            "Nhiệm vụ của bạn là hoàn thiện thân hàm Dafny sao cho thỏa mãn 100% các điều kiện ensures. "
            "QUY TẮC BẮT BUỘC:\n"
            "- Giữ nguyên vẹn toàn bộ các mệnh đề ensures gốc.\n"
            "- Chỉ trả về duy nhất khối mã nguồn Dafny hoàn chỉnh nằm trong cặp thẻ ```dafny ... ```.\n"
            "- Không thêm bất kỳ lời giải thích văn bản nào bên ngoài mã nguồn."
        )
        return self._call_model(system_prompt, prompt)

    def repair_code(self, code: str, error_msg: str, original_spec: str) -> str:
        """Sửa mã nguồn Dafny dựa trên phản hồi lỗi từ Z3 Solver."""
        system_prompt = (
            "Bạn là chuyên gia vá lỗi và chứng minh tính đúng đắn cho mã nguồn Dafny 4.x. "
            "Chỉ trả về duy nhất khối mã Dafny hoàn chỉnh đã được sửa trong thẻ ```dafny ... ```, "
            "không giải thích gì thêm."
        )
        user_prompt = (
            f"Mã nguồn Dafny sau đây đã thất bại khi kiểm định với Z3 Solver:\n"
            f"```dafny\n{code}\n```\n\n"
            f"Chi tiết thông báo lỗi từ bộ kiểm định:\n{error_msg}\n\n"
            f"YÊU CẦU SỬA ĐỔI:\n"
            f"1. Sửa lại thân hàm, cập nhật biến phụ trợ hoặc bổ sung bất biến vòng lặp (loop invariant / decreases) nếu cần.\n"
            f"2. TUYỆT ĐỐI KHÔNG ĐƯỢC THAY ĐỔI HOẶC XÓA BỎ các điều kiện ensures sau:\n{original_spec}\n"
            f"Hãy trả về toàn bộ mã Dafny hoàn chỉnh đã được sửa."
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
