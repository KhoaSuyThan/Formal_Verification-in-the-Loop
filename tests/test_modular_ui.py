"""Kiểm thử tính toàn vẹn của cấu trúc mô-đun hóa giao diện người dùng (web_demo/tabs/).

Kiểm tra:
1. Tất cả 4 hàm render tab được xuất khẩu đầy đủ từ web_demo.tabs.
2. Chữ ký hàm và khả năng nạp module mà không phát sinh ImportError.
"""

import inspect
from web_demo.tabs import (
    render_pipeline_tab,
    render_diff_tab,
    render_metrics_tab,
    render_cross_model_tab,
)


def test_tabs_exported_correctly():
    """Kiểm tra các hàm render tab được export chính xác."""
    assert callable(render_pipeline_tab)
    assert callable(render_diff_tab)
    assert callable(render_metrics_tab)
    assert callable(render_cross_model_tab)


def test_render_pipeline_tab_signature():
    """Kiểm tra chữ ký hàm render_pipeline_tab đầy đủ các tham số cần thiết."""
    sig = inspect.signature(render_pipeline_tab)
    params = list(sig.parameters.keys())
    expected = [
        "exec_mode",
        "selected_task_label",
        "selected_task_file",
        "selected_batch",
        "model_name",
        "max_k",
        "timeout_sec",
        "temperature",
        "flat_registry",
    ]
    for exp in expected:
        assert exp in params, f"Thiếu tham số {exp} trong render_pipeline_tab"


def test_render_cross_model_tab_signature():
    """Kiểm tra chữ ký hàm render_cross_model_tab."""
    sig = inspect.signature(render_cross_model_tab)
    params = list(sig.parameters.keys())
    expected = [
        "exec_mode",
        "selected_task_label",
        "selected_batch",
        "flat_registry",
        "max_k",
    ]
    for exp in expected:
        assert exp in params, f"Thiếu tham số {exp} trong render_cross_model_tab"


def test_app_script_syntax_and_structure():
    """Kiểm tra app.py có cấu trúc gọi các tab mô-đun."""
    from pathlib import Path
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    assert app_path.exists()
    content = app_path.read_text(encoding="utf-8")
    assert "render_pipeline_tab(" in content
    assert "render_diff_tab()" in content
    assert "render_metrics_tab(" in content
    assert "render_cross_model_tab(" in content
    # Đảm bảo app.py đã được thu gọn đáng kể (từ gần 2000 dòng xuống dưới 750 dòng)
    lines = content.splitlines()
    assert len(lines) < 750, f"app.py vẫn còn quá dài ({len(lines)} dòng)"
