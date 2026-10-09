"""Module theo dõi và lưu trữ tích lũy số lượng token của Google Gemini API.

Lưu trữ kiên cố vào file JSON để đảm bảo số liệu không bị mất khi làm mới trang hoặc khởi động lại.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

TRACKER_FILE = os.path.join("artifacts", "results", "gemini_token_usage.json")


def get_gemini_token_usage() -> Dict[str, Any]:
    """Đọc dữ liệu lượng token Gemini đã tích lũy."""
    default_data = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_requests": 0,
        "last_updated": datetime.now().isoformat()
    }
    if not os.path.exists(TRACKER_FILE):
        return default_data

    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {**default_data, **data}
    except Exception:
        return default_data


def record_gemini_tokens(prompt_count: int, completion_count: int, total_count: int) -> Dict[str, Any]:
    """Ghi nhận và cộng dồn lượng token cho một yêu cầu Gemini vừa thực hiện."""
    current = get_gemini_token_usage()
    current["prompt_tokens"] += max(0, prompt_count)
    current["completion_tokens"] += max(0, completion_count)
    current["total_tokens"] += max(0, total_count if total_count > 0 else (prompt_count + completion_count))
    current["total_requests"] += 1
    current["last_updated"] = datetime.now().isoformat()

    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    try:
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CẢNH BÁO TOKEN TRACKER]: Không thể lưu token: {e}")

    return current


def reset_gemini_tokens() -> Dict[str, Any]:
    """Đặt lại bộ đếm token về 0."""
    reset_data = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_requests": 0,
        "last_updated": datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    try:
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(reset_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CẢNH BÁO TOKEN TRACKER]: Không thể reset token: {e}")
    return reset_data


# ==============================================================================
# BỘ THEO DÕI TOKEN CHO GROQ CLOUD API (LPU INFERENCE)
# ==============================================================================
GROQ_TRACKER_FILE = os.path.join("artifacts", "results", "groq_token_usage.json")


def get_groq_token_usage() -> Dict[str, Any]:
    """Đọc dữ liệu lượng token Groq đã tích lũy."""
    default_data = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_requests": 0,
        "last_updated": datetime.now().isoformat()
    }
    if not os.path.exists(GROQ_TRACKER_FILE):
        return default_data

    try:
        with open(GROQ_TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {**default_data, **data}
    except Exception:
        return default_data


def record_groq_tokens(prompt_count: int, completion_count: int, total_count: int) -> Dict[str, Any]:
    """Ghi nhận và cộng dồn lượng token cho một yêu cầu Groq vừa thực hiện."""
    current = get_groq_token_usage()
    current["prompt_tokens"] += max(0, prompt_count)
    current["completion_tokens"] += max(0, completion_count)
    current["total_tokens"] += max(0, total_count if total_count > 0 else (prompt_count + completion_count))
    current["total_requests"] += 1
    current["last_updated"] = datetime.now().isoformat()

    os.makedirs(os.path.dirname(GROQ_TRACKER_FILE), exist_ok=True)
    try:
        with open(GROQ_TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CẢNH BÁO GROQ TOKEN TRACKER]: Không thể lưu token: {e}")

    return current


def reset_groq_tokens() -> Dict[str, Any]:
    """Đặt lại bộ đếm token Groq về 0."""
    reset_data = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_requests": 0,
        "last_updated": datetime.now().isoformat()
    }
    os.makedirs(os.path.dirname(GROQ_TRACKER_FILE), exist_ok=True)
    try:
        with open(GROQ_TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump(reset_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[CẢNH BÁO GROQ TOKEN TRACKER]: Không thể reset token: {e}")
    return reset_data

