"""Giao diện Tab 1: Live Verification Pipeline (Đơn, Hàng Loạt & Playground).

Điều khiển quy trình kiểm định logic hình thức Actor-Critic khép kín:
- Chế độ Đơn (Single Task): Thẩm định 1 bài, hiển thị mã verified, badge CEGAR, CoT inspector.
- Chế độ Hàng Loạt (Batch Mode): Kiểm định danh mục bài toán, dừng tiến trình an toàn, soi chi tiết bài.
- Chế độ Tự Do (Dafny Playground): Soạn thảo và kiểm định đặc tả toán học tùy ý.
"""

import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
import streamlit as st

from agents.llm_agent import LLMAgent
from core.batch_execution import iter_completed
from core.dafny_engine import DafnyEngine
from core.pipeline_controller import PipelineController, PipelineResult
from core.spec_locker import SpecLocker
from core.topology_detector import TopologyDetector
from web_demo.icons import icon_heading, icon_svg, plain_label
from web_demo.helpers import (
    clear_last_batch_run,
    clear_last_single_run,
    dict_to_pipeline_result,
    load_last_batch_details,
    load_last_batch_run,
    load_last_single_run,
    load_task_spec,
    load_ui_state,
    save_last_batch_run,
    save_last_single_run,
    save_ui_state,
)




