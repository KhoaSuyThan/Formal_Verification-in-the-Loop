"""Module xuất bảng biểu định dạng LaTeX chuẩn bài báo khoa học (ACM/IEEE/Springer).

Cung cấp các công cụ tạo bảng LaTeX chuẩn booktabs:
- Bảng so sánh đối chuẩn Ablation Study giữa Stanford Clover (2024) và Hệ thống đề xuất.
- Bảng phân tích tác động bóc tách từng trụ cột kỹ thuật (Component Contribution).
"""

from typing import List, Dict, Any, Optional


class LaTeXExporter:
    """Bộ tạo bảng biểu LaTeX chuẩn khoa học phục vụ công bố quốc tế."""

    @staticmethod
    def escape_latex(text: str) -> str:
        """Thoát các ký tự đặc biệt trong LaTeX."""
        special_chars = {
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        for char, repl in special_chars.items():
            text = text.replace(char, repl)
        return text

    @classmethod
    def generate_clover_comparison_table(
        cls,
        clover_stats: Dict[str, Any],
        our_stats: Dict[str, Any],
        caption: str = "Ablation Study: Comparison between Stanford Clover Baseline and Our Neuro-Symbolic System",
        label: str = "tab:clover_vs_our_system",
    ) -> str:
        """Tạo bảng LaTeX booktabs so sánh đối đầu giữa Stanford Clover Baseline và Hệ Thống Đề Xuất.

        Các chỉ số đối chuẩn:
        - Pass@1 Rate (%)
        - Pass@K Rate (%)
        - Spec-Tampering Rate H1 (%)
        - Avg Repair Loops
        - Avg Duration (s)
        - CEGAR Recovered
        """
        # Xác định giá trị tốt hơn để bôi đậm
        p1_better = "our" if our_stats.get("pass_at_1_rate", 0) >= clover_stats.get("pass_at_1_rate", 0) else "clover"
        pk_better = "our" if our_stats.get("pass_at_k_rate", 0) >= clover_stats.get("pass_at_k_rate", 0) else "clover"
        tamper_better = "our" if our_stats.get("spec_tampering_rate", 0) <= clover_stats.get("spec_tampering_rate", 0) else "clover"
        loops_better = "our" if our_stats.get("avg_repair_loops", 0) <= clover_stats.get("avg_repair_loops", 0) else "clover"
        time_better = "our" if our_stats.get("avg_duration_sec", 0) <= clover_stats.get("avg_duration_sec", 0) else "clover"

        def fmt(val: float, is_bold: bool, is_pct: bool = False, decimals: int = 1) -> str:
            val_str = f"{val:.{decimals}f}"
            if is_pct:
                val_str += r"\%"
            return f"\\textbf{{{val_str}}}" if is_bold else val_str

        c_p1 = fmt(clover_stats.get("pass_at_1_rate", 0), p1_better == "clover", is_pct=True)
        o_p1 = fmt(our_stats.get("pass_at_1_rate", 0), p1_better == "our", is_pct=True)

        c_pk = fmt(clover_stats.get("pass_at_k_rate", 0), pk_better == "clover", is_pct=True)
        o_pk = fmt(our_stats.get("pass_at_k_rate", 0), pk_better == "our", is_pct=True)

        c_tamper = fmt(clover_stats.get("spec_tampering_rate", 0), tamper_better == "clover", is_pct=True)
        o_tamper = fmt(our_stats.get("spec_tampering_rate", 0), tamper_better == "our", is_pct=True)

        c_loops = fmt(clover_stats.get("avg_repair_loops", 0), loops_better == "clover", decimals=2)
        o_loops = fmt(our_stats.get("avg_repair_loops", 0), loops_better == "our", decimals=2)

        c_time = fmt(clover_stats.get("avg_duration_sec", 0), time_better == "clover", decimals=1)
        o_time = fmt(our_stats.get("avg_duration_sec", 0), time_better == "our", decimals=1)

        c_cegar = "-"
        o_cegar = str(our_stats.get("cegar_repaired_count", 0))

        c_tasks = clover_stats.get("total_tasks", 30)
        o_tasks = our_stats.get("total_tasks", 30)

        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            r"\begin{tabular}{lcccccc}",
            r"\toprule",
            r"\textbf{Method / Framework} & \textbf{Tasks} & \textbf{Pass@1} & \textbf{Pass@3} & \textbf{Spec-Tamper ($H_1$)} & \textbf{Avg Loops} & \textbf{$T_{avg}$ (s)} \\",
            r"\midrule",
            f"Stanford Clover (2024) Baseline & {c_tasks} & {c_p1} & {c_pk} & {c_tamper} & {c_loops} & {c_time} \\\\",
            f"\\textbf{{Our System (Neuro-Symbolic)}} & {o_tasks} & {o_p1} & {o_pk} & {o_tamper} & {o_loops} & {o_time} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
        return "\n".join(lines)

    @classmethod
    def generate_ablation_matrix_table(
        cls,
        configs: List[Dict[str, Any]],
        caption: str = "Detailed Component Ablation Study on Benchmark Suite",
        label: str = "tab:ablation_components",
    ) -> str:
        """Tạo bảng LaTeX bóc tách tác động của từng thành phần kỹ thuật.

        Hỗ trợ các cấu hình:
        - Full System (Our System)
        - w/o Topology (Tắt mồi hình thái)
        - w/o Normalizer (Tắt chuẩn hóa cú pháp & decreases/modifies)
        - w/o Spec-Locker (Tắt khóa đặc tả)
        - w/o CEGAR (Tắt phản ví dụ)
        - Clover Baseline (Tắt tất cả)
        """
        lines = [
            r"\begin{table}[htbp]",
            r"\centering",
            f"\\caption{{{caption}}}",
            f"\\label{{{label}}}",
            r"\begin{tabular}{lccccc}",
            r"\toprule",
            r"\textbf{Configuration} & \textbf{Pass@1 (\%)} & \textbf{Pass@3 (\%)} & \textbf{$\Delta$ Pass@3} & \textbf{Tampering ($H_1$)} & \textbf{Avg Loops} \\",
            r"\midrule",
        ]

        full_p3 = 0.0
        for cfg in configs:
            if cfg.get("is_full", False):
                full_p3 = cfg.get("pass_at_k_rate", 0.0)
                break

        for cfg in configs:
            name = cls.escape_latex(cfg.get("name", "Config"))
            p1 = f"{cfg.get('pass_at_1_rate', 0.0):.1f}"
            p3 = f"{cfg.get('pass_at_k_rate', 0.0):.1f}"
            diff = cfg.get("pass_at_k_rate", 0.0) - full_p3
            diff_str = f"{diff:+.1f}\\%" if not cfg.get("is_full", False) else "--"
            tamper = f"{cfg.get('spec_tampering_rate', 0.0):.1f}\\%"
            loops = f"{cfg.get('avg_repair_loops', 0.0):.2f}"

            if cfg.get("is_full", False):
                line = f"\\textbf{{{name}}} & \\textbf{{{p1}\\%}} & \\textbf{{{p3}\\%}} & {diff_str} & {tamper} & \\textbf{{{loops}}} \\\\"
            else:
                line = f"{name} & {p1}\\% & {p3}\\% & {diff_str} & {tamper} & {loops} \\\\"
            lines.append(line)

        lines.extend([
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ])
        return "\n".join(lines)
