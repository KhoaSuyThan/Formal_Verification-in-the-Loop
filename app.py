"""Formal Verification-in-the-Loop — Ứng Dụng Web Demo Nghiên Cứu Khoa Học.

Giao diện trực quan hóa tương tác quy trình sinh mã nguồn và tự sửa lỗi khép kín
dựa trên kiểm định toán học tất định Dafny 4.x và Z3 SMT Solver.
"""

import os
import sys
import time
from pathlib import Path
import sys

# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
import streamlit.components.v1 as components

# Đảm bảo đường dẫn gốc của dự án nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.token_tracker import get_gemini_token_usage
from web_demo.helpers import (
    get_benchmark_tasks,
    get_flat_task_registry,
)
from web_demo.tabs import (
    render_cross_model_tab,
    render_diff_tab,
    render_metrics_tab,
    render_pipeline_tab,
)


# ==============================================================================
# CẤU HÌNH TRANG WEB STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Formal Verification-in-the-Loop | NCKH Studio",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tùy biến giao diện CSS cao cấp, học thuật chuẩn quốc tế (Deep Space High-Tech Theme)
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    
    <style>
    /* Toàn cục Font & Theme */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Tiêu đề Hero Gradient */
    .hero-container {
        padding: 1.8rem 2rem;
        background: radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(168, 85, 247, 0.15) 0%, transparent 40%),
                    linear-gradient(180deg, #111827 0%, #0b0f19 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        margin-bottom: 1.5rem;
    }
    .hero-badge-top {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(129, 140, 248, 0.3);
        border-radius: 9999px;
        font-size: 0.78rem;
        color: #a5b4fc;
        font-weight: 600;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        font-size: 0.98rem;
        color: #94a3b8;
        line-height: 1.5;
        max-width: 820px;
    }

    /* Thẻ thông số Glassmorphism */
    .glass-card {
        padding: 1.1rem 1.3rem;
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.4);
    }
    .glass-card-icon {
        font-size: 1.6rem;
        padding: 8px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .glass-card-label {
        font-size: 0.78rem;
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
    }
    .glass-card-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Nút bấm Run Button Gradient */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 50%, #8b5cf6 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.02em !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
        transition: all 0.3s ease !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 50%, #7c3aed 100%) !important;
        box-shadow: 0 6px 28px rgba(99, 102, 241, 0.6) !important;
        transform: translateY(-2px) !important;
    }

    /* Thẻ trạng thái kết quả */
    .status-card-pass {
        padding: 1.4rem;
        background: radial-gradient(circle at 10% 20%, rgba(34, 197, 94, 0.15) 0%, transparent 70%),
                    linear-gradient(180deg, rgba(6, 78, 59, 0.4) 0%, rgba(6, 78, 59, 0.2) 100%);
        border: 1px solid rgba(74, 222, 128, 0.4);
        border-radius: 12px;
        color: #86efac;
        font-weight: 700;
        font-size: 1.15rem;
        box-shadow: 0 8px 24px rgba(34, 197, 94, 0.2);
        margin: 1.2rem 0;
    }
    .status-card-fail {
        padding: 1.4rem;
        background: radial-gradient(circle at 10% 20%, rgba(239, 68, 68, 0.15) 0%, transparent 70%),
                    linear-gradient(180deg, rgba(127, 29, 29, 0.4) 0%, rgba(127, 29, 29, 0.2) 100%);
        border: 1px solid rgba(248, 113, 113, 0.4);
        border-radius: 12px;
        color: #fca5a5;
        font-weight: 700;
        font-size: 1.15rem;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.2);
        margin: 1.2rem 0;
    }

    /* Tinh chỉnh Tab Headers */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        color: #94a3b8;
        background: transparent;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        background: rgba(99, 102, 241, 0.15) !important;
        border: 1px solid rgba(99, 102, 241, 0.3) !important;
    }

    /* Tinh chỉnh Checkbox danh sách bài toán */
    div[data-testid="stCheckbox"] {
        padding: 2px 0 !important;
        margin-bottom: 3px !important;
    }
    div[data-testid="stCheckbox"] label span {
        font-size: 0.88rem !important;
        color: #cbd5e1 !important;
        line-height: 1.3 !important;
    }
    div[data-testid="stCheckbox"]:hover label span {
        color: #38bdf8 !important;
    }

    /* Tinh chỉnh Radio nằm ngang ở sidebar: 3 nút chia đều 3 cột bằng nhau, căn đều 2 góc */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 6px !important;
        width: 100% !important;
        align-items: stretch !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        width: 100% !important;
        min-width: 0 !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        padding: 6px 4px !important;
        border-radius: 8px !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        transition: all 0.2s ease !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: rgba(99, 102, 241, 0.15) !important;
        border-color: rgba(99, 102, 241, 0.35) !important;
    }
    /* Chỉnh kích cỡ chữ nhỏ gọn và bắt buộc white-space: nowrap để hiển thị trọn vẹn 1 hàng */
    div[data-testid="stRadio"] > div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] > div[role="radiogroup"] label p,
    div[data-testid="stRadio"] > div[role="radiogroup"] label span {
        font-size: 0.72rem !important;
        white-space: nowrap !important;
        letter-spacing: -0.015em !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center !important;
    }
    /* Thu nhỏ nút tròn radio cân đối, giữ khoảng cách bên trong viền */
    div[data-testid="stRadio"] > div[role="radiogroup"] label > div:first-child {
        transform: scale(0.75) !important;
        margin: 0 !important;
        flex-shrink: 0 !important;
    }

    /* Tinh chỉnh các ô Dropdown (Selectbox) trong Sidebar: Thu nhỏ chữ và làm gọn khoảng cách */
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] {
        margin-bottom: 2px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] label {
        min-height: unset !important;
        margin-bottom: 2px !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stSelectbox"] label p {
        font-size: 0.76rem !important;
        font-weight: 600 !important;
        color: #cbd5e1 !important;
        margin: 0 !important;
        line-height: 1.25 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] {
        font-size: 0.78rem !important;
        min-height: 34px !important;
        height: 34px !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        min-height: 34px !important;
        height: 34px !important;
        padding: 2px 8px !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] div {
        font-size: 0.78rem !important;
        line-height: 1.25 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
        font-size: 0.78rem !important;
    }
    /* Menu xổ xuống (dropdown list) hiển thị chữ nhỏ gọn tương ứng */
    div[data-baseweb="popover"] ul li,
    div[data-baseweb="menu"] ul li {
        font-size: 0.78rem !important;
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }

    /* Tinh chỉnh thanh kéo Slider trong Sidebar vừa vặn, thoáng đãng */
    [data-testid="stSidebar"] div[data-testid="stSlider"] {
        padding-top: 1px !important;
        padding-bottom: 2px !important;
        margin-bottom: 1px !important;
    }
    [data-testid="stSidebar"] div[data-testid="stSlider"] label p {
        font-size: 0.78rem !important;
        margin-bottom: 1px !important;
        color: #e2e8f0 !important;
    }

    /* Tinh chỉnh 3 mục ở Sidebar: Thu gọn khoảng cách viền và padding */
    .sidebar-section-title {
        font-size: 0.86rem !important;
        font-weight: 700 !important;
        color: #f1f5f9 !important;
        margin-bottom: 4px !important;
        letter-spacing: 0.01em !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0 !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] > div {
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        background: rgba(255, 255, 255, 0.02) !important;
        padding: 8px 10px !important;
        gap: 5px !important;
    }
    /* Tinh chỉnh cỡ chữ nhỏ gọn cho danh sách bài toán trong Modal Dialog */
    div[data-testid="stDialog"] div[data-testid="stCheckbox"] label span {
        font-size: 0.82rem !important;
        color: #cbd5e1 !important;
        line-height: 1.35 !important;
    }
    div[data-testid="stDialog"] div[data-testid="stCheckbox"] {
        padding: 1px 0 !important;
        margin-bottom: 2px !important;
    }
    div[data-testid="stDialog"] div[data-testid="stCheckbox"]:hover label span {
        color: #38bdf8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Chặn hoàn toàn gõ bàn phím vào các ô selectbox: Chỉ cho phép click chọn từ menu
components.html(
    """
    <script>
    function lockSelectboxes() {
        const rootDoc = window.parent.document;
        if (!rootDoc) return;
        const inputs = rootDoc.querySelectorAll('div[data-baseweb="select"] input');
        inputs.forEach(input => {
            input.setAttribute('readonly', 'readonly');
            input.setAttribute('inputmode', 'none');
            input.style.caretColor = 'transparent';
            input.style.cursor = 'pointer';
            input.onkeydown = function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            };
            input.oninput = function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            };
        });
    }
    lockSelectboxes();
    setInterval(lockSelectboxes, 250);
    </script>
    """,
    height=0,
    width=0,
)


# ==============================================================================
# BẢNG ĐIỀU KHIỂN BÊN TRÁI (SIDEBAR)
# ==============================================================================
flat_registry = get_flat_task_registry()


@st.dialog("📋 Lựa Chọn Danh Sách Bài Toán Benchmark", width="large")
def open_task_selection_dialog():
    """Hộp thoại Modal hiển thị danh sách bài toán cho người dùng tick chọn."""
    st.caption("Tick chọn các bài toán bạn muốn đưa vào vòng lặp kiểm định tự động:")

    # Hàng điều khiển: Tìm kiếm -> Chọn tất cả -> Bỏ chọn theo tỉ lệ 6 / 2 / 2
    col_search, col_all, col_none = st.columns([6, 2, 2])
    with col_search:
        search_query = st.text_input(
            "Tìm kiếm:",
            value="",
            placeholder="🔍 Tìm theo tên file (.dfy) hoặc tên bài...",
            key="dialog_task_search_query",
            label_visibility="collapsed",
        )

    # Lọc danh sách bài toán theo từ khóa tìm kiếm
    query_clean = search_query.strip().lower()
    if query_clean:
        filtered_tasks = {
            k: v for k, v in flat_registry.items()
            if query_clean in Path(v["rel_path"]).name.lower()
            or query_clean in v["short_name"].lower()
            or query_clean in v["label"].lower()
        }
    else:
        filtered_tasks = flat_registry

    with col_all:
        if st.button("✓ Chọn tất cả", width="stretch", help="Tick chọn tất cả các bài đang hiển thị"):
            for k in filtered_tasks.keys():
                st.session_state[f"chk_task_{flat_registry[k]['short_name']}"] = True
            st.rerun()

    with col_none:
        if st.button("✕ Bỏ chọn", width="stretch", help="Bỏ tick các bài đang hiển thị"):
            for k in filtered_tasks.keys():
                st.session_state[f"chk_task_{flat_registry[k]['short_name']}"] = False
            st.rerun()

    st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

    # Hiển thị 3 cột bài toán theo định dạng: Tên tiếng Việt (tên file)
    clover_filtered = {k: v for k, v in filtered_tasks.items() if v["group"] == "Clover"}
    humaneval_filtered = {k: v for k, v in filtered_tasks.items() if v["group"] == "HumanEval"}
    advanced_filtered = {k: v for k, v in filtered_tasks.items() if v["group"] == "Advanced"}

    col_c, col_h, col_a = st.columns(3)
    with col_c:
        st.markdown(f"**🍀 Clover ({len(clover_filtered)} bài):**")
        for _item_key, meta in clover_filtered.items():
            file_name = Path(meta["rel_path"]).name
            vn_desc = meta["label"].split(" - ", 1)[1] if " - " in meta["label"] else meta["short_name"]
            badge_txt = " 🔥" if meta["is_target"] else ""
            st.checkbox(
                f"{vn_desc} ({file_name}){badge_txt}",
                key=f"chk_task_{meta['short_name']}",
                help=f"Mã: {meta['short_name']} | Đường dẫn: {meta['rel_path']}",
            )

    with col_h:
        st.markdown(f"**🧪 HumanEval ({len(humaneval_filtered)} bài):**")
        for _item_key, meta in humaneval_filtered.items():
            file_name = Path(meta["rel_path"]).name
            vn_desc = meta["label"].split(" - ", 1)[1] if " - " in meta["label"] else meta["short_name"]
            badge_txt = " 🔥" if meta["is_target"] else ""
            st.checkbox(
                f"{vn_desc} ({file_name}){badge_txt}",
                key=f"chk_task_{meta['short_name']}",
                help=f"Mã: {meta['short_name']} | Đường dẫn: {meta['rel_path']}",
            )

    with col_a:
        st.markdown(f"**⚡ Mở Rộng ({len(advanced_filtered)} bài):**")
        for _item_key, meta in advanced_filtered.items():
            file_name = Path(meta["rel_path"]).name
            vn_desc = meta["label"].split(" - ", 1)[1] if " - " in meta["label"] else meta["short_name"]
            badge_txt = " 🚀"
            st.checkbox(
                f"{vn_desc} ({file_name}){badge_txt}",
                key=f"chk_task_{meta['short_name']}",
                help=f"Mã: {meta['short_name']} | Đường dẫn: {meta['rel_path']}",
            )

    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
    if st.button("✅ Hoàn Tất Lựa Chọn", type="primary", width="stretch"):
        st.rerun()


with st.sidebar:
    st.image(
        "https://img.shields.io/badge/Formal%20Verification-Z3%20SMT%20Solver-2ea44f?style=for-the-badge",
        width="stretch",
    )

    # ==========================================================================
    # MỤC 1: CHẾ ĐỘ THỰC THI (VIỀN MỎNG)
    # ==========================================================================
    with st.container(border=True):
        st.markdown("<div class='sidebar-section-title'>⚙️ Chế Độ Thực Thi</div>", unsafe_allow_html=True)
        exec_mode = st.radio(
            "Chọn chế độ:",
            ["Đơn", "Hàng loạt", "Tự do"],
            index=0,
            horizontal=True,
            label_visibility="collapsed",
        )

    # ==========================================================================
    # MỤC 2: CHỌN BÀI TOÁN BENCHMARK (VIỀN MỎNG)
    # ==========================================================================
    with st.container(border=True):
        if exec_mode == "Đơn":
            st.markdown("<div class='sidebar-section-title'>📁 Chọn Bài Toán Mẫu</div>", unsafe_allow_html=True)
            task_groups = get_benchmark_tasks()
            selected_group = st.selectbox("Tập Benchmark", list(task_groups.keys()))
            task_options = task_groups[selected_group]
            selected_task_label = st.selectbox("Bài toán mẫu", list(task_options.keys()))
            selected_task_file = task_options[selected_task_label]
            selected_batch = []
        elif exec_mode == "Hàng loạt":
            st.markdown("<div class='sidebar-section-title'>📁 Danh Mục Benchmark</div>", unsafe_allow_html=True)
            # Tính toán ĐỘNG số lượng bài toán theo registry thực tế (không hardcode)
            clover_tasks = {k: v for k, v in flat_registry.items() if v["group"] == "Clover"}
            humaneval_tasks = {k: v for k, v in flat_registry.items() if v["group"] == "HumanEval"}
            advanced_tasks = {k: v for k, v in flat_registry.items() if v["group"] == "Advanced"}
            target_tasks = {k: v for k, v in flat_registry.items() if v["is_target"]}

            clover_total = len(clover_tasks)
            humaneval_total = len(humaneval_tasks)
            advanced_total = len(advanced_tasks)
            target_total = len(target_tasks)
            all_total = len(flat_registry)

            # Mặc định ban đầu: KHÔNG chọn bài nào cả (False)
            for _item_key, meta in flat_registry.items():
                cb_key = f"chk_task_{meta['short_name']}"
                if cb_key not in st.session_state:
                    st.session_state[cb_key] = False

            preset_options = [
                "--- Bấm để sổ xuống chọn bộ ---",
                f"🔥 Bộ chuẩn 100% ({target_total} bài)",
                f"🍀 Bộ Clover ({clover_total} bài)",
                f"🧪 Bộ HumanEval ({humaneval_total} bài)",
                f"⚡ Bộ Mở Rộng Advanced ({advanced_total} bài)",
                f"🌐 Toàn bộ 30 bài toán ({all_total} bài)",
                "🧹 Bỏ chọn toàn bộ (0 bài)",
            ]

            preset_choice = st.selectbox(
                "Sổ xuống chọn bộ bài toán:",
                options=preset_options,
                index=0,
                key="preset_selector_dropdown",
                help="Số lượng bài toán được tính toán tự động dựa trên thư mục benchmark.",
            )

            if preset_choice != st.session_state.get("current_preset_applied", "--- Bấm để sổ xuống chọn bộ ---"):
                st.session_state["current_preset_applied"] = preset_choice
                if "Bộ chuẩn 100%" in preset_choice:
                    for _item_key, meta in flat_registry.items():
                        st.session_state[f"chk_task_{meta['short_name']}"] = meta["is_target"]
                elif "Bộ Clover" in preset_choice:
                    for _item_key, meta in flat_registry.items():
                        st.session_state[f"chk_task_{meta['short_name']}"] = (meta["group"] == "Clover")
                elif "Bộ HumanEval" in preset_choice:
                    for _item_key, meta in flat_registry.items():
                        st.session_state[f"chk_task_{meta['short_name']}"] = (meta["group"] == "HumanEval")
                elif "Bộ Mở Rộng" in preset_choice:
                    for _item_key, meta in flat_registry.items():
                        st.session_state[f"chk_task_{meta['short_name']}"] = (meta["group"] == "Advanced")
                elif "Toàn bộ" in preset_choice:
                    for _item_key, meta in flat_registry.items():
                        st.session_state[f"chk_task_{meta['short_name']}"] = True
                elif "Bỏ chọn toàn bộ" in preset_choice:
                    for _item_key, meta in flat_registry.items():
                        st.session_state[f"chk_task_{meta['short_name']}"] = False
                st.rerun()

            # Mở hộp thoại Modal Popup khi bấm nút thay vì dùng expander xổ xuống
            if st.button("📋 Chọn Cụ Thể", width="stretch", help="Bấm để mở"):
                open_task_selection_dialog()

            # Thu thập danh sách các bài toán được người dùng tick chọn
            selected_batch = [
                item_key for item_key, meta in flat_registry.items()
                if st.session_state.get(f"chk_task_{meta['short_name']}", False)
            ]

            st.markdown(
                f"<div style='background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.25); "
                f"border-radius: 8px; padding: 6px 10px; margin-top: 6px; font-size: 0.84rem;'>"
                f"📊 <strong>Đã tick chọn:</strong> <span style='color: #38bdf8; font-weight: bold;'>{len(selected_batch)}/{all_total} bài</span>",
                unsafe_allow_html=True,
            )
        else:
            # Chế độ Sân Chơi Tự Do (Playground)
            st.markdown("<div class='sidebar-section-title'>🛠️ Sân Chơi Tự Do</div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size: 0.84rem; color: #94a3b8; line-height: 1.45;'>"
                "Tự do nhập hoặc dán bất kỳ bài toán Dafny 4.x nào. "
                "Hệ thống tự động phân tích cú pháp, khóa SHA-256 đặc tả và kích hoạt Z3 SMT Solver chứng minh toán học khép kín."
                "</div>",
                unsafe_allow_html=True,
            )
            selected_batch = []

    # ==========================================================================
    # MỤC 3: CẤU HÌNH MÔ HÌNH (VIỀN MỎNG)
    # ==========================================================================
    with st.container(border=True):
        st.markdown("<div class='sidebar-section-title'>🤖 Cấu Hình Mô Hình</div>", unsafe_allow_html=True)
        model_name = st.selectbox(
            "Mô hình LLM",
            [
                "ollama/qwen2.5-coder:7b",
                "gemini-2.5-flash",
                "gemini-3.5-flash",
                "gemini-3.6-flash",
                "ollama/llama3.1:8b",
                "ollama/deepseek-r1:7b",
            ],
            index=0,
            help="Hỗ trợ mô hình Local (Ollama) và Cloud (Google Gemini Flash Free Tier đã lưu key trong .env).",
        )
        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            max_k = st.slider("Pass@K", min_value=1, max_value=5, value=3, help="Số lượt tự sửa tối đa")
        with col_cfg2:
            timeout_sec = st.slider("Timeout (s)", min_value=5, max_value=30, value=15, help="Giới hạn thời gian Z3 Solver")

        temperature = st.slider(
            "Độ ngẫu nhiên (Temp)",
            min_value=0.0,
            max_value=0.5,
            value=0.0,
            step=0.05,
            help="0.0: Tất định, kết quả tái lập tuyệt đối (chuẩn NCKH). >0: Cho phép ngẫu nhiên hóa token.",
        )

    st.caption("Đề tài NCKH: Formal Verification-in-the-Loop (2026)")


# ==============================================================================
# NỘI DUNG CHÍNH (MAIN AREA)
# ==============================================================================
gemini_tokens = get_gemini_token_usage()
gem_total = gemini_tokens.get("total_tokens", 0)
gem_prompt = gemini_tokens.get("prompt_tokens", 0)
gem_completion = gemini_tokens.get("completion_tokens", 0)
gem_reqs = gemini_tokens.get("total_requests", 0)

st.markdown(
    f"""
    <div class="hero-container" style="display: flex; justify-content: space-between; align-items: center; gap: 24px;">
        <div style="flex: 1; min-width: 0;">
            <div class="hero-badge-top">🛡️ Formal Verification-in-the-Loop • Z3 SMT Powered</div>
            <div class="hero-title">Formal Verification Studio</div>
            <div class="hero-subtitle">
                Khung sinh mã nguồn và tự sửa lỗi khép kín loại bỏ hoàn toàn ảo giác (Zero-Hallucination)
                dựa trên kiểm định logic toán học tất định <strong>Dafny 4.x</strong> và <strong>Z3 SMT Solver</strong>.
            </div>
        </div>
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 14px 20px; min-width: 220px; box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4); backdrop-filter: blur(10px);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="font-size: 0.8rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em;">💎 Gemini Token</span>
                <span style="font-size: 0.72rem; padding: 2px 7px; border-radius: 6px; background: rgba(34, 197, 94, 0.15); color: #86efac; font-weight: 700; border: 1px solid rgba(34, 197, 94, 0.3);">FREE</span>
            </div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; line-height: 1.15; font-family: 'JetBrains Mono', monospace;">
                {gem_total:,}
            </div>
            <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 5px;">
                In: <span style="color: #cbd5e1; font-weight: 600;">{gem_prompt:,}</span> | Out: <span style="color: #cbd5e1; font-weight: 600;">{gem_completion:,}</span>
            </div>
            <div style="font-size: 0.72rem; color: #64748b; margin-top: 3px;">
                Tổng yêu cầu: <strong style="color: #94a3b8;">{gem_reqs}</strong> calls
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Phân bố 4 Tab chức năng gọn gàng, súc tích
tab_pipeline, tab_diff, tab_metrics, tab_cross_model = st.tabs(
    [
        "⚡ Kiểm Định Trực Tiếp",
        "🔍 So Sánh Mã",
        "📊 Báo Cáo NCKH",
        "⚔️ So Sánh Chéo",
    ]
)

# ==============================================================================
# ĐIỀU PHỐI GIAO DIỆN 4 TABS CHUYÊN BIỆT
# ==============================================================================
with tab_pipeline:
    render_pipeline_tab(
        exec_mode=exec_mode,
        selected_task_label=selected_task_label if exec_mode == "Đơn" else "",
        selected_task_file=selected_task_file if exec_mode == "Đơn" else "",
        selected_batch=selected_batch,
        model_name=model_name,
        max_k=max_k,
        timeout_sec=timeout_sec,
        temperature=temperature,
        flat_registry=flat_registry,
    )

with tab_diff:
    render_diff_tab()

with tab_metrics:
    render_metrics_tab(
        model_name=model_name,
        max_k=max_k,
        timeout_sec=timeout_sec,
    )

with tab_cross_model:
    render_cross_model_tab(
        exec_mode=exec_mode,
        selected_task_label=selected_task_label if exec_mode == "Đơn" else "",
        selected_batch=selected_batch,
        flat_registry=flat_registry,
        max_k=max_k,
    )

# Formal Verification-in-the-Loop Web Demo v1.4.2 - Modular UI Architecture Ready
