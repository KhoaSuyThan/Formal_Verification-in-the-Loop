"""Giao diện Tab 4: Ma Trận Đánh Giá Đối Đầu Đa Mô Hình (Cross-Model Evaluation).

So sánh năng lực sinh mã và kiểm định hình thức giữa Local AI (Qwen, LLaMA, DeepSeek-R1)
và Cloud AI (Gemini Flash), trực quan hóa phân bố ảo giác Nature 2024 (H0-H4),
phân tích hiện tượng Overthinking CoT (arXiv:2505.12886) và xuất bảng LaTeX học thuật.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import streamlit as st

from core.cross_model_evaluator import CrossModelEvaluator
from core.hallucination_classifier import classify_hallucination


def render_cross_model_tab(
    exec_mode: str,
    selected_task_label: str,
    selected_batch: List[str],
    flat_registry: Dict[str, Any],
    max_k: int,
) -> None:
    """Hiển thị toàn bộ nội dung của Tab 4: So sánh đối đầu đa mô hình."""
    st.markdown("### ⚔️ So Sánh Đối Đầu Mô Hình")
    st.caption("Đo lường năng lực sinh mã kèm kiểm chứng hình thức giữa Local AI (Ollama) và Cloud AI (Google Gemini).")

    # Lựa chọn mô hình tham gia thi đấu (Hỗ trợ các dòng Gemini Flash ổn định)
    eval_models = [
        ("ollama/qwen2.5-coder:7b", "Qwen 7B (Local)"),
        ("gemini-2.5-flash", "Gemini 2.5 Flash (Cloud - Quota cao 1500 req/ngày)"),
        ("gemini-3.5-flash", "Gemini 3.5 Flash (Cloud - Đã kiểm chứng)"),
        ("gemini-3.6-flash", "Gemini 3.6 Flash (Preview - Hạn ngạch 20 req/ngày)"),
        ("ollama/llama3.1:8b", "LLaMA 8B (Local)"),
        ("ollama/deepseek-r1:7b", "DeepSeek 7B (Local)"),
    ]
    selected_eval_models = st.multiselect(
        "Mô hình tham gia:",
        options=[m[0] for m in eval_models],
        default=["ollama/qwen2.5-coder:7b", "ollama/llama3.1:8b"],
        format_func=lambda x: next((m[1] for m in eval_models if m[0] == x), x),
        help="Tick chọn các mô hình muốn so tài.",
    )

    # Cấu hình hiệu năng: Thực thi đa luồng song song & SMT Verification Cache
    col_cfg_w, col_cfg_c = st.columns([1.5, 2.5])
    with col_cfg_w:
        eval_workers = st.slider(
            "Số luồng xử lý song song (Workers):",
            min_value=1,
            max_value=8,
            value=1,
            help="1: Tuần tự truyền thống. 2-8: Đa luồng song song (ThreadPoolExecutor), tăng tốc độ chạy trên CPU đa nhân."
        )
    with col_cfg_c:
        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
        eval_use_cache = st.checkbox(
            "Bật SMT Verification Cache (Tái sử dụng Z3)",
            value=True,
            help="Băm SHA-256 mã nguồn và lưu đệm kết quả kiểm định Z3. Giúp chạy lại benchmark cực nhanh (< vài giây)."
        )

    # Khuyến nghị tối ưu hóa tài nguyên phần cứng
    st.caption("💡 **Khuyến nghị:** Mô hình Local (Ollama) nên đặt **1 - 2 Workers** (để GPU dồn tài nguyên xử lý dứt điểm, tránh chia tải tráo đổi mô hình); Mô hình Cloud (Gemini) nên đặt **4 - 8 Workers** để khai thác tối đa tốc độ server Google.")

    # Đồng bộ trực tiếp danh sách bài toán đã chọn từ Sidebar bên trái (tránh trùng lặp cấu hình)
    if exec_mode == "Hàng loạt" and selected_batch:
        target_keys = selected_batch
        source_note = f"Đang áp dụng **{len(target_keys)} bài** đã tick chọn ở mục 'Danh Mục Benchmark' bên trái."
    elif exec_mode == "Đơn":
        target_keys = [k for k in flat_registry.keys() if selected_task_label.split(" - ")[0] in k][:1]
        source_note = f"Đang áp dụng **1 bài** ({selected_task_label.split(' - ')[0]}) đang chọn ở menu bên trái."
    else:
        target_keys = [
            k for k in flat_registry.keys()
            if any(name in k for name in ["abs_val", "sample_max", "002-truncate", "013-greatest_common_divisor", "binary_search"])
        ][:5]
        source_note = f"Mặc định chạy **5 bài tiêu biểu** (hoặc chuyển sang chế độ 'Hàng loạt' bên trái để tự chọn bài)."

    # Kiểm tra xem có bản checkpoint dở dang để hỗ trợ tính năng tiếp tục chạy (Resume)
    latest_file = os.path.join("artifacts", "results", "cross_model_benchmark_latest.json")
    has_resumable_checkpoint = False
    resumable_tasks_count = 0
    if os.path.exists(latest_file):
        try:
            with open(latest_file, "r", encoding="utf-8") as f_chk_info:
                chk_content = json.load(f_chk_info)
                for _m_id, r_list in chk_content.get("detailed_results", {}).items():
                    resumable_tasks_count += len(r_list)
                if resumable_tasks_count > 0:
                    has_resumable_checkpoint = True
        except Exception:
            pass

    if has_resumable_checkpoint:
        col_btn_run, col_btn_resume, col_btn_stop, col_btn_load = st.columns([2.5, 3.5, 2, 2])
        with col_btn_run:
            btn_start_benchmark = st.button("🚀 Chạy Mới Từ Đầu", type="secondary", width="stretch", help="Xóa bỏ checkpoint cũ và bắt đầu chạy lại từ bài đầu tiên")
        with col_btn_resume:
            btn_resume_benchmark = st.button(f"▶️ Tiếp Tục Chạy ({resumable_tasks_count} bài đã xong)", type="primary", width="stretch", help="Nạp lại kết quả cũ và tiếp tục chạy ngay từ bài chưa hoàn thành")
        with col_btn_stop:
            btn_stop_benchmark = st.button("⏹️ Dừng So Sánh", type="secondary", width="stretch", help="Dừng an toàn quá trình so sánh sau bài toán hiện tại")
        with col_btn_load:
            btn_load_cached = st.button("📂 Tải Kết Quả Cũ", width="stretch")
    else:
        btn_resume_benchmark = False
        col_btn_run, col_btn_stop, col_btn_load = st.columns([3, 2, 2])
        with col_btn_run:
            btn_start_benchmark = st.button("🚀 Bắt Đầu So Sánh", type="primary", width="stretch")
        with col_btn_stop:
            btn_stop_benchmark = st.button("⏹️ Dừng So Sánh", type="secondary", width="stretch", help="Dừng an toàn quá trình so sánh sau bài toán hiện tại")
        with col_btn_load:
            btn_load_cached = st.button("📂 Tải Kết Quả Cũ", width="stretch")

    cross_stop_flag = os.path.join("artifacts", ".stop_cross_flag")
    if btn_stop_benchmark:
        Path(cross_stop_flag).touch()
        st.toast("🛑 Đã gửi lệnh dừng! Quá trình so sánh sẽ dừng an toàn sau bài toán hiện tại.", icon="🛑")
        st.warning("🛑 Đã kích hoạt lệnh dừng. Hệ thống đang hoàn tất bài hiện tại và dừng an toàn...")

    if (btn_start_benchmark or btn_resume_benchmark) and os.path.exists(cross_stop_flag):
        try:
            os.remove(cross_stop_flag)
        except Exception:
            pass

    # Xử lý khi bấm nút Tải Kết Quả Cũ ở hàng điều khiển trên cùng
    if btn_load_cached:
        if os.path.exists(latest_file):
            try:
                with open(latest_file, "r", encoding="utf-8") as f_cached:
                    st.session_state["cross_model_data"] = json.load(f_cached)
                st.session_state["currently_loaded_file"] = "Mới nhất (Latest)"
                st.toast("✅ Đã nạp thành công bản kết quả benchmark gần nhất!", icon="📂")
                st.rerun()
            except Exception as err:
                st.error(f"❌ Không thể đọc file kết quả gần nhất: {err}")
        else:
            st.warning("⚠️ Chưa có bản lưu kết quả benchmark nào trong thư mục artifacts/results!")

    st.caption(f"📌 {source_note}")
    if has_resumable_checkpoint:
        st.info(f"💡 **Phát hiện tiến trình trước đó đã chạy {resumable_tasks_count} bài.** Bấm nút **'▶️ Tiếp Tục Chạy'** màu tím để chạy tiếp từ bài dở dang mà không mất kết quả cũ, hoặc bấm **'🚀 Chạy Mới Từ Đầu'** nếu muốn đo lại từ đầu.")

    # Xử lý khi bấm nút chạy mới hoặc tiếp tục chạy dở dang
    is_resuming = bool(btn_resume_benchmark)
    if btn_start_benchmark or btn_resume_benchmark:
        if not selected_eval_models:
            st.warning("⚠️ Vui lòng chọn ít nhất một mô hình để chạy benchmark!")
        elif not target_keys:
            st.warning("⚠️ Chưa có bài toán nào được chọn từ menu bên trái!")
        else:
            dafny_exe_path = os.getenv("DAFNY_PATH")
            evaluator = CrossModelEvaluator(dafny_path=dafny_exe_path)

            progress_bar = st.progress(0.0)
            status_text = st.empty()
            live_table_placeholder = st.empty()
            live_detail_placeholder = st.empty()

            def update_progress(model_id: str, cur_step: int, total_steps: int, msg: str, latest_data: Optional[dict] = None):
                frac = min(1.0, cur_step / max(1, total_steps))
                progress_bar.progress(frac)
                status_text.markdown(f"**[{cur_step}/{total_steps}]** {msg}")
                if latest_data and "summaries" in latest_data and latest_data["summaries"]:
                    st.session_state["cross_model_data"] = latest_data
                    try:
                        # 1. Cập nhật bảng tổng quan đối đầu
                        df_live = pd.DataFrame(latest_data["summaries"])[[
                            "display_name", "model_type", "total_tasks",
                            "passed_tasks", "pass_at_1_rate", "pass_at_k_rate",
                            "avg_duration_sec", "avg_repair_loops"
                        ]]
                        df_live.columns = [
                            "Mô Hình", "Loại", "Số Bài Đã Chạy", "Bài Đạt",
                            "Pass@1 (%)", "Pass@K (%)", "Thời Gian TB (s)", "Số Vòng Lặp TB"
                        ]
                        live_table_placeholder.dataframe(df_live, width="stretch", hide_index=True)

                        # 2. Cập nhật bảng chi tiết từng bài vừa giải xong (mới nhất lên đầu)
                        all_detailed = []
                        for m_key, t_list in latest_data.get("detailed_results", {}).items():
                            m_name = next((s["display_name"] for s in latest_data["summaries"] if s["model_name"] == m_key), m_key)
                            for t in t_list:
                                all_detailed.append({
                                    "Mô Hình": m_name,
                                    "Bài Toán": t["task_name"],
                                    "Tập": t.get("group", ""),
                                    "Kết Quả Z3": "✅ PASS" if t["success"] else "❌ FAIL",
                                    "Lượt Thử": f"Pass@{t['iterations']}" if t["success"] else ">3",
                                    "Thời Gian (s)": t["duration_sec"],
                                })
                        if all_detailed:
                            df_tasks = pd.DataFrame(all_detailed)
                            with live_detail_placeholder.container():
                                st.markdown("##### 📝 Nhật Ký Từng Bài Vừa Giải Xong (Mới Nhất Ở Trên):")
                                st.dataframe(df_tasks.iloc[::-1], width="stretch", hide_index=True)
                    except Exception:
                        pass

            spinner_msg = "Đang tiếp tục kiểm chứng hình thức đa mô hình từ bài dở dang..." if is_resuming else "Đang tiến hành kiểm chứng hình thức đa mô hình (kết quả tự động lưu sau mỗi bài)..."
            with st.spinner(spinner_msg):
                benchmark_data = evaluator.run_benchmark(
                    model_ids=selected_eval_models,
                    task_keys=target_keys,
                    max_attempts=max_k,
                    progress_callback=update_progress,
                    stop_check=lambda: os.path.exists(cross_stop_flag),
                    resume_from_checkpoint=is_resuming,
                    workers=eval_workers,
                    use_cache=eval_use_cache,
                )
                st.session_state["cross_model_data"] = benchmark_data
                st.session_state["currently_loaded_file"] = "Mới nhất (Latest)"
                if os.path.exists(cross_stop_flag):
                    try:
                        os.remove(cross_stop_flag)
                    except Exception:
                        pass
                    status_text.warning("🛑 Quá trình so sánh đã dừng lại theo yêu cầu! Toàn bộ kết quả đã chạy được lưu trữ đầy đủ.")
                else:
                    progress_bar.progress(1.0)
                    status_text.success("🎉 Đã hoàn thành toàn bộ chu trình đánh giá đối đầu!")
                st.rerun()

    # Tự động nạp kết quả đã lưu gần nhất nếu session_state chưa có
    latest_file = os.path.join("artifacts", "results", "cross_model_benchmark_latest.json")
    if "cross_model_data" not in st.session_state and os.path.exists(latest_file):
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                st.session_state["cross_model_data"] = json.load(f)
            st.session_state["currently_loaded_file"] = "Mới nhất (Latest)"
        except Exception:
            pass

    # Quét danh sách các file lịch sử benchmark đã lưu
    res_dir = os.path.join("artifacts", "results")
    bench_files = []
    if os.path.exists(res_dir):
        for f in os.listdir(res_dir):
            if f.startswith("cross_model_benchmark_") and f.endswith(".json") and f != "cross_model_benchmark_latest.json":
                bench_files.append(f)
    bench_files.sort(reverse=True)

    if bench_files:
        hist_options = ["Mới nhất (Latest)"] + bench_files

        col_hist1, col_hist2 = st.columns([7, 3])
        with col_hist1:
            selected_hist = st.selectbox(
                "📂 Xem lại các lần chạy trong lịch sử:",
                hist_options,
                key="hist_selector_dropdown",
                help="Chọn bất kỳ file nào để xem lại kết quả. Bảng và biểu đồ sẽ tự động cập nhật ngay lập tức!",
            )
        with col_hist2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_force_reload = st.button("🔄 Nạp Lại Bản Này", width="stretch")

        # Tự động nạp dữ liệu tức thì mỗi khi mục chọn thay đổi hoặc bấm nạp lại
        need_load = (st.session_state.get("currently_loaded_file") != selected_hist) or btn_force_reload
        if need_load:
            target_fname = "cross_model_benchmark_latest.json" if selected_hist == "Mới nhất (Latest)" else selected_hist
            target_path = os.path.join(res_dir, target_fname)
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f_in:
                        st.session_state["cross_model_data"] = json.load(f_in)
                    st.session_state["currently_loaded_file"] = selected_hist
                    st.toast(f"✅ Đã tải: {selected_hist}")
                except Exception as err:
                    st.error(f"Lỗi khi đọc file {selected_hist}: {err}")

        # Hiển thị nhãn rõ ràng để người dùng biết đang xem dữ liệu của file nào
        active_label = st.session_state.get("currently_loaded_file", selected_hist)
        st.info(f"📊 Đang hiển thị dữ liệu lịch sử từ tệp: **`{active_label}`**")

    # Hiển thị bảng kết quả và đồ thị khi đã có dữ liệu
    active_data = st.session_state.get("cross_model_data")
    if active_data and "summaries" in active_data and active_data["summaries"]:
        summaries = active_data["summaries"]
        st.markdown("---")
        st.markdown("#### 📊 Bảng Ma Trận Đối Đầu Khoa Học (Benchmark Matrix)")

        df_summary = pd.DataFrame(summaries)

        # Kiểm tra sự hiện diện của mô hình Reasoning (Trục 2 - arXiv:2505.12886)
        has_cot_in_summary = "avg_cot_tokens" in df_summary.columns and (df_summary["avg_cot_tokens"] > 0).any()

        summary_cols = [
            "display_name", "model_type", "total_tasks",
            "passed_tasks", "pass_at_1_rate", "pass_at_k_rate",
            "avg_duration_sec", "avg_repair_loops"
        ]
        summary_headers = [
            "Mô Hình", "Loại", "Số Bài",
            "Bài Đạt", "Pass@1 (%)", "Pass@K (%)",
            "Thời Gian TB (s)", "Số Vòng Lặp TB"
        ]
        if has_cot_in_summary:
            summary_cols.append("avg_cot_tokens")
            summary_headers.append("CoT Token TB (L_CoT)")

        df_display = df_summary[summary_cols].copy()
        df_display.columns = summary_headers
        st.dataframe(df_display, width="stretch", hide_index=True)

        # Tính toán trước danh sách chi tiết và thống kê ảo giác để vẽ 3 biểu đồ song hành
        all_detailed = []
        h_counts_by_model: Dict[str, Dict[str, int]] = {}
        all_cot_records = []

        if "detailed_results" in active_data and active_data["detailed_results"]:
            for m_key, t_list in active_data.get("detailed_results", {}).items():
                m_name = next((s["display_name"] for s in summaries if s["model_name"] == m_key), m_key)
                h_counts_by_model[m_name] = {"H0": 0, "H1": 0, "H2": 0, "H3": 0, "H4": 0}

                for t in t_list:
                    is_pass = t.get("success", False)
                    # Tương thích ngược an toàn với bản lưu cũ chưa có trường h_code
                    h_code = t.get("h_code")
                    h_badge = t.get("h_badge")
                    if not h_code or not h_badge:
                        h_rep = classify_hallucination(
                            is_success=is_pass,
                            error_message=t.get("failure_reason", "")
                        )
                        h_code = h_rep["code"]
                        h_badge = h_rep["badge"]

                    if h_code in h_counts_by_model[m_name]:
                        h_counts_by_model[m_name][h_code] += 1

                    # Ghi nhận chỉ số CoT Reasoning
                    c_tok = t.get("cot_tokens", 0)
                    has_c = t.get("has_cot", False) or c_tok > 0
                    cot_label = f"🧠 {c_tok:,} tokens" if has_c else "⚡ Trực tiếp"
                    if has_c:
                        all_cot_records.append({**t, "model_display": m_name})

                    task_row = {
                        "Mô Hình": m_name,
                        "Bài Toán": t.get("task_name", ""),
                        "Tập": t.get("group", ""),
                        "Kết Quả Z3": "✅ PASS" if is_pass else "❌ FAIL",
                        "Phân Loại Ảo Giác (Nature 2024)": h_badge,
                        "Lượt Thử": f"Pass@{t.get('iterations')}" if is_pass else ">3",
                        "Thời Gian (s)": t.get("duration_sec", 0.0),
                    }
                    if has_cot_in_summary or all_cot_records:
                        task_row["Suy Luận CoT"] = cot_label
                    all_detailed.append(task_row)

        # --- BỘ 3 BIỂU ĐỒ CHUNG 1 HÀNG NGANG (DASHBOARD TRỰC QUAN GỌN GÀNG) ---
        col_fig1, col_fig2, col_fig3 = st.columns([1, 1, 1.15])
        with col_fig1:
            st.markdown("##### 🎯 Tỷ Lệ Đạt (Pass Rate)")
            fig_pass = px.bar(
                df_summary,
                x="display_name",
                y=["pass_at_1_rate", "pass_at_k_rate"],
                barmode="group",
                labels={"value": "Tỷ lệ (%)", "variable": "Chỉ số", "display_name": "Mô hình"},
                color_discrete_sequence=["#38bdf8", "#22c55e"],
                text_auto=True,
            )
            # Chuẩn hóa tên hiển thị trên chú thích (Legend)
            metric_names = {"pass_at_1_rate": "Pass@1 (%)", "pass_at_k_rate": "Pass@K (%)"}
            fig_pass.for_each_trace(lambda t: t.update(name=metric_names.get(t.name, t.name)))
            fig_pass.update_xaxes(title_text="")
            fig_pass.update_layout(
                legend_title_text="",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
                margin=dict(l=10, r=10, t=30, b=20),
                height=360,
                bargap=0.35,
                bargroupgap=0.08,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pass, width="stretch")

        with col_fig2:
            st.markdown("##### ⏱️ Thời Gian TB (Latency)")
            fig_time = px.bar(
                df_summary,
                x="display_name",
                y="avg_duration_sec",
                labels={"avg_duration_sec": "Giây (s)", "display_name": "Mô hình"},
                color="avg_duration_sec",
                color_continuous_scale="Purples",
                text_auto=".1f",
            )
            fig_time.update_xaxes(title_text="")
            fig_time.update_layout(
                margin=dict(l=10, r=10, t=30, b=20),
                height=360,
                bargap=0.45,
                coloraxis_showscale=False,  # Ẩn thang đo màu bên phải để không bị bóp méo diện tích cột
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_time, width="stretch")

        with col_fig3:
            st.markdown("##### 🔬 Phân Bố Ảo Giác (Taxonomy)")
            if h_counts_by_model:
                # Đảm bảo hiển thị đầy đủ 5 tầng bản chất ảo giác H0 -> H4 chuẩn mực Nature 2024
                ordered_codes = ["H0", "H1", "H2", "H3", "H4"]
                code_labels = {
                    "H0": "H0: Zero-Hallucination",
                    "H1": "H1: Can Thiệp Đặc Tả",
                    "H2": "H2: Ngụy Biện Quy Nạp",
                    "H3": "H3: Vi Phạm Biên/Chỉ Số",
                    "H4": "H4: Trôi Dạt Ngữ Nghĩa",
                }
                color_map = {
                    "H0: Zero-Hallucination": "#22c55e",
                    "H1: Can Thiệp Đặc Tả": "#ef4444",
                    "H2: Ngụy Biện Quy Nạp": "#f97316",
                    "H3: Vi Phạm Biên/Chỉ Số": "#eab308",
                    "H4: Trôi Dạt Ngữ Nghĩa": "#a855f7",
                }

                df_h_chart = []
                for m_n, counts in h_counts_by_model.items():
                    for code in ordered_codes:
                        df_h_chart.append({
                            "Mô Hình": m_n,
                            "Tầng Ảo Giác": code_labels[code],
                            "Số Bài": counts.get(code, 0),
                            "Mã": code,
                        })
                df_h_plot = pd.DataFrame(df_h_chart)

                fig_h = px.bar(
                    df_h_plot,
                    x="Mô Hình",
                    y="Số Bài",
                    color="Tầng Ảo Giác",
                    color_discrete_map=color_map,
                    barmode="stack",
                    text_auto=True,
                )
                fig_h.update_xaxes(title_text="")
                fig_h.update_layout(
                    margin=dict(l=10, r=10, t=30, b=85),
                    height=360,
                    bargap=0.45,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend_title_text="",
                    # Bố trí ghi chú đầy đủ 5 mục bên dưới chia làm 2 cột
                    legend=dict(
                        orientation="h",
                        entrywidth=0.48,
                        entrywidthmode="fraction",
                        yanchor="top",
                        y=-0.18,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=9.5),
                    ),
                )
                st.plotly_chart(fig_h, width="stretch")
            else:
                st.caption("Chưa có dữ liệu phân loại ảo giác.")

        # --- KHUNG PHÂN LOẠI ẢO GIÁC HÌNH THỨC (NATURE 2024 & SMT SOLVER) ---
        with st.expander("📘 Khung Phân Loại Ảo Giác Mã Nguồn Hình Thức (Căn cứ Nature HSSC 2024 & Z3 SMT Solver)"):
            st.markdown(
                """
                Dựa trên công trình phân loại toàn diện của **Nature (2024)** và đặc thù kiểm định toán học **Dafny + Z3 Solver**, hệ thống phân rã kết quả sinh mã thành 5 tầng bản chất:
                * **✅ H0 (Zero-Hallucination)**: Mã nguồn được Z3 SMT Solver chứng minh toán học đúng đắn 100% trên toàn bộ không gian biến vô hạn.
                * **⚠️ H1 (Spec-Tampering)**: Ảo giác can thiệp đặc tả — mô hình tự ý xóa bỏ hoặc nới lỏng tiền/hậu điều kiện (bị chặn bởi băm SHA-256).
                * **🌀 H2 (Inductive Fallacy)**: Ảo giác ngụy biện quy nạp — bất biến vòng lặp (`invariant`) sai bước cơ sở hoặc không bảo toàn qua bước quy nạp.
                * **⚡ H3 (Boundary Overflow)**: Ảo giác vi phạm biên — truy xuất chỉ số mảng vượt kích thước (`out of bounds`), chỉ số âm hoặc chia cho 0.
                * **🌊 H4 (Semantic Drift)**: Trôi dạt ngữ nghĩa — code chạy được ca mẫu nhưng vi phạm hậu điều kiện tổng quát (`ensures`) trong không gian dữ liệu lớn.
                """
            )

        if all_detailed:
            st.markdown("---")
            st.markdown(f"##### 📝 Nhật Ký Chi Tiết Toàn Bộ {len(all_detailed)} Lượt Giải:")
            df_tasks = pd.DataFrame(all_detailed)
            st.dataframe(df_tasks, width="stretch", hide_index=True)

        # --- KHUNG PHÂN TÍCH HIỆN TƯỢNG OVERTHINKING & COT REASONING (TRỤC 2) ---
        with st.expander("🧠 Phân Tích Hiện Tượng 'Overthinking' & Chuỗi Suy Luận CoT (Căn cứ arXiv:2505.12886 & 2505.23646)"):
            if all_cot_records:
                col_cot1, col_cot2, col_cot3 = st.columns([1, 1, 1.2])
                pass_cots = [t.get("cot_tokens", 0) for t in all_cot_records if t.get("success")]
                fail_cots = [t.get("cot_tokens", 0) for t in all_cot_records if not t.get("success")]
                avg_pass_cot = round(sum(pass_cots) / len(pass_cots)) if pass_cots else 0
                avg_fail_cot = round(sum(fail_cots) / len(fail_cots)) if fail_cots else 0

                with col_cot1:
                    st.metric(
                        "CoT TB Bài Đạt (H0)",
                        f"{avg_pass_cot:,} tokens",
                        help="Độ dài suy luận trung bình của các bài giải trúng ngay và được Z3 chứng minh toán học.",
                    )
                with col_cot2:
                    delta_text = f"+{avg_fail_cot - avg_pass_cot:,} tokens (Overthinking)" if avg_fail_cot > avg_pass_cot else "Tương đương"
                    st.metric(
                        "CoT TB Bài Thất Bại (H1-H4)",
                        f"{avg_fail_cot:,} tokens",
                        delta=delta_text,
                        delta_color="inverse",
                        help="Các bài thất bại thường có lượng token suy luận cao hơn đáng kể (vòng lặp luẩn quẩn).",
                    )
                with col_cot3:
                    overthink_count = sum(1 for t in all_cot_records if t.get("cot_tokens", 0) > 800)
                    st.metric(
                        "Số Bài Chạm Ngưỡng Overthinking (>800 tokens)",
                        f"{overthink_count}/{len(all_cot_records)} bài",
                        help="Ngưỡng thực nghiệm theo arXiv:2505.12886: Suy luận trên 800 tokens cho một bài toán đơn thường sinh ra bất biến rác.",
                    )

                # Biểu đồ phân bổ độ dài CoT theo bài toán kèm đường ngưỡng Overthinking (800 tokens)
                cot_plot_data = []
                for rec in all_cot_records:
                    status_lbl = "✅ Đạt Chứng Minh (H0)" if rec.get("success") else f"❌ Vi Phạm ({rec.get('h_code', 'FAIL')})"
                    cot_plot_data.append({
                        "Bài Toán": f"{rec.get('task_name', '')}",
                        "Tokens CoT": rec.get("cot_tokens", 0),
                        "Trạng Thái": status_lbl,
                    })
                if cot_plot_data:
                    df_cot_plot = pd.DataFrame(cot_plot_data)
                    color_map = {
                        "✅ Đạt Chứng Minh (H0)": "#22c55e",
                        "❌ Vi Phạm (H1)": "#ef4444",
                        "❌ Vi Phạm (H2)": "#f97316",
                        "❌ Vi Phạm (H3)": "#eab308",
                        "❌ Vi Phạm (H4)": "#06b6d4",
                    }
                    fig_cot = px.bar(
                        df_cot_plot,
                        x="Bài Toán",
                        y="Tokens CoT",
                        color="Trạng Thái",
                        color_discrete_map=color_map,
                        text_auto=True,
                    )
                    fig_cot.add_hline(
                        y=800,
                        line_dash="dash",
                        line_color="#f43f5e",
                        annotation_text="Ngưỡng Nguy Cơ Overthinking (800 tokens)",
                        annotation_position="top right",
                        annotation_font=dict(color="#f43f5e", size=11),
                    )
                    fig_cot.update_layout(
                        margin=dict(l=10, r=10, t=30, b=20),
                        height=280,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend_title_text="",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
                    )
                    st.plotly_chart(fig_cot, width="stretch")

                # Soi chi tiết chuỗi suy luận CoT của từng bài
                st.markdown("##### 🔬 Kính Soi Chuỗi Suy Luận (CoT Inspector):")
                cot_options = {
                    f"[{t.get('model_display')}] {t.get('task_name')} ({'✅ PASS' if t.get('success') else '❌ ' + t.get('h_code', 'FAIL')}) - {t.get('cot_tokens', 0):,} tokens": t
                    for t in all_cot_records if t.get("cot_trace")
                }
                if cot_options:
                    selected_cot_label = st.selectbox(
                        "Chọn bài toán để xem toàn văn chuỗi suy luận của mô hình:",
                        list(cot_options.keys()),
                        key="sb_cot_inspector",
                    )
                    chosen_rec = cot_options[selected_cot_label]
                    st.text_area(
                        "Nội dung chuỗi suy luận bên trong thẻ <think>:",
                        value=chosen_rec.get("cot_trace", ""),
                        height=220,
                        disabled=True,
                    )
            else:
                st.info(
                    "💡 **Chưa có dữ liệu suy luận CoT trong lượt chạy hiện tại.** "
                    "Để kích hoạt đo lường và soi chuỗi suy luận Trục 2, hãy chọn mô hình suy luận sâu như **`ollama/deepseek-r1:7b`** tham gia đối đầu."
                )

        # Khung xuất mã bảng LaTeX cho bài báo khoa học
        with st.expander("📝 Bảng Mã LaTeX Chuẩn Cho Bài Báo Khoa Học (Nhấn để sao chép)"):
            st.caption("Sao chép đoạn mã LaTeX sau đây và dán trực tiếp vào tệp .tex của bài báo:")
            latex_code = active_data.get("latex_table", "")
            if not latex_code and summaries:
                latex_code = CrossModelEvaluator.generate_latex_table(summaries)
            st.code(latex_code, language="latex")
            st.download_button(
                "📥 Tải File LaTeX (.tex)",
                data=latex_code,
                file_name="cross_model_evaluation_table.tex",
                mime="text/plain",
            )
