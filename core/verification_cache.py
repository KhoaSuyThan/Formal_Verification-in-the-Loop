"""Bộ nhớ đệm xác minh toán học SMT (SMT Verification Memoization Cache).

Lưu trữ và tái sử dụng kết quả kiểm định của Dafny CLI / Z3 SMT Solver dựa trên
mã băm SHA-256 của nội dung mã nguồn Dafny và cấu hình kiểm định.
Đảm bảo an toàn đa luồng (Thread-Safe) cho môi trường chạy song song.
"""

import os
import json
import hashlib
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from core.dafny_engine import VerifyResult


class VerificationCache:
    """Bộ nhớ đệm lưu trữ kết quả kiểm định hình thức SMT."""

    def __init__(self, cache_file: Optional[str] = None):
        """Khởi tạo bộ nhớ đệm với đường dẫn lưu trữ JSON kiên cố."""
        if cache_file:
            self.cache_path = Path(cache_file)
        else:
            project_root = Path(__file__).resolve().parent.parent
            self.cache_path = project_root / "artifacts" / "cache" / "smt_verification_cache.json"

        self._lock = threading.Lock()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._load()

    def _compute_key(self, code: str, extract_counterexample: bool) -> str:
        """Tạo khóa băm tất định (deterministic hash key) từ mã nguồn và cờ kiểm định."""
        normalized_code = code.strip().replace("\r\n", "\n")
        raw_key = f"ce={extract_counterexample}:::{normalized_code}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, code: str, extract_counterexample: bool = True) -> Optional[VerifyResult]:
        """Truy xuất kết quả kiểm định từ bộ nhớ đệm nếu đã tồn tại."""
        key = self._compute_key(code, extract_counterexample)
        with self._lock:
            if key in self._cache:
                self._hits += 1
                data = self._cache[key]
                return VerifyResult(
                    is_verified=data["is_verified"],
                    return_code=data["return_code"],
                    output=data["output"],
                    error_summary=data.get("error_summary", "")
                )
            self._misses += 1
            return None

    def set(self, code: str, extract_counterexample: bool, result: VerifyResult) -> None:
        """Ghi nhận kết quả kiểm định mới vào bộ nhớ đệm và lưu trữ xuống đĩa."""
        key = self._compute_key(code, extract_counterexample)
        with self._lock:
            self._cache[key] = {
                "is_verified": result.is_verified,
                "return_code": result.return_code,
                "output": result.output,
                "error_summary": result.error_summary
            }
            self._save_unsafe()

    def _save_unsafe(self) -> None:
        """Ghi dữ liệu ra tệp tin JSON (hàm nội bộ, yêu cầu đã giữ lock)."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CẢNH BÁO CACHE]: Không thể lưu cache: {e}")

    def _load(self) -> None:
        """Nạp dữ liệu cache từ tệp tin JSON nếu tồn tại."""
        with self._lock:
            if self.cache_path.exists():
                try:
                    with open(self.cache_path, "r", encoding="utf-8") as f:
                        self._cache = json.load(f)
                except Exception as e:
                    print(f"[CẢNH BÁO CACHE]: Không thể nạp cache: {e}")
                    self._cache = {}
            else:
                self._cache = {}

    def clear(self) -> None:
        """Xóa toàn bộ dữ liệu trong bộ nhớ đệm."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            if self.cache_path.exists():
                try:
                    os.remove(self.cache_path)
                except Exception:
                    pass

    def stats(self) -> Dict[str, Any]:
        """Trả về thống kê số lượt hit, miss và tỷ lệ hit của cache."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = round(self._hits / total * 100, 1) if total > 0 else 0.0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total,
                "cached_items": len(self._cache),
                "hit_rate_percent": hit_rate
            }