def render_pipeline_tab(
    exec_mode: str,
    selected_task_label: str,
    selected_task_file: str,
    selected_batch: List[str],
    model_name: str,
    max_k: int,
    timeout_sec: int,
    temperature: float,
    flat_registry: Dict[str, Any],
) -> None:
    """Hiển thị toàn bộ nội dung của Tab 1: Kiểm định trực tiếp."""
    if exec_mode == "Đơn":
        task_name = selected_task_label.split(" - ")[0]
        spec_content = load_task_spec(selected_task_file)
        detected_topology = TopologyDetector.detect(spec_content)
        spec_hash = SpecLocker.get_hash(spec_content)

        col_meta1, col_meta2, col_meta3 = st.columns([1.2, 1.2, 1])
        with col_meta1:
            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="glass-card-icon">{icon_svg('network')}</div>
                    <div>
                        <div class="glass-card-label">Hình Thái Giải Thuật</div>
                        <div class="glass-card-value" style="color: #38bdf8;">{detected_topology.value}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_meta2:
            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="glass-card-icon">{icon_svg('lock')}</div>
                    <div>
                        <div class="glass-card-label">Khóa Đặc Tả (Spec-Locking)</div>
                        <div class="glass-card-value" style="color: #a78bfa;">SHA-256: {spec_hash[:8]}...{spec_hash[-4:]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_meta3:
            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="glass-card-icon">{icon_svg('cpu')}</div>
                    <div>
                        <div class="glass-card-label">SMT Solver Backend</div>
                        <div class="glass-card-value" style="color: #4ade80;">Z3 Online ({timeout_sec}s)</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Xem mã đặc tả gốc của bài toán (Formal Specification)", expanded=False):
            st.code(spec_content, language="dafny")

        start_btn = st.button("Bắt đầu kiểm định và tự sửa lỗi", icon=":material/play_arrow:", type="primary", width="stretch")

        if start_btn:
            progress_bar = st.progress(0)
            status_placeholder = st.empty()

            status_placeholder.info(f"Đang kích hoạt quy trình Actor-Critic với mô hình `{model_name}`...")

            try:
                agent = LLMAgent(model_name=model_name, temperature=temperature)
                engine = DafnyEngine(timeout_sec=timeout_sec)
                controller = PipelineController(agent=agent, engine=engine, max_k=max_k, verbose=False)

                start_time = time.time()
                with st.spinner("Mô hình đang suy luận và Z3 SMT Solver đang thẩm định..."):
                    res: PipelineResult = controller.run_task(raw_spec=spec_content, task_name=task_name)
                elapsed = time.time() - start_time

                progress_bar.progress(100)

                # Lưu kết quả vào session_state để phục vụ Tab Diff
                st.session_state["last_result"] = res
                st.session_state["spec_content"] = spec_content

                # Lưu trữ kiên cố xuống đĩa để không bị mất khi F5 hoặc đóng tab
                save_last_single_run(
                    task_name=task_name,
                    task_label=selected_task_label,
                    spec_content=spec_content,
                    model_name=model_name,
                    max_k=max_k,
                    timeout_sec=timeout_sec,
                    result_obj=res,
                    elapsed=elapsed,
                )

                # Hiển thị thông báo trạng thái chung cuộc
                if res.is_success:
                    st.markdown(
                        f"""
                        <div class="status-card-pass">
                            {icon_svg('check')} XÁC MINH THÀNH CÔNG: Mã nguồn đã được Dafny & Z3 Solver chứng minh theo đặc tả!
                            <br><small>Thời gian thực thi: {elapsed:.2f}s | Đạt chứng nhận tại Lượt {res.total_iterations}/{max_k}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="status-card-fail">
                            {icon_svg('error')} THẤT BẠI: Không thể hội tụ chứng minh sau {res.total_iterations} vòng lặp.
                            <br><small>Lý do: {res.failure_reason}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Hiển thị chi tiết từng vòng lặp Pass@K
                st.markdown(icon_heading("Lịch sử các lượt kiểm định và tự sửa lỗi", "list"), unsafe_allow_html=True)
                for entry in res.history:
                    status_text = "Đã Chứng Minh (Verified)" if entry.is_verified else f"Vi Phạm: {entry.error_taxonomy}"

                    with st.expander(f"Lượt {entry.iteration}: {status_text}", expanded=True):
                        col_code, col_diag = st.columns([1.2, 1])

                        with col_code:
                            st.markdown("**Mã nguồn thuật toán:**")
                            st.code(entry.code, language="dafny")

                        with col_diag:
                            st.markdown("**Phản hồi từ Z3 Solver & Bộ Chẩn Đoán:**")
                            if entry.is_verified:
                                st.success("Z3 đã thẩm định thành công tất cả Verification Conditions (VCs).")
                            else:
                                st.error(f"**Lỗi phát hiện:** `{entry.error_taxonomy}`")
                                st.markdown(f"**Chi tiết:** {entry.error_message}")
                                if getattr(entry, "counterexample_desc", None):
                                    st.warning(f"**Phản ví dụ Z3 (CEGAR):** `{entry.counterexample_desc}`")

                        if getattr(entry, "cot_trace", None):
                            cot_tok = getattr(entry, "cot_tokens", 0)
                            with st.expander(f"Chuỗi suy luận CoT lượt {entry.iteration} ({cot_tok:,} tokens)", expanded=False):
                                st.caption("Nội dung mô hình tự suy luận bên trong thẻ `<think>` trước khi sinh mã:")
                                st.text_area(
                                    label=f"cot_view_live_{entry.iteration}",
                                    value=entry.cot_trace,
                                    height=150,
                                    disabled=True,
                                    label_visibility="collapsed",
                                )

            except Exception as e:
                st.error(f"Đã xảy ra lỗi trong quá trình thực thi: {str(e)}")

        else:
            # Khi người dùng chưa bấm chạy lượt mới: Nạp lịch sử kiểm định gần nhất từ đĩa nếu có
            saved_single = load_last_single_run()
            if saved_single:
                saved_res, saved_meta = dict_to_pipeline_result(saved_single)
                st.session_state["last_result"] = saved_res
                st.session_state["spec_content"] = saved_meta.get("spec_content", spec_content)

                col_s_info, col_s_clear = st.columns([4, 1])
                with col_s_info:
                    st.markdown(
                        f"""
                        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 8px 14px; margin-top: 8px;">
                            <span style="font-weight: 700; color: #38bdf8;">{icon_svg('clock')} Lịch sử lần chạy gần nhất:</span>
                            <span style="color: #e2e8f0;">Bài <strong>{saved_meta.get('task_name')}</strong> | Mô hình: <code>{saved_meta.get('model_name')}</code> | Lưu lúc: {saved_meta.get('timestamp')} | Thời gian: {saved_meta.get('elapsed', 0)}s</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_s_clear:
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                    if st.button("Xóa lịch sử", icon=":material/delete_outline:", key="btn_clear_single_run", width="stretch"):
                        clear_last_single_run()
                        if "last_result" in st.session_state:
                            del st.session_state["last_result"]
                        st.rerun()

                # Hiển thị trạng thái chung cuộc đã lưu
                if saved_res.is_success:
                    st.markdown(
                        f"""
                        <div class="status-card-pass">
                            {icon_svg('check')} XÁC MINH THÀNH CÔNG (DỮ LIỆU ĐÃ LƯU): Mã nguồn đã được Dafny & Z3 Solver chứng minh theo đặc tả!
                            <br><small>Thời gian thực thi: {saved_meta.get('elapsed', 0)}s | Đạt chứng nhận tại Lượt {saved_res.total_iterations}/{saved_meta.get('max_k', max_k)}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="status-card-fail">
                            {icon_svg('error')} THẤT BẠI (DỮ LIỆU ĐÃ LƯU): Không thể hội tụ chứng minh sau {saved_res.total_iterations} vòng lặp.
                            <br><small>Lý do: {saved_res.failure_reason}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Hiển thị chi tiết từng vòng lặp Pass@K đã lưu
                st.markdown(icon_heading("Lịch sử các lượt kiểm định và tự sửa lỗi", "list"), unsafe_allow_html=True)
                for entry in saved_res.history:
                    status_text = "Đã Chứng Minh (Verified)" if entry.is_verified else f"Vi Phạm: {entry.error_taxonomy}"

                    with st.expander(f"Lượt {entry.iteration}: {status_text}", expanded=False):
                        col_code, col_diag = st.columns([1.2, 1])

                        with col_code:
                            st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px;'>MÃ NGUỒN THUẬT TOÁN:</div>", unsafe_allow_html=True)
                            st.code(entry.code, language="dafny")

                        with col_diag:
                            st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px;'>PHẢN HỒI Z3 SOLVER & BỘ CHẨN ĐOÁN:</div>", unsafe_allow_html=True)
                            if entry.is_verified:
                                st.markdown(
                                    """
                                    <div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 6px; padding: 10px 12px; color: #86efac; font-size: 0.79rem; line-height: 1.5; text-align: justify;">
                                        <strong>Z3 SMT Solver:</strong> Đã thẩm định thành công tất cả Verification Conditions (VCs).
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            else:
                                st.markdown(
                                    f"""
                                    <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(248, 113, 113, 0.3); border-radius: 6px; padding: 6px 10px; color: #fca5a5; font-size: 0.78rem; font-weight: 600; margin-bottom: 6px;">
                                        Lỗi phát hiện: <span style="font-family: monospace; color: #f87171;">{entry.error_taxonomy}</span>
                                    </div>
                                    <div class="diag-box-text" style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(248, 113, 113, 0.2); border-radius: 6px; padding: 10px 12px; color: #cbd5e1; font-size: 0.79rem; line-height: 1.5; text-align: justify; margin-bottom: 6px;">
                                        <strong style="color: #f87171;">Chi tiết:</strong> {entry.error_message}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                if getattr(entry, "counterexample_desc", None):
                                    st.markdown(
                                        f"""
                                        <div class="diag-box-text" style="background: rgba(113, 63, 18, 0.25); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: 6px; padding: 8px 12px; color: #fde047; font-size: 0.78rem; line-height: 1.45; text-align: justify;">
                                            <strong>Phản ví dụ Z3 (CEGAR):</strong> <code>{entry.counterexample_desc}</code>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                        if getattr(entry, "cot_trace", None):
                            cot_tok = getattr(entry, "cot_tokens", 0)
                            with st.expander(f"Chuỗi suy luận CoT lượt {entry.iteration} ({cot_tok:,} tokens)", expanded=False):
                                st.caption("Nội dung mô hình tự suy luận bên trong thẻ `<think>` trước khi sinh mã:")
                                st.text_area(
                                    label=f"cot_view_saved_{entry.iteration}",
                                    value=entry.cot_trace,
                                    height=150,
                                    disabled=True,
                                    label_visibility="collapsed",
                                )

    elif exec_mode == "Hàng loạt":
        # ======================================================================
        # CHẾ ĐỘ HÀNG LOẠT (BATCH MULTI-SELECT MODE)
        # ======================================================================
        if not selected_batch:
            st.warning("Chưa có bài toán nào được chọn. Vui lòng dùng bộ chọn nhanh hoặc chọn bài toán ở thanh bên trái.")
        else:
            col_b1, col_b2, col_b3 = st.columns([1.2, 1.4, 1])
            with col_b1:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <div class="glass-card-icon">{icon_svg('layers')}</div>
                        <div>
                            <div class="glass-card-label">Tổng Bài Cần Chạy</div>
                            <div class="glass-card-value" style="color: #38bdf8;">{len(selected_batch)} Bài Toán</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            clover_cnt = sum(1 for k in selected_batch if flat_registry[k]["group"] == "Clover")
            humaneval_cnt = sum(1 for k in selected_batch if flat_registry[k]["group"] == "HumanEval")
            advanced_cnt = sum(1 for k in selected_batch if flat_registry[k]["group"] == "Advanced")
            with col_b2:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <div class="glass-card-icon">{icon_svg('tag')}</div>
                        <div>
                            <div class="glass-card-label">Cơ Cấu Benchmark</div>
                            <div class="glass-card-value" style="color: #a78bfa; font-size: 0.95rem;">{clover_cnt} Clover • {humaneval_cnt} HumanEval • {advanced_cnt} Mở Rộng</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_b3:
                st.markdown(
                    f"""
                    <div class="glass-card">
                        <div class="glass-card-icon">{icon_svg('cpu')}</div>
                        <div>
                            <div class="glass-card-label">Cấu Hình Z3 SMT</div>
                            <div class="glass-card-value" style="color: #4ade80;">Max K={max_k} ({timeout_sec}s)</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander(f"Danh mục chi tiết {len(selected_batch)} bài toán đã chọn", expanded=False):
                for idx_item, item_key in enumerate(selected_batch, 1):
                    item_info = flat_registry[item_key]
                    target_badge = "[Core Target]" if item_info["is_target"] else "[Extended]"
                    st.markdown(f"**{idx_item}.** `{item_info['short_name']}` ({item_info['group']}) — {target_badge} — *{item_info['rel_path']}*")

            batch_workers = st.slider(
                "Số bài chạy song song",
                min_value=1,
                max_value=4,
                value=1 if model_name.startswith("ollama/") else 2,
                help="Mỗi bài dùng một agent và tiến trình Dafny riêng. Chọn 1 để chạy tuần tự; tăng dần nếu hạn mức API cho phép.",
            )

            col_b_run, col_b_stop = st.columns([4, 2])
            with col_b_run:
                batch_btn = st.button(
                    f"Bắt đầu kiểm định hàng loạt ({len(selected_batch)} bài toán)",
                    icon=":material/play_arrow:",
                    type="primary",
                    width="stretch",
                )
            with col_b_stop:
                batch_stop_btn = st.button("Dừng tiến trình", icon=":material/stop:", type="secondary", width="stretch", help="Dừng an toàn chu trình kiểm định sau khi hoàn thành bài toán hiện tại")

            batch_stop_flag = os.path.join("artifacts", ".stop_batch_flag")
            if batch_stop_btn:
                Path(batch_stop_flag).touch()
                st.toast("Đã gửi lệnh dừng. Hệ thống sẽ dừng sau bài toán hiện tại.", icon=":material/stop:")
                st.warning("Đã kích hoạt lệnh dừng. Hệ thống đang hoàn tất bài hiện tại.")

            if batch_btn and os.path.exists(batch_stop_flag):
                try:
                    os.remove(batch_stop_flag)
                except Exception:
                    pass

            # Khung hiển thị tiến độ và kết quả
            batch_progress_bar = st.progress(0)
            batch_status = st.empty()
            batch_table_placeholder = st.empty()

            # Hiển thị lại kết quả lần chạy trước từ session_state hoặc file lưu kiên cố nếu có
            if not batch_btn:
                saved_batch = None
                if "last_batch_results" not in st.session_state:
                    saved_batch = load_last_batch_run()
                    if saved_batch and saved_batch.get("results_list"):
                        st.session_state["last_batch_results"] = saved_batch["results_list"]

                # Tự động nạp chi tiết các lượt chạy 1 2 3 đã lưu từ đĩa nếu session_state chưa có
                if "batch_history_dict" not in st.session_state or not st.session_state["batch_history_dict"]:
                    loaded_details = load_last_batch_details()
                    if loaded_details:
                        st.session_state["batch_history_dict"] = loaded_details

                if "last_batch_results" in st.session_state:
                    if saved_batch:
                        col_b_info, col_b_clear = st.columns([4, 1])
                        with col_b_info:
                            st.markdown(
                                f"""
                                <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 8px 14px; margin-bottom: 8px;">
                                    <span style="font-weight: 700; color: #38bdf8;">{icon_svg('clock')} Lịch sử đợt chạy gần nhất:</span>
                                    <span style="color: #e2e8f0;">Lưu lúc: {saved_batch.get('timestamp')} | Mô hình: <code>{saved_batch.get('model_name')}</code> | Song song: {saved_batch.get('workers', 1)} | Thời gian: {saved_batch.get('total_batch_time')}s ({len(saved_batch.get('results_list', []))} bài)</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with col_b_clear:
                            st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
                            if st.button("Xóa lịch sử", icon=":material/delete_outline:", key="btn_clear_batch_run", width="stretch"):
                                clear_last_batch_run()
                                if "last_batch_results" in st.session_state:
                                    del st.session_state["last_batch_results"]
                                if "batch_history_dict" in st.session_state:
                                    del st.session_state["batch_history_dict"]
                                st.rerun()

                    df_prev = pd.DataFrame(st.session_state["last_batch_results"])
                    if "Kết Quả Z3" in df_prev:
                        df_prev["Kết Quả Z3"] = df_prev["Kết Quả Z3"].map(plain_label)
                    batch_table_placeholder.dataframe(df_prev, width="stretch", hide_index=True)

            if batch_btn:
                results_list = []
                batch_history_dict = {}
                total_tasks = len(selected_batch)

                try:
                    serial_controller = None
                    if batch_workers == 1:
                        serial_controller = PipelineController(
                            agent=LLMAgent(model_name=model_name, temperature=temperature),
                            engine=DafnyEngine(timeout_sec=timeout_sec),
                            max_k=max_k,
                            verbose=False,
                        )

                    def run_case(item_key: str) -> tuple[str, PipelineResult, float]:
                        task_info = flat_registry[item_key]
                        spec = load_task_spec(task_info["rel_path"])
                        controller = serial_controller or PipelineController(
                            agent=LLMAgent(model_name=model_name, temperature=temperature),
                            engine=DafnyEngine(timeout_sec=timeout_sec),
                            max_k=max_k,
                            verbose=False,
                        )
                        start = time.monotonic()
                        result = controller.run_task(raw_spec=spec, task_name=task_info["short_name"])
                        return spec, result, time.monotonic() - start

                    batch_start_time = time.time()
                    results_by_index: dict[int, dict[str, Any]] = {}
                    batch_status.info(f"Đang kiểm định {total_tasks} bài, tối đa {batch_workers} bài song song...")

                    for idx, item_key, completed in iter_completed(
                        selected_batch,
                        run_case,
                        workers=batch_workers,
                        stop_requested=lambda: os.path.exists(batch_stop_flag),
                    ):
                        task_info = flat_registry[item_key]
                        task_name_item = task_info["short_name"]
                        task_group_item = task_info["group"]
                        spec_item, res_item, duration_item = completed

                        batch_history_dict[task_name_item] = {
                            "result": res_item,
                            "spec": spec_item,
                            "info": task_info,
                        }

                        status_label = "PASS" if res_item.is_success else "FAIL"
                        convergence_str = f"Pass@{res_item.total_iterations}" if res_item.is_success else f">{max_k}"

                        results_by_index[idx] = {
                            "STT": idx + 1,
                            "Bài Toán": task_name_item,
                            "Tập Benchmark": task_group_item,
                            "Kết Quả Z3": status_label,
                            "Lượt Hội Tụ": convergence_str,
                            "Thời Gian (s)": round(duration_item, 2),
                            "Hình Thái": TopologyDetector.detect(spec_item).value,
                        }
                        results_list = [results_by_index[i] for i in sorted(results_by_index)]

                        # Cập nhật thanh tiến trình và bảng kết quả trực tiếp
                        batch_progress_bar.progress(len(results_by_index) / total_tasks)
                        batch_status.info(f"Đã hoàn thành {len(results_by_index)}/{total_tasks} bài; gần nhất: `{task_name_item}`.")
                        df_current = pd.DataFrame(results_list)
                        batch_table_placeholder.dataframe(df_current, width="stretch", hide_index=True)

                    if os.path.exists(batch_stop_flag):
                        batch_status.warning(f"Đã dừng an toàn sau {len(results_list)}/{total_tasks} bài.")
                        Path(batch_stop_flag).unlink(missing_ok=True)

                    total_batch_time = time.time() - batch_start_time
                    st.session_state["last_batch_results"] = results_list
                    st.session_state["batch_history_dict"] = batch_history_dict

                    # Lưu kiên cố đợt chạy hàng loạt vào artifacts/results/last_batch_run.json và last_batch_details.json
                    save_last_batch_run(
                        results_list=results_list,
                        total_batch_time=total_batch_time,
                        model_name=model_name,
                        max_k=max_k,
                        timeout_sec=timeout_sec,
                        batch_history_dict=batch_history_dict,
                        workers=batch_workers,
                    )

                    # Đếm số lượng pass
                    passed_count = sum(1 for r in results_list if "PASS" in r["Kết Quả Z3"])
                    completed_count = len(results_list)
                    pass_rate = (passed_count / completed_count * 100) if completed_count else 0.0

                    if completed_count == total_tasks and passed_count == total_tasks:
                        st.markdown(
                            f"""
                            <div class="status-card-pass">
                                {icon_svg('check')} HOÀN THÀNH TOÀN BỘ: {passed_count}/{total_tasks} bài toán đã được Dafny & Z3 xác minh theo đặc tả!
                                <br><small>Tổng thời gian thực thi: {total_batch_time:.2f}s | Tỷ lệ thành công: 100.0%</small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="status-card-pass" style="border-color: rgba(56, 189, 248, 0.4);">
                                {icon_svg('chart')} KẾT QUẢ THỰC NGHIỆM HÀNG LOẠT: Đạt {passed_count}/{completed_count} bài đã chạy ({pass_rate:.1f}%)
                                <br><small>Tổng thời gian: {total_batch_time:.2f}s | Mô hình: {model_name}</small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi trong quá trình chạy hàng loạt: {str(e)}")

            # Hiển thị trực tiếp lịch sử các lượt chạy 1, 2, 3 của từng bài toán trong danh sách hàng loạt
            has_history = "batch_history_dict" in st.session_state and bool(st.session_state["batch_history_dict"])
            has_results_list = "last_batch_results" in st.session_state and bool(st.session_state["last_batch_results"])

            if has_history or has_results_list:
                st.markdown("---")
                st.markdown(icon_heading("Lịch sử kiểm định của từng bài toán", "list"), unsafe_allow_html=True)

                if has_results_list:
                    r_map = {r["Bài Toán"]: r for r in st.session_state["last_batch_results"]}
                    task_keys_list = list(r_map.keys())
                    saved_batch_task = load_ui_state().get("batch_task")
                    default_idx = task_keys_list.index(saved_batch_task) if saved_batch_task in task_keys_list else 0

                    chosen_detail = st.selectbox(
                        "Chọn một bài toán trong danh sách để xem chi tiết tiến trình tự sửa lỗi (Lượt 1, 2, 3):",
                        task_keys_list,
                        index=default_idx,
                        format_func=lambda x: f"[{r_map[x].get('Tập Benchmark', '')}] {x} — {plain_label(r_map[x].get('Kết Quả Z3', ''))} ({r_map[x].get('Lượt Hội Tụ', '')} | {r_map[x].get('Thời Gian (s)', '')}s)",
                        key="batch_detail_selector",
                    )
                    if chosen_detail and chosen_detail != saved_batch_task:
                        save_ui_state({"batch_task": chosen_detail})
                else:
                    b_history = st.session_state["batch_history_dict"]
                    b_keys = list(b_history.keys())
                    saved_batch_task = load_ui_state().get("batch_task")
                    default_idx = b_keys.index(saved_batch_task) if saved_batch_task in b_keys else 0

                    chosen_detail = st.selectbox(
                        "Chọn một bài toán trong danh sách để xem chi tiết tiến trình tự sửa lỗi (Lượt 1, 2, 3):",
                        b_keys,
                        index=default_idx,
                        key="batch_detail_selector",
                    )
                    if chosen_detail and chosen_detail != saved_batch_task:
                        save_ui_state({"batch_task": chosen_detail})

                if chosen_detail:
                    # Nếu bài toán đã có chi tiết PipelineResult trong bộ nhớ
                    if has_history and chosen_detail in st.session_state["batch_history_dict"]:
                        detail_data = st.session_state["batch_history_dict"][chosen_detail]
                        detail_res: PipelineResult = detail_data["result"]
                        detail_spec: str = detail_data["spec"]

                        st.session_state["last_result"] = detail_res
                        st.session_state["spec_content"] = detail_spec

                        # Hiển thị thẻ trạng thái chung cuộc y như Chế độ Đơn
                        if detail_res.is_success:
                            st.markdown(
                                f"""
                                <div class="status-card-pass">
                                    {icon_svg('check')} XÁC MINH THÀNH CÔNG: Mã nguồn đã được Dafny & Z3 Solver chứng minh theo đặc tả!
                                    <br><small>Đạt chứng nhận tại Lượt {detail_res.total_iterations}/{max_k}</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f"""
                                <div class="status-card-fail">
                                    {icon_svg('error')} THẤT BẠI: Không thể hội tụ chứng minh sau {detail_res.total_iterations} vòng lặp.
                                    <br><small>Lý do: {detail_res.failure_reason}</small>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        # Hiển thị từng lượt 1, 2, 3 với mã nguồn và phản hồi Z3 y như Chế độ Đơn
                        for entry in detail_res.history:
                            status_text = "Đã Chứng Minh (Verified)" if entry.is_verified else f"Vi Phạm: {entry.error_taxonomy}"

                            with st.expander(f"Lượt {entry.iteration}: {status_text}", expanded=False):
                                col_code, col_diag = st.columns([1.2, 1])

                                with col_code:
                                    st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px;'>MÃ NGUỒN THUẬT TOÁN:</div>", unsafe_allow_html=True)
                                    st.code(entry.code, language="dafny")

                                with col_diag:
                                    st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; margin-bottom: 4px;'>PHẢN HỒI Z3 SOLVER & BỘ CHẨN ĐOÁN:</div>", unsafe_allow_html=True)
                                    if entry.is_verified:
                                        st.markdown(
                                            """
                                            <div style="background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(74, 222, 128, 0.3); border-radius: 6px; padding: 10px 12px; color: #86efac; font-size: 0.79rem; line-height: 1.5; text-align: justify;">
                                                <strong>Z3 SMT Solver:</strong> Đã thẩm định thành công tất cả Verification Conditions (VCs).
                                            </div>
                                            """,
                                            unsafe_allow_html=True,
                                        )
                                    else:
                                        st.markdown(
                                            f"""
                                            <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(248, 113, 113, 0.3); border-radius: 6px; padding: 6px 10px; color: #fca5a5; font-size: 0.78rem; font-weight: 600; margin-bottom: 6px;">
                                                Lỗi phát hiện: <span style="font-family: monospace; color: #f87171;">{entry.error_taxonomy}</span>
                                            </div>
                                            <div class="diag-box-text" style="background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(248, 113, 113, 0.2); border-radius: 6px; padding: 10px 12px; color: #cbd5e1; font-size: 0.79rem; line-height: 1.5; text-align: justify; margin-bottom: 6px;">
                                                <strong style="color: #f87171;">Chi tiết:</strong> {entry.error_message}
                                            </div>
                                            """,
                                            unsafe_allow_html=True,
                                        )
                                        if getattr(entry, "counterexample_desc", None):
                                            st.markdown(
                                                f"""
                                                <div class="diag-box-text" style="background: rgba(113, 63, 18, 0.25); border: 1px solid rgba(234, 179, 8, 0.35); border-radius: 6px; padding: 8px 12px; color: #fde047; font-size: 0.78rem; line-height: 1.45; text-align: justify;">
                                                    <strong>Phản ví dụ Z3 (CEGAR):</strong> <code>{entry.counterexample_desc}</code>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )

                                if getattr(entry, "cot_trace", None):
                                    cot_tok = getattr(entry, "cot_tokens", 0)
                                    with st.expander(f"Chuỗi suy luận CoT lượt {entry.iteration} ({cot_tok:,} tokens)", expanded=False):
                                        st.caption("Nội dung mô hình tự suy luận bên trong thẻ `<think>` trước khi sinh mã:")
                                        st.text_area(
                                            label=f"cot_view_batch_{chosen_detail}_{entry.iteration}",
                                            value=entry.cot_trace,
                                            height=150,
                                            disabled=True,
                                            label_visibility="collapsed",
                                        )

                    else:
                        # Trường hợp bài toán chưa có lịch sử chi tiết trong bộ nhớ (ví dụ chạy từ đợt trước)
                        r_info = r_map.get(chosen_detail, {})
                        meta_match = next((v for k, v in flat_registry.items() if v["short_name"] == chosen_detail), None)

                        col_inf1, col_inf2, col_inf3, col_inf4 = st.columns(4)
                        with col_inf1:
                            st.metric("Kết Quả Z3", plain_label(r_info.get("Kết Quả Z3", "N/A")))
                        with col_inf2:
                            st.metric("Lượt Hội Tụ", r_info.get("Lượt Hội Tụ", "N/A"))
                        with col_inf3:
                            st.metric("Thời Gian Thực Nghiệm", f"{r_info.get('Thời Gian (s)', 0)}s")
                        with col_inf4:
                            st.metric("Hình Thái Giải Thuật", r_info.get("Hình Thái", "N/A"))

                        if meta_match:
                            spec_c = load_task_spec(meta_match["rel_path"])
                            with st.expander(f"Xem đặc tả bài toán '{chosen_detail}' (.dfy)", expanded=False):
                                st.code(spec_c, language="dafny")

                            if st.button(f"Trích xuất các lượt chạy của bài '{chosen_detail}'", icon=":material/visibility:", type="primary", use_container_width=True):
                                with st.spinner(f"Đang kiểm định và ghi nhận vết tự sửa lỗi cho '{chosen_detail}'..."):
                                    ag = LLMAgent(model_name=model_name, temperature=temperature)
                                    eng = DafnyEngine(timeout_sec=timeout_sec)
                                    ctrl = PipelineController(agent=ag, engine=eng, max_k=max_k, verbose=False)
                                    res_item = ctrl.run_task(raw_spec=spec_c, task_name=chosen_detail)

                                    if "batch_history_dict" not in st.session_state:
                                        st.session_state["batch_history_dict"] = {}
                                    st.session_state["batch_history_dict"][chosen_detail] = {
                                        "result": res_item,
                                        "spec": spec_c,
                                        "info": meta_match,
                                    }
                                    st.session_state["last_result"] = res_item
                                    st.session_state["spec_content"] = spec_c

                                    # Tự động cập nhật vào last_batch_details.json
                                    save_last_batch_run(
                                        results_list=st.session_state.get("last_batch_results", []),
                                        total_batch_time=0.0,
                                        model_name=model_name,
                                        max_k=max_k,
                                        timeout_sec=timeout_sec,
                                        batch_history_dict=st.session_state["batch_history_dict"],
                                    )
                                    st.rerun()


    elif exec_mode == "Tự do":
        # ======================================================================
        # CHẾ ĐỘ SÂN CHƠI TỰ DO (CUSTOM DAFNY PLAYGROUND)
        # ======================================================================
        st.markdown(icon_heading("Sân chơi tự do (Custom Dafny Playground)", "file"), unsafe_allow_html=True)
        st.caption("Tự do thiết kế bài toán đặc tả hình thức (Formally Specified Method), viết tiền/hậu điều kiện và để LLM cùng Z3 Solver tổng hợp & kiểm định mã nguồn.")

        # Định nghĩa các mẫu bài toán thực nghiệm
        SAMPLE_MAX = """// Bài toán: Tìm giá trị lớn nhất trong mảng không rỗng
method FindMax(a: array<int>) returns (max: int)
  requires a.Length > 0
  ensures forall k :: 0 <= k < a.Length ==> a[k] <= max
  ensures exists k :: 0 <= k < a.Length && a[k] == max
{
  // LLM Agent sẽ tự động suy diễn thuật toán và loop invariant tại đây
}
"""

        SAMPLE_REVERSE = """// Bài toán: Đảo ngược các phần tử của mảng tại chỗ
method ReverseArray(a: array<int>)
  modifies a
  ensures forall k :: 0 <= k < a.Length ==> a[k] == old(a[a.Length - 1 - k])
{
  // LLM Agent sẽ tự động sinh vòng lặp đổi chỗ và invariants hai đầu
}
"""

        SAMPLE_BIN_SEARCH = """// Bài toán: Tìm kiếm nhị phân trên mảng đã sắp xếp
method BinarySearch(a: array<int>, target: int) returns (index: int)
  requires forall i, j :: 0 <= i < j < a.Length ==> a[i] <= a[j]
  ensures 0 <= index ==> index < a.Length && a[index] == target
  ensures index < 0 ==> forall k :: 0 <= k < a.Length ==> a[k] != target
{
  // LLM Agent sẽ thiết lập biến chặn low, high và chứng minh không sót phần tử
}
"""

        if "playground_code" not in st.session_state:
            st.session_state["playground_code"] = SAMPLE_MAX

        st.markdown(icon_heading("Nạp nhanh mẫu bài toán thực nghiệm", "folder", level=5), unsafe_allow_html=True)
        col_s1, col_s2, col_s3, col_s_clear = st.columns([1, 1, 1, 0.8])
        with col_s1:
            if st.button("1. Tìm Max (Mảng)", icon=":material/arrow_outward:", width="stretch"):
                st.session_state["playground_code"] = SAMPLE_MAX
                st.rerun()
        with col_s2:
            if st.button("2. Đảo Ngược Mảng", icon=":material/arrow_outward:", width="stretch"):
                st.session_state["playground_code"] = SAMPLE_REVERSE
                st.rerun()
        with col_s3:
            if st.button("3. Tìm Kiếm Nhị Phân", icon=":material/arrow_outward:", width="stretch"):
                st.session_state["playground_code"] = SAMPLE_BIN_SEARCH
                st.rerun()
        with col_s_clear:
            if st.button("Xóa trắng", icon=":material/close:", width="stretch"):
                st.session_state["playground_code"] = "// Nhập mã đặc tả Dafny của bạn tại đây\nmethod CustomTask()\n{\n}\n"
                st.rerun()

        custom_code_input = st.text_area(
            "Trình soạn thảo mã nguồn đặc tả Dafny (.dfy):",
            value=st.session_state["playground_code"],
            height=260,
            help="Hãy định nghĩa method cùng các mệnh đề requires / ensures. Bạn có thể để trống thân hàm hoặc viết mã chưa hoàn thiện.",
        )
        st.session_state["playground_code"] = custom_code_input

        col_run_pg, col_info_pg = st.columns([1.5, 2.5])
        with col_run_pg:
            run_pg_btn = st.button(
                "Bắt đầu kiểm chứng và tổng hợp mã",
                icon=":material/play_arrow:",
                type="primary",
                width="stretch",
            )
        with col_info_pg:
            st.caption(f"Cấu hình hiện tại: Mô hình **{model_name}** | Số vòng lặp tối đa **K={max_k}** | Timeout Z3: **{timeout_sec}s**")

        if run_pg_btn:
            if not custom_code_input.strip():
                st.warning("Vui lòng nhập mã đặc tả Dafny trước khi bắt đầu.")
            else:
                try:
                    with st.spinner("Agent đang phân tích đặc tả và suy diễn bất biến..."):
                        start_time = time.time()
                        agent = LLMAgent(model_name=model_name, temperature=temperature)
                        engine = DafnyEngine(timeout_sec=timeout_sec)
                        controller = PipelineController(agent=agent, engine=engine, max_k=max_k)

                        res_pg = controller.run_task(
                            raw_spec=custom_code_input,
                            task_name="Custom_Playground_Task",
                        )
                        elapsed_pg = time.time() - start_time

                    st.session_state["last_result"] = res_pg
                    st.session_state["spec_content"] = custom_code_input

                    if res_pg.is_success:
                        st.markdown(
                            f"""
                            <div class="status-card-pass">
                                {icon_svg('check')} XÁC MINH THÀNH CÔNG: Mã nguồn đã được Dafny & Z3 Solver chứng minh theo đặc tả!
                                <br><small>Thời gian thực thi: {elapsed_pg:.2f}s | Hội tụ tại Lượt {res_pg.total_iterations}/{max_k}</small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class="status-card-fail">
                                {icon_svg('error')} CHƯA HỘI TỤ CHỨNG MINH: Sau {res_pg.total_iterations} vòng lặp.
                                <br><small>Lý do: {res_pg.failure_reason}</small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown(icon_heading("Lịch sử các vòng lặp kiểm định", "list"), unsafe_allow_html=True)
                    for entry in res_pg.history:
                        status_text = "Đã Chứng Minh (Verified)" if entry.is_verified else f"Vi Phạm: {entry.error_taxonomy}"

                        with st.expander(f"Lượt {entry.iteration}: {status_text}", expanded=True):
                            col_c1, col_c2 = st.columns([1.2, 1])
                            with col_c1:
                                st.markdown("**Mã nguồn sinh bởi AI:**")
                                st.code(entry.code, language="dafny")
                            with col_c2:
                                st.markdown("**Chẩn đoán Z3 & Lập Luận:**")
                                if entry.is_verified:
                                    st.success("Z3 Solver đã thẩm định thành công tất cả Verification Conditions (VCs).")
                                else:
                                    st.error(f"**Lỗi phát hiện:** `{entry.error_taxonomy}`")
                                    st.markdown(f"**Chi tiết:** {entry.error_message}")

                except Exception as e:
                    st.error(f"Đã xảy ra lỗi trong quá trình thực thi: {str(e)}")
