"""Giao diện Tab 2: So Sánh Mã & Phân Tích Bất Biến (Diff Viewer).

Trực quan hóa sự khác biệt dòng mã nguồn giữa các lượt tự sửa lỗi Pass@K
và các bất biến quy nạp (Loop Invariants) được Z3 SMT Solver chứng thực.
"""

from typing import Optional
# pyrefly: ignore [missing-import]
import streamlit as st

from core.pipeline_controller import PipelineResult
from web_demo.helpers import (
    dict_to_pipeline_result,
    generate_code_diff_html,
    load_last_single_run,
)


def render_diff_tab() -> None:
    """Hiển thị toàn bộ nội dung của Tab 2: So sánh mã và phân tích bất biến."""
    st.markdown("### 🔍 Phân Tích Sự Khác Biệt & Bất Biến Toán Học")

    # Tự động nạp từ lịch sử kiên cố nếu session_state chưa có
    if "last_result" not in st.session_state or not getattr(st.session_state["last_result"], "history", []):
        saved_diff_data = load_last_single_run()
        if saved_diff_data:
            res_diff, meta_diff = dict_to_pipeline_result(saved_diff_data)
            st.session_state["last_result"] = res_diff
            st.session_state["spec_content"] = meta_diff.get("spec_content", "")
            st.caption(f"💾 Đang phân tích kết quả lưu kiên cố của bài: **{meta_diff.get('task_name')}** ({meta_diff.get('timestamp')})")

    if "last_result" in st.session_state and st.session_state["last_result"].history:
        res: PipelineResult = st.session_state["last_result"]

        if len(res.history) >= 2 or res.is_success:
            initial_code = res.history[0].code
            final_code = res.final_code

            st.markdown(
                "So sánh dòng mã nguồn giữa **Lượt 1 (Mã sinh ban đầu)** và **Lượt cuối (Mã hoàn chỉnh được Z3 xác thực)**:"
            )

            diff_html = generate_code_diff_html(initial_code, final_code)
            st.markdown(diff_html, unsafe_allow_html=True)

            st.markdown("#### 💡 Các bất biến quy nạp toán học đóng vai trò quyết định:")
            invariants = [line.strip() for line in final_code.splitlines() if line.strip().startswith("invariant ")]
            if invariants:
                for inv in invariants:
                    st.info(f"🔹 `{inv}`")
            else:
                st.caption("Bài toán giải tích trực tiếp không yêu cầu bổ sung loop invariant.")
        else:
            st.info("Bài toán đã đạt chứng minh ngay tại Lượt 1 hoặc chưa có vòng lặp tự sửa để so sánh diff.")
    else:
        st.info("Vui lòng thực hiện một lượt chạy kiểm định tại Tab 1 để xem phân tích so sánh mã nguồn.")
