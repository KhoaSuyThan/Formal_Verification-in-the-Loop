"""Module tương tác với Dafny CLI để thực hiện kiểm định logic hình thức.

Sử dụng subprocess để gọi bộ giải Z3 tích hợp sẵn trong Dafny 4.x.
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any


# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

# Tải cấu hình biến môi trường từ .env
load_dotenv()


@dataclass
class VerifyResult:
    """Kết quả phản hồi từ trình kiểm định Dafny."""
    is_verified: bool
    return_code: int
    output: str
    error_summary: str = ""


class DafnyEngine:
    """Bộ điều khiển gọi trình kiểm định Dafny qua CLI."""

    def __init__(
        self,
        timeout_sec: int = 15,
        dafny_path: Optional[str] = None,
        cache: Optional[Any] = None,
    ):
        """Khởi tạo engine với thời gian timeout, đường dẫn Dafny và bộ nhớ đệm kiểm định SMT."""
        self.timeout = timeout_sec
        self.cache = cache
        resolved_path = (
            dafny_path
            or os.getenv("DAFNY_PATH")
            or shutil.which("dafny")
        )

        # Nếu chưa tìm thấy, tự động tìm kiếm trong thư mục tools/dafny nội bộ của dự án
        if not resolved_path or not (shutil.which(resolved_path) or Path(resolved_path).is_file()):
            project_root = Path(__file__).resolve().parent.parent
            for candidate in [
                project_root / "tools" / "dafny" / "Dafny.exe",
                project_root / "tools" / "dafny" / "dafny.exe",
                project_root / "tools" / "dafny" / "dafny"
            ]:
                if candidate.is_file():
                    resolved_path = str(candidate)
                    break

        self.dafny_bin = resolved_path

    def is_available(self) -> bool:
        """Kiểm tra Dafny CLI đã sẵn sàng trên hệ thống hay chưa."""
        if not self.dafny_bin:
            return False
        return shutil.which(self.dafny_bin) is not None or Path(self.dafny_bin).is_file()

    def verify(self, code: str, extract_counterexample: bool = True) -> VerifyResult:
        """Ghi mã nguồn ra file tạm và gọi Dafny verify để kiểm tra tính đúng đắn.
        
        Khi extract_counterexample=True, kích hoạt cờ --extract-counterexample của Z3
        để trích xuất trạng thái dữ liệu vi phạm thực tế phục vụ cơ chế tự sửa lỗi CEGAR (arXiv:2506.06923).
        Tự động truy xuất từ SMT Cache nếu đã từng kiểm tra đoạn mã này.
        """
        # Kiểm tra bộ nhớ đệm SMT trước khi gọi tiến trình nặng
        if self.cache is not None:
            cached_res = self.cache.get(code, extract_counterexample)
            if cached_res is not None:
                return cached_res

        if not self.is_available():
            raise EnvironmentError(
                "Dafny chưa được cài đặt hoặc chưa được cấu hình đường dẫn. "
                "Vui lòng cài đặt Dafny 4.x và thêm vào PATH hoặc đặt biến môi trường DAFNY_PATH."
            )

        # Tạo file tạm thời an toàn chứa mã nguồn cần kiểm định
        with tempfile.NamedTemporaryFile(mode="w", suffix=".dfy", delete=False, encoding="utf-8") as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(code)

        try:
            cmd = [str(self.dafny_bin), "verify", "--allow-warnings"]
            if extract_counterexample:
                cmd.append("--extract-counterexample")
            cmd.extend(["--verification-time-limit", str(self.timeout), str(tmp_path)])
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 5,
                encoding="utf-8",
                errors="replace"
            )

            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
            combined_output = stdout + ("\n" + stderr if stderr else "")

            # Trong Dafny 4.x, kết quả thành công xuất hiện dòng '0 errors'
            verified = (proc.returncode == 0) and ("0 errors" in stdout)

            result = VerifyResult(
                is_verified=verified,
                return_code=proc.returncode,
                output=combined_output if not verified else stdout,
                error_summary="" if verified else "Lỗi kiểm định logic hoặc cú pháp"
            )

            # Ghi nhận kết quả vào bộ nhớ đệm SMT
            if self.cache is not None:
                self.cache.set(code, extract_counterexample, result)

            return result
        except subprocess.TimeoutExpired:
            timeout_res = VerifyResult(
                is_verified=False,
                return_code=-1,
                output="Timeout: Bộ giải Z3 vượt quá thời gian cho phép.",
                error_summary="SolverTimeout"
            )
            if self.cache is not None:
                self.cache.set(code, extract_counterexample, timeout_res)
            return timeout_res
        finally:
            # Dọn dẹp file tạm thời sau khi hoàn tất kiểm tra
            if tmp_path.exists():
                tmp_path.unlink()
