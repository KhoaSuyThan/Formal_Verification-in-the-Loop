"""Module điều khiển Agent LLM tương tác qua thư viện LiteLLM.

Hỗ trợ mô hình chạy cục bộ (Ollama) và các mô hình trên đám mây (DeepSeek, OpenAI, Claude).
"""

import os
import re
from typing import Optional, Tuple
# pyrefly: ignore [missing-import]
import litellm
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from core.cot_extractor import extract_cot_trace

# Tải các biến môi trường từ file .env nếu có
load_dotenv()


class LLMAgent:
    """Agent LLM thực hiện sinh mã và sửa lỗi logic Dafny."""

    def __init__(
        self,
        model_name: str = "ollama/qwen2.5-coder:7b",
        api_base: Optional[str] = None,
        temperature: float = 0.0,
        timeout_sec: int = 180
    ):
        """Khởi tạo agent với model, cấu hình kết nối và thời gian timeout."""
        self.model = model_name
        self.temperature = temperature
        self.timeout_sec = timeout_sec
        # Lưu vết chuỗi suy luận CoT và số token tương ứng của lượt sinh mã gần nhất
        self.last_cot_trace: str = ""
        self.last_cot_tokens: int = 0
        # Mặc định cấu hình api_base cho Ollama nếu model bắt đầu bằng ollama/
        if api_base:
            self.api_base = api_base
        elif model_name.startswith("ollama/"):
            self.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        else:
            self.api_base = None

    def _call_gemini_rest(self, system_prompt: str, user_prompt: str, timeout_sec: int = 120) -> Optional[str]:
        """Gọi trực tiếp Google Generative Language v1beta REST API cho các dòng mô hình Gemini."""
        import requests
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        # Chuẩn hóa tên model: loại bỏ tiền tố 'gemini/' nếu có
        raw_name = self.model
        if raw_name.startswith("gemini/"):
            raw_name = raw_name[len("gemini/"):]
        elif raw_name.startswith("models/"):
            raw_name = raw_name[len("models/"):]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{raw_name}:generateContent?key={api_key}"
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        payload = {
            "contents": [
                {"parts": [{"text": combined_prompt}]}
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 8192
            }
        }
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                res = requests.post(url, json=payload, timeout=timeout_sec)
                if res.status_code == 200:
                    data = res.json()

                    # Ghi nhận chính xác lượng token từ máy chủ Google (bao gồm cả thoughts token)
                    usage = data.get("usageMetadata", {})
                    p_tok = usage.get("promptTokenCount", 0)
                    c_tok = usage.get("candidatesTokenCount", 0)
                    t_tok = usage.get("totalTokenCount", p_tok + c_tok)
                    if p_tok or c_tok or t_tok:
                        try:
                            from core.token_tracker import record_gemini_tokens
                            record_gemini_tokens(p_tok, c_tok, t_tok)
                        except Exception as err:
                            print(f"[CẢNH BÁO TOKEN]: {err}")

                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            raw_text = parts[0]["text"]
                            clean_code, cot_trace, cot_tokens = extract_cot_trace(raw_text)
                            self.last_cot_trace = cot_trace
                            self.last_cot_tokens = cot_tokens
                            return clean_code
                elif res.status_code == 429:
                    # Trích xuất thời gian chờ chuẩn xác theo yêu cầu từ Google AI Studio
                    wait_time = 35
                    try:
                        err_json = res.json()
                        details = err_json.get("error", {}).get("details", [])
                        for d in details:
                            if "retryDelay" in d:
                                wait_time = int(d["retryDelay"].rstrip("s")) + 2
                                break
                    except Exception:
                        pass
                    print(f"[CẢNH BÁO GEMINI 429]: Hạn ngạch Google yêu cầu giãn cách {wait_time}s, đang tự động chờ để thử lại (lần {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[CẢNH BÁO GEMINI REST]: HTTP {res.status_code} - {res.text[:200]}")
                    break
            except Exception as e:
                print(f"[CẢNH BÁO GEMINI REST]: Gặp lỗi kết nối: {e}")
                time.sleep(3)
        self.last_cot_trace = ""
        self.last_cot_tokens = 0
        return ""

    def _call_model(self, system_prompt: str, user_prompt: str, timeout_sec: Optional[int] = None) -> str:
        """Thực hiện gọi API thông qua litellm.completion hoặc REST API với cơ chế timeout an toàn."""
        actual_timeout = timeout_sec if timeout_sec is not None else getattr(self, "timeout_sec", 180)

        # Gọi trực tiếp REST API độc lập cho họ mô hình Gemini (chống lỗi Vertex AI)
        if "gemini" in self.model.lower():
            return self._call_gemini_rest(system_prompt, user_prompt, timeout_sec=actual_timeout) or ""

        # Tối ưu hóa: max_tokens = 1024 giúp Ollama sinh mã ngắn gọn (15-20s), riêng DeepSeek-R1 giữ 8192 cho CoT
        effective_max_tokens = 8192 if "deepseek" in self.model.lower() else 1024
        effective_timeout = max(actual_timeout, 240) if "deepseek" in self.model.lower() else actual_timeout

        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": effective_max_tokens,
            "timeout": effective_timeout
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base

        try:
            response = litellm.completion(**kwargs)
            msg = response.choices[0].message
            raw_text = msg.content or ""
            # Một số phiên bản LiteLLM/Ollama tách riêng chuỗi suy nghĩ vào trường reasoning_content
            reasoning = getattr(msg, "reasoning_content", None) or ""
            if reasoning and "<think>" not in raw_text:
                raw_text = f"<think>\n{reasoning}\n</think>\n\n{raw_text}"

            clean_code, cot_trace, cot_tokens = extract_cot_trace(raw_text)
            self.last_cot_trace = cot_trace
            self.last_cot_tokens = cot_tokens
            return clean_code
        except Exception as e:
            print(f"\n[CẢNH BÁO LLM]: Gặp lỗi/timeout khi gọi mô hình {self.model}: {e}")
            self.last_cot_trace = ""
            self.last_cot_tokens = 0
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
            "- Giữ nguyên vẹn 100% tất cả các mệnh đề ensures gốc và tất cả các hàm phụ trợ (function, predicate, lemma). TUYỆT ĐỐI KHÔNG tự ý thêm, bớt hoặc sửa đổi bất kỳ mệnh đề ensures nào, chỉ hoàn thiện thân method bên trong `{ ... }`.\n"
            "- Hoàn thiện toàn bộ thân hàm và đóng ngoặc nhọn `}` đầy đủ, TUYỆT ĐỐI KHÔNG dừng dở dang giữa chừng.\n"
            "- Câu lệnh rẽ nhánh: Dùng `if điều_kiện { ... } else { ... }` (KHÔNG dùng từ khóa `then` trong method).\n"
            "- Vòng lặp: Bắt buộc dùng `while` (KHÔNG dùng từ khóa `loop` hoặc `for`).\n"
            "- Mệnh đề `invariant` và `decreases` BẮT BUỘC phải đặt ngay TRƯỚC dấu mở ngoặc `{` của vòng lặp `while` (KHÔNG đặt bên trong thân vòng lặp).\n"
            "- Bảo chứng dừng (Total Correctness): Mọi vòng lặp while BẮT BUỘC phải có mệnh đề `decreases <ranking_function>` để chứng minh tính dừng toán học (ví dụ: `decreases n - i` hoặc `decreases |s| - i` khi lặp tiến `i < n`; `decreases i` khi lặp lùi `i > 0`; `decreases high - low` khi tìm kiếm nhị phân; `decreases b` khi lặp Euclid `b > 0`). Biểu thức decreases phải luôn >= 0 tại mỗi vòng lặp.\n"
            "- Thao tác mảng (In-place Array): Nếu method nhận tham số `a: array<T>` và có câu lệnh gán in-place `a[i] := val;`, method header BẮT BUỘC phải có mệnh đề `modifies a` (ví dụ: `method Foo(a: array<int>) modifies a`). Đối với kiểu `seq<T>` là bất biến, KHÔNG dùng modifies mà dùng cú pháp functional update `s := s[i := val];`.\n"
            "- Biên của vòng lặp và bất biến: Khi duyệt `while i < n` (hoặc `while i < |s|`), sau khi vòng lặp kết thúc thì `i == n`. "
            "Bất biến cận trên BẮT BUỘC là `invariant 0 <= i <= n` (hoặc `0 <= i <= |s|`). "
            "Gán giá trị cho biến kết quả ngõ ra phù hợp với phạm vi biến (scope) trước khi thoát hàm.\n"
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
        clean_code, _, _ = extract_cot_trace(text)
        return clean_code

