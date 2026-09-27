"""Module tương tác với Dafny CLI để thực hiện kiểm định logic hình thức.

Sử dụng subprocess để gọi bộ giải Z3 tích hợp sẵn trong Dafny 4.x.
"""

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class VerifyResult:
    """Kết quả phản hồi từ trình kiểm định Dafny."""
    is_verified: bool
    return_code: int
    output: str
    error_summary: str = ""


class DafnyEngine:
    """Bộ điều khiển gọi trình kiểm định Dafny qua CLI."""

    def __init__(self, timeout_sec: int = 15, dafny_path: Optional[str] = None):
        """Khởi tạo engine với thời gian timeout và đường dẫn thực thi Dafny.

        Đường dẫn ưu tiên theo thứ tự: tham số truyền vào -> biến môi trường DAFNY_PATH -> PATH hệ thống.
        """
        self.timeout = timeout_sec
        resolved_path = (
            dafny_path
            or os.getenv("DAFNY_PATH")
            or shutil.which("dafny")
        )
        self.dafny_bin = resolved_path

    def is_available(self) -> bool:
        """Kiểm tra Dafny CLI đã sẵn sàng trên hệ thống hay chưa."""
        if not self.dafny_bin:
            return False
        return shutil.which(self.dafny_bin) is not None or Path(self.dafny_bin).is_file()

    def verify(self, code: str) -> VerifyResult:
        """Ghi mã nguồn ra file tạm và gọi Dafny verify để kiểm tra tính đúng đắn."""
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
            cmd = [str(self.dafny_bin), "verify", f"--time-limit:{self.timeout}", str(tmp_path)]
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

            return VerifyResult(
                is_verified=verified,
                return_code=proc.returncode,
                output=combined_output if not verified else stdout,
                error_summary="" if verified else "Lỗi kiểm định logic hoặc cú pháp"
            )
        except subprocess.TimeoutExpired:
            return VerifyResult(
                is_verified=False,
                return_code=-1,
                output="Timeout: Bộ giải Z3 vượt quá thời gian cho phép.",
                error_summary="SolverTimeout"
            )
        finally:
            # Dọn dẹp file tạm thời sau khi hoàn tất kiểm tra
            if tmp_path.exists():
                tmp_path.unlink()
