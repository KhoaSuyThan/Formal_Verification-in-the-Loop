"""Gói module các Tabs giao diện người dùng cho ứng dụng Streamlit Studio.

Bao gồm:
- render_pipeline_tab: Tab 1 - Kiểm định trực tiếp (Single, Batch, Playground).
- render_diff_tab: Tab 2 - So sánh mã và phân tích bất biến.
- render_metrics_tab: Tab 3 - Báo cáo chỉ số khoa học độc lập.
- render_cross_model_tab: Tab 4 - Đánh giá đối đầu đa mô hình, CoT & Ảo giác.
"""

from web_demo.tabs.tab_pipeline_view import render_pipeline_tab
from web_demo.tabs.tab_diff_view import render_diff_tab
from web_demo.tabs.tab_metrics_view import render_metrics_tab
from web_demo.tabs.tab_cross_model_view import render_cross_model_tab

__all__ = [
    "render_pipeline_tab",
    "render_diff_tab",
    "render_metrics_tab",
    "render_cross_model_tab",
]
