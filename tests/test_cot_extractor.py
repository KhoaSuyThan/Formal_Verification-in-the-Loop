"""Kiểm thử tự động cho module bóc tách và định lượng CoT (tests/test_cot_extractor.py)."""

import pytest
from core.cot_extractor import extract_cot_trace, count_tokens_approx, analyze_cot_density


def test_deepseek_full_cot():
    """Kiểm thử bóc tách chuẩn xác khi có đầy đủ cặp thẻ <think>...</think>."""
    raw = (
        "<think>\n"
        "Need to find min element.\n"
        "Let's maintain invariant 0 <= i <= |s| and ensures min <= s[k].\n"
        "</think>\n\n"
        "```dafny\n"
        "method FindMin(s: seq<int>) returns (m: int)\n"
        "{\n"
        "    m := s[0];\n"
        "}\n"
        "```"
    )
    code, cot, tokens = extract_cot_trace(raw)
    assert "method FindMin" in code
    assert "<think>" not in code
    assert "</think>" not in code
    assert "Need to find min element" in cot
    assert "invariant" in cot
    assert tokens > 10


def test_deepseek_truncated_cot_with_code():
    """Kiểm thử khi thẻ <think> bị thiếu thẻ đóng nhưng vẫn có khối code."""
    raw = (
        "<think>\n"
        "We need invariant for loop.\n"
        "```dafny\n"
        "method Abs(x: int) returns (y: int)\n"
        "{\n"
        "    if x < 0 { y := -x; } else { y := x; }\n"
        "}\n"
        "```"
    )
    code, cot, tokens = extract_cot_trace(raw)
    assert "method Abs" in code
    assert "We need invariant for loop" in cot
    assert tokens > 0


def test_deepseek_incomplete_truncated_no_code():
    """Kiểm thử khi mô hình chạm trần token khi đang suy nghĩ dở dang, chưa kịp sinh code."""
    raw = "<think>\nLet's analyze the problem step by step. We have array s of integers..."
    code, cot, tokens = extract_cot_trace(raw)
    assert code == ""
    assert "Let's analyze" in cot
    assert tokens > 5


def test_non_reasoning_model():
    """Kiểm thử với mô hình thông thường (Qwen, LLaMA) không có thẻ suy nghĩ."""
    raw = (
        "```dafny\n"
        "method Sum(n: int) returns (s: int)\n"
        "{\n"
        "    s := n * (n + 1) / 2;\n"
        "}\n"
        "```"
    )
    code, cot, tokens = extract_cot_trace(raw)
    assert "method Sum" in code
    assert cot == ""
    assert tokens == 0


def test_cot_with_pseudo_code_inside():
    """Kiểm thử đảm bảo khối code giả lập bên trong <think> không bị nhầm lẫn với code chính."""
    raw = (
        "<think>\n"
        "Could we do:\n"
        "```\n"
        "var x := 5;\n"
        "```\n"
        "No that's wrong.\n"
        "</think>\n"
        "```dafny\n"
        "method Correct() returns (r: int) { r := 10; }\n"
        "```"
    )
    code, cot, tokens = extract_cot_trace(raw)
    assert "method Correct" in code
    assert "var x := 5" not in code
    assert "var x := 5" in cot


def test_analyze_cot_density_and_overthinking():
    """Kiểm thử phân tích mật độ từ khóa và phát hiện ngưỡng Overthinking."""
    # CoT ngắn tập trung vào invariant
    cot_short = "We must maintain invariant 0 <= i <= n and loop invariant a[i] == 0."
    metrics = analyze_cot_density(cot_short)
    assert metrics["has_cot"] is True
    assert metrics["invariant_mentions"] == 2
    assert metrics["primary_focus"] == "Bất biến Invariant"
    assert metrics["is_overthinking"] is False

    # CoT siêu dài (Overthinking)
    cot_long = "invariant " * 20 + "word " * 850
    metrics_over = analyze_cot_density(cot_long)
    assert metrics_over["is_overthinking"] is True
    assert metrics_over["tokens"] > 800

    # Không có CoT
    metrics_empty = analyze_cot_density("")
    assert metrics_empty["has_cot"] is False
    assert metrics_empty["tokens"] == 0
