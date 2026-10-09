"""Module điều phối và đánh giá thực nghiệm so sánh chéo đa mô hình (Cross-Model Evaluation).

Hỗ trợ so sánh hiệu năng giữa các mô hình cục bộ (Ollama) và đám mây (Gemini Cloud)
trong vòng lặp kiểm chứng hình thức Dafny + Z3 Solver.
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

from agents.llm_agent import LLMAgent
from core.dafny_engine import DafnyEngine
from core.pipeline_controller import PipelineController, PipelineResult
from core.hallucination_classifier import classify_hallucination, FormalHallucinationType
from web_demo.helpers import get_flat_task_registry, load_task_spec


import concurrent.futures
import threading
from core.verification_cache import VerificationCache


@dataclass
class ModelBenchmarkSummary:
    """Tóm tắt các chỉ số hiệu năng của một mô hình trong thử nghiệm."""
    model_name: str
    display_name: str
    model_type: str  # 'Local (Ollama)' hoặc 'Cloud (Google AI)'
    total_tasks: int
    passed_tasks: int
    pass_at_1_count: int
    pass_at_k_count: int
    pass_at_1_rate: float
    pass_at_k_rate: float
    avg_duration_sec: float
    avg_repair_loops: float
    total_duration_sec: float
    avg_cot_tokens: float = 0.0  # Chỉ số L_CoT trung bình phục vụ nghiên cứu Overthinking (Trục 2)
    cegar_repaired_count: int = 0  # Số bài sửa lỗi thành công nhờ phản ví dụ CEGAR (Trục 3)


class CrossModelEvaluator:
    """Bộ điều phối thực nghiệm so sánh chéo đa mô hình."""

    DEFAULT_MODELS = [
        {
            "id": "ollama/qwen2.5-coder:7b",
            "name": "Qwen2.5-Coder-7B",
            "type": "Local (Ollama)",
            "description": "Baseline chuyên biệt sinh mã hình thức (Alibaba)"
        },
        {
            "id": "gemini-2.5-flash",
            "name": "Gemini 2.5 Flash",
            "type": "Cloud (Google AI)",
            "description": "Mô hình đám mây Google tốc độ cao, quota tiêu chuẩn 1500 req/ngày"
        },
        {
            "id": "gemini-3.5-flash",
            "name": "Gemini 3.5 Flash",
            "type": "Cloud (Google AI)",
            "description": "Mô hình đám mây Google thế hệ 3.x tốc độ cao, hỗ trợ sinh mã Dafny tất định"
        },
        {
            "id": "gemini-3.6-flash",
            "name": "Gemini 3.6 Flash",
            "type": "Cloud (Google AI)",
            "description": "Mô hình đám mây thử nghiệm 2026 (Free Tier giới hạn 20 req/ngày)"
        },
        {
            "id": "ollama/llama3.1:8b",
            "name": "LLaMA-3.1-8B",
            "type": "Local (Ollama)",
            "description": "Mô hình mã nguồn mở tổng quát (Meta)"
        },
        {
            "id": "ollama/deepseek-r1:7b",
            "name": "DeepSeek-R1-7B",
            "type": "Local (Ollama)",
            "description": "Mô hình lập luận suy luận sâu Chain-of-Thought (DeepSeek)"
        },
        {
            "id": "groq/qwen/qwen3.8-27b",
            "name": "Qwen-3.8-27B-Groq",
            "type": "Cloud (Groq LPU)",
            "description": "Mô hình Qwen thế hệ mới 27B tốc độ siêu tốc trên chip LPU (Alibaba / Groq)"
        },
        {
            "id": "groq/openai/gpt-oss-120b",
            "name": "GPT-OSS-120B-Groq",
            "type": "Cloud (Groq LPU)",
            "description": "Mô hình mã nguồn mở siêu lớn 120B trên chip LPU (OpenAI OSS / Groq)"
        },
        {
            "id": "groq/openai/gpt-oss-20b",
            "name": "GPT-OSS-20B-Groq",
            "type": "Cloud (Groq LPU)",
            "description": "Mô hình mã nguồn mở gọn nhẹ 20B trên chip LPU (OpenAI OSS / Groq)"
        }
    ]

    def __init__(self, dafny_path: Optional[str] = None):
        """Khởi tạo evaluator với đường dẫn Dafny Engine."""
        self.dafny_path = dafny_path

    @staticmethod
    def _run_single_task(
        task_label: str,
        meta: Dict[str, Any],
        model_id: str,
        controller: PipelineController,
        max_attempts: int
    ) -> Dict[str, Any]:
        """Thực thi một bài toán độc lập qua vòng lặp kiểm chứng hình thức."""
        short_name = meta["short_name"]
        spec_content = load_task_spec(meta["rel_path"])
        start_time = time.time()
        try:
            res: PipelineResult = controller.run_task(spec_content, task_name=short_name)
            duration = time.time() - start_time
        except Exception as e:
            duration = time.time() - start_time
            print(f"[CẢNH BÁO BENCHMARK]: Lỗi tại bài {short_name} trên {model_id}: {e}")
            res = PipelineResult(
                task_name=short_name,
                is_success=False,
                total_iterations=max_attempts,
                final_code="",
                history=[],
                failure_reason=str(e)
            )

        loops = max(0, res.total_iterations - 1)
        is_pass = res.is_success

        # Phân loại ảo giác toán học H0 - H4 chuẩn Nature 2024
        last_err = res.failure_reason or (res.history[-1].error_message if res.history else "")
        h_report = classify_hallucination(
            is_success=is_pass,
            is_tampered=getattr(res, "is_spec_tampered", False),
            error_message=last_err
        )

        # Ghi nhận chỉ số suy luận sâu Chain-of-Thought (Trục 2 - arXiv:2505.12886)
        cot_tokens = getattr(res, "total_cot_tokens", 0)
        cot_trace = getattr(res, "final_cot_trace", "")
        has_cot = cot_tokens > 0 or bool(cot_trace)
        cot_preview = (cot_trace[:140].replace("\n", " ") + "...") if len(cot_trace) > 140 else cot_trace.replace("\n", " ")

        # Ghi nhận chỉ số phản ví dụ CEGAR (Trục 3 - arXiv:2506.06923)
        has_cegar = getattr(res, "has_cegar", False)
        has_cegar_repaired = getattr(res, "has_cegar_repaired", False)
        ce_desc = next((l.counterexample_desc for l in res.history if getattr(l, "counterexample_desc", None)), "")

        return {
            "task_key": task_label,
            "task_name": short_name,
            "group": meta["group"],
            "success": is_pass,
            "iterations": res.total_iterations,
            "duration_sec": round(duration, 2),
            "repair_loops": loops,
            "h_code": h_report["code"],
            "h_badge": h_report["badge"],
            "h_name": h_report["name"],
            "has_cot": has_cot,
            "cot_tokens": cot_tokens,
            "cot_preview": cot_preview,
            "cot_trace": cot_trace,
            "has_cegar": has_cegar,
            "has_cegar_repaired": has_cegar_repaired,
            "counterexample_desc": ce_desc
        }

    @staticmethod
    def _execute_task_worker(
        task_label: str,
        meta: Dict[str, Any],
        model_id: str,
        engine: DafnyEngine,
        max_attempts: int
    ) -> Dict[str, Any]:
        # Khởi tạo LLMAgent với timeout 180s (3 phút) tránh đứt kết nối trên bài toán nặng
        agent = LLMAgent(model_name=model_id, timeout_sec=180)
        controller = PipelineController(
            agent=agent,
            engine=engine,
            max_k=max_attempts,
            verbose=False
        )
        return CrossModelEvaluator._run_single_task(
            task_label=task_label,
            meta=meta,
            model_id=model_id,
            controller=controller,
            max_attempts=max_attempts
        )

    def run_benchmark(
        self,
        model_ids: List[str],
        task_keys: Optional[List[str]] = None,
        max_attempts: int = 3,
        progress_callback: Optional[Callable[..., None]] = None,
        stop_check: Optional[Callable[[], bool]] = None,
        resume_from_checkpoint: bool = False,
        workers: int = 1,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Thực hiện chạy benchmark đối đầu giữa các mô hình được chọn.
        
        Args:
            model_ids: Danh sách mã định danh mô hình (vd: ['ollama/qwen2.5-coder:7b', 'gemini-3.6-flash'])
            task_keys: Danh sách key bài toán từ registry (None = chạy tất cả 30 tasks)
            max_attempts: Số lần sửa tối đa mỗi bài (Pass@K)
            progress_callback: Hàm nhận callback (model_id, current_step, total_steps, status_text)
            stop_check: Hàm kiểm tra tín hiệu dừng an toàn
            resume_from_checkpoint: Nếu True, nạp checkpoint gần nhất và tiếp tục chạy từ bài chưa hoàn thành
            workers: Số lượng luồng chạy song song (1 = tuần tự, >1 = đa luồng concurrent)
            use_cache: Nếu True, kích hoạt SMT Verification Memoization Cache
            
        Returns:
            Dict chứa 'summaries', 'detailed_results', 'timestamp', và 'latex_table'
        """
        registry = get_flat_task_registry()
        if task_keys:
            selected_tasks = {k: v for k, v in registry.items() if k in task_keys}
        else:
            selected_tasks = registry

        total_steps = len(model_ids) * len(selected_tasks)
        current_step = 0

        # Kiểm tra và nạp checkpoint nếu người dùng kích hoạt chế độ tiếp tục (Resume)
        cached_data: Optional[Dict[str, Any]] = None
        latest_file = os.path.join("artifacts", "results", "cross_model_benchmark_latest.json")
        if resume_from_checkpoint and os.path.exists(latest_file):
            try:
                with open(latest_file, "r", encoding="utf-8") as f_chk:
                    cached_data = json.load(f_chk)
            except Exception as err:
                print(f"[CẢNH BÁO RESUME]: Không thể nạp checkpoint: {err}")

        # Khởi tạo khung summaries cho tất cả mô hình để UI có thể hiển thị đầy đủ ngay từ đầu
        initial_summaries = []
        for m_id in model_ids:
            existing_s = None
            if cached_data and "summaries" in cached_data:
                existing_s = next((s for s in cached_data["summaries"] if s.get("model_name") == m_id), None)

            if existing_s:
                initial_summaries.append(existing_s)
            else:
                m_info = self._get_model_info(m_id)
                initial_summaries.append({
                    "model_name": m_id,
                    "display_name": m_info["name"],
                    "model_type": m_info["type"],
                    "total_tasks": 0,
                    "passed_tasks": 0,
                    "pass_at_1_count": 0,
                    "pass_at_k_count": 0,
                    "pass_at_1_rate": 0.0,
                    "pass_at_k_rate": 0.0,
                    "avg_duration_sec": 0.0,
                    "avg_repair_loops": 0.0,
                    "total_duration_sec": 0.0
                })

        initial_detailed = {m_id: [] for m_id in model_ids}
        if cached_data and "detailed_results" in cached_data:
            for m_id in model_ids:
                if m_id in cached_data["detailed_results"]:
                    initial_detailed[m_id] = list(cached_data["detailed_results"][m_id])

        benchmark_results: Dict[str, Any] = {
            "timestamp": cached_data.get("timestamp", datetime.now().isoformat()) if cached_data else datetime.now().isoformat(),
            "task_count": len(selected_tasks),
            "max_attempts": max_attempts,
            "models_evaluated": model_ids,
            "workers": workers,
            "use_cache": use_cache,
            "summaries": initial_summaries,
            "detailed_results": initial_detailed
        }

        # Khởi tạo SMT Verification Cache (nếu được kích hoạt)
        smt_cache = VerificationCache() if use_cache else None
        engine = DafnyEngine(dafny_path=self.dafny_path, cache=smt_cache)
        lock = threading.Lock()

        for model_id in model_ids:
            if stop_check and stop_check():
                print("[CROSS-MODEL]: Đã nhận tín hiệu dừng, ngắt sớm chuỗi mô hình.")
                break

            display_info = self._get_model_info(model_id)
            task_records = list(benchmark_results["detailed_results"].get(model_id, []))
            completed_keys = {r["task_key"] for r in task_records if "task_key" in r}

            pass_at_1 = sum(1 for r in task_records if r.get("success") and r.get("iterations") == 1)
            pass_at_k = sum(1 for r in task_records if r.get("success"))
            total_duration = sum(r.get("duration_sec", 0.0) for r in task_records)
            total_loops = sum(r.get("repair_loops", 0) for r in task_records)

            # Lọc các bài toán chưa hoàn thành
            pending_tasks = []
            for task_label, meta in selected_tasks.items():
                if resume_from_checkpoint and task_label in completed_keys:
                    current_step += 1
                    prev_status = next((r.get("success", False) for r in task_records if r.get("task_key") == task_label), False)
                    status_desc = "✅ ĐÃ ĐẠT" if prev_status else "❌ CHƯA ĐẠT"
                    if progress_callback:
                        progress_callback(
                            model_id,
                            current_step,
                            total_steps,
                            f"Kế thừa từ checkpoint: {display_info['name']} trên bài {meta['short_name']} ({status_desc}) [{current_step}/{total_steps}]",
                            benchmark_results
                        )
                else:
                    pending_tasks.append((task_label, meta))

            # Hàm cập nhật tiến trình và checkpoint luồng an toàn (Thread-Safe)
            def on_task_completed(rec: Dict[str, Any]):
                nonlocal pass_at_1, pass_at_k, total_duration, total_loops, current_step
                with lock:
                    current_step += 1
                    task_records.append(rec)
                    is_pass = rec.get("success", False)
                    if is_pass:
                        pass_at_k += 1
                        if rec.get("iterations") == 1:
                            pass_at_1 += 1
                    total_duration += rec.get("duration_sec", 0.0)
                    total_loops += rec.get("repair_loops", 0)

                    cur_n = len(task_records)
                    cur_summary = ModelBenchmarkSummary(
                        model_name=model_id,
                        display_name=display_info["name"],
                        model_type=display_info["type"],
                        total_tasks=cur_n,
                        passed_tasks=pass_at_k,
                        pass_at_1_count=pass_at_1,
                        pass_at_k_count=pass_at_k,
                        pass_at_1_rate=round((pass_at_1 / cur_n * 100.0) if cur_n > 0 else 0.0, 1),
                        pass_at_k_rate=round((pass_at_k / cur_n * 100.0) if cur_n > 0 else 0.0, 1),
                        avg_duration_sec=round((total_duration / cur_n) if cur_n > 0 else 0.0, 2),
                        avg_repair_loops=round((total_loops / cur_n) if cur_n > 0 else 0.0, 2),
                        total_duration_sec=round(total_duration, 2),
                        avg_cot_tokens=round((sum(r.get("cot_tokens", 0) for r in task_records) / cur_n) if cur_n > 0 else 0.0, 1),
                        cegar_repaired_count=sum(1 for r in task_records if r.get("has_cegar_repaired"))
                    )

                    temp_summaries = [s for s in benchmark_results["summaries"] if s["model_name"] != model_id]
                    temp_summaries.append(asdict(cur_summary))
                    benchmark_results["summaries"] = temp_summaries
                    benchmark_results["detailed_results"][model_id] = task_records
                    benchmark_results["latex_table"] = self.generate_latex_table(benchmark_results["summaries"])
                    if smt_cache:
                        benchmark_results["cache_stats"] = smt_cache.stats()

                    self._save_checkpoint(benchmark_results)

                    if progress_callback:
                        short_name = rec.get("task_name", "")
                        status_str = "ĐẠT" if is_pass else "CHƯA ĐẠT"
                        try:
                            progress_callback(
                                model_id,
                                current_step,
                                total_steps,
                                f"Hoàn thành {short_name} ({status_str}) — Đã chạy {cur_n}/{len(selected_tasks)} bài",
                                benchmark_results
                            )
                        except TypeError:
                            progress_callback(
                                model_id,
                                current_step,
                                total_steps,
                                f"Hoàn thành {short_name} ({status_str}) — Đã chạy {cur_n}/{len(selected_tasks)} bài"
                            )

            # Thực thi bài toán: Tuần tự nếu workers=1, Đa luồng nếu workers > 1
            if workers <= 1:
                for task_label, meta in pending_tasks:
                    if stop_check and stop_check():
                        print(f"[CROSS-MODEL]: Đã nhận tín hiệu dừng tại {model_id} trước bài {meta.get('short_name')}.")
                        break
                    rec = self._execute_task_worker(
                        task_label=task_label,
                        meta=meta,
                        model_id=model_id,
                        engine=engine,
                        max_attempts=max_attempts
                    )
                    on_task_completed(rec)
            else:
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    future_map = {
                        executor.submit(
                            self._execute_task_worker,
                            task_label,
                            meta,
                            model_id,
                            engine,
                            max_attempts
                        ): (task_label, meta)
                        for task_label, meta in pending_tasks
                    }
                    for future in concurrent.futures.as_completed(future_map):
                        if stop_check and stop_check():
                            print(f"[CROSS-MODEL]: Đã nhận tín hiệu dừng, hủy các bài còn lại của {model_id}.")
                            for f in future_map:
                                f.cancel()
                            break
                        try:
                            rec = future.result()
                            on_task_completed(rec)
                        except Exception as err:
                            t_label, m_info = future_map[future]
                            print(f"[LỖI ĐA LUỒNG]: Lỗi tại bài {m_info.get('short_name')} trên {model_id}: {err}")

        # Thống kê bộ nhớ đệm SMT cuối cùng
        if smt_cache:
            benchmark_results["cache_stats"] = smt_cache.stats()

        # Lưu bản lưu trữ chính thức có gắn timestamp khi hoàn thành trọn vẹn
        self._save_results(benchmark_results)

        return benchmark_results

    @staticmethod
    def _save_checkpoint(data: Dict[str, Any]):
        """Ghi đè checkpoint tức thì vào file latest để bảo toàn dữ liệu khi có sự cố."""
        output_dir = os.path.join("artifacts", "results")
        os.makedirs(output_dir, exist_ok=True)
        latest_filepath = os.path.join(output_dir, "cross_model_benchmark_latest.json")
        try:
            with open(latest_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as err:
            print(f"[CẢNH BÁO CHECKPOINT]: Không thể ghi checkpoint: {err}")

    def _get_model_info(self, model_id: str) -> Dict[str, str]:
        """Lấy thông tin hiển thị của model."""
        for m in self.DEFAULT_MODELS:
            if m["id"] == model_id:
                return m
        # Fallback tự động
        if "groq" in model_id.lower():
            m_type = "Cloud (Groq LPU)"
        elif "gemini" in model_id.lower():
            m_type = "Cloud (Google AI)"
        else:
            m_type = "Local"
        return {"id": model_id, "name": model_id.split("/")[-1], "type": m_type}

    @staticmethod
    def generate_latex_table(summaries: List[Dict[str, Any]]) -> str:
        """Tạo bảng LaTeX chuẩn bài báo khoa học từ tóm tắt benchmark."""
        has_cot = any(s.get("avg_cot_tokens", 0) > 0 for s in summaries)
        col_align = "lccccccc" if has_cot else "lcccccc"
        header_line = (
            r"\textbf{Model} & \textbf{Type} & \textbf{Tasks} & \textbf{Pass@1 (\%)} & \textbf{Pass@K (\%)} & \textbf{$T_{avg}$ (s)} & \textbf{Avg Loops} & \textbf{$L_{CoT}$ (tok)} \\"
            if has_cot else
            r"\textbf{Model} & \textbf{Type} & \textbf{Tasks} & \textbf{Pass@1 (\%)} & \textbf{Pass@K (\%)} & \textbf{$T_{avg}$ (s)} & \textbf{Avg Loops} \\"
        )

        latex_lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            r"\caption{Cross-Model Verification Performance Comparison}",
            r"\label{tab:cross_model_eval}",
            f"\\begin{{tabular}}{{{col_align}}}",
            r"\toprule",
            header_line,
            r"\midrule"
        ]

        for s in summaries:
            cot_part = f" & {s.get('avg_cot_tokens', 0):.0f}" if has_cot else ""
            line = (
                f"{s['display_name']} & {s['model_type']} & {s['total_tasks']} & "
                f"{s['pass_at_1_rate']}\\% & {s['pass_at_k_rate']}\\% & "
                f"{s['avg_duration_sec']} & {s['avg_repair_loops']}{cot_part} \\\\"
            )
            latex_lines.append(line)

        latex_lines.extend([
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}"
        ])
        return "\n".join(latex_lines)

    @staticmethod
    def _save_results(data: Dict[str, Any]) -> str:
        """Lưu kết quả benchmark ra file JSON."""
        output_dir = os.path.join("artifacts", "results")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cross_model_benchmark_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        latest_filepath = os.path.join(output_dir, "cross_model_benchmark_latest.json")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        with open(latest_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath
