"""Unit test kiểm thử tính năng Đối Chuẩn Ablation Study (Bước 3).

Kiểm tra:
- Khả năng cấu hình cờ bóc tách trong PipelineController (enable_*).
- Khả năng sinh mã bảng LaTeX chuẩn booktabs của LaTeXExporter.
- Thuật toán bôi đậm chỉ số khoa học và escape ký tự an toàn.
"""

from unittest.mock import MagicMock
from core.pipeline_controller import PipelineController
from core.latex_exporter import LaTeXExporter
from core.dafny_engine import DafnyEngine
from agents.llm_agent import LLMAgent


def test_pipeline_ablation_flags_default():
    """Kiểm tra mặc định tất cả các cờ của Our System đều được bật (True)."""
    mock_agent = MagicMock(spec=LLMAgent)
    mock_engine = MagicMock(spec=DafnyEngine)
    controller = PipelineController(agent=mock_agent, engine=mock_engine)

    assert controller.enable_topology is True
    assert controller.enable_normalizer is True
    assert controller.enable_spec_locker is True
    assert controller.enable_semantic_hints is True
    assert controller.enable_cegar is True


def test_pipeline_ablation_flags_custom():
    """Kiểm tra cấu hình chế độ Stanford Clover Baseline (tất cả cờ đều False)."""
    mock_agent = MagicMock(spec=LLMAgent)
    mock_engine = MagicMock(spec=DafnyEngine)
    clover_controller = PipelineController(
        agent=mock_agent,
        engine=mock_engine,
        enable_topology=False,
        enable_normalizer=False,
        enable_spec_locker=False,
        enable_semantic_hints=False,
        enable_cegar=False,
    )

    assert clover_controller.enable_topology is False
    assert clover_controller.enable_normalizer is False
    assert clover_controller.enable_spec_locker is False
    assert clover_controller.enable_semantic_hints is False
    assert clover_controller.enable_cegar is False


def test_pipeline_normalizer_ablation():
    """Kiểm tra khi enable_normalizer=False, mã không qua SyntaxNormalizer."""
    mock_agent = MagicMock(spec=LLMAgent)
    mock_engine = MagicMock(spec=DafnyEngine)

    # Controller tắt normalizer
    controller_no_norm = PipelineController(
        agent=mock_agent,
        engine=mock_engine,
        enable_normalizer=False
    )
    raw_spec = "method Test(n: int)\n{\n}\n"
    # Mã có while không decreases
    gen_code = "method Test(n: int)\n{\n  var i := 0;\n  while i < n\n  {\n    i := i + 1;\n  }\n}\n"
    post_code = controller_no_norm._postprocess_code(raw_spec, gen_code)
    # Không được chèn decreases vì normalizer bị tắt
    assert "decreases" not in post_code

    # Controller bật normalizer
    controller_with_norm = PipelineController(
        agent=mock_agent,
        engine=mock_engine,
        enable_normalizer=True
    )
    post_code_norm = controller_with_norm._postprocess_code(raw_spec, gen_code)
    # Được chèn decreases vì normalizer được bật
    assert "decreases n - i" in post_code_norm


def test_latex_exporter_syntax():
    """Kiểm tra cú pháp bảng LaTeX booktabs cơ bản."""
    clover_stats = {
        "pass_at_1_rate": 30.0,
        "pass_at_k_rate": 50.0,
        "spec_tampering_rate": 20.0,
        "avg_repair_loops": 2.5,
        "avg_duration_sec": 35.0,
        "total_tasks": 10,
    }
    our_stats = {
        "pass_at_1_rate": 60.0,
        "pass_at_k_rate": 90.0,
        "spec_tampering_rate": 0.0,
        "avg_repair_loops": 1.4,
        "avg_duration_sec": 22.0,
        "cegar_repaired_count": 3,
        "total_tasks": 10,
    }

    latex = LaTeXExporter.generate_clover_comparison_table(clover_stats, our_stats)
    assert r"\begin{table}" in latex
    assert r"\end{table}" in latex
    assert r"\toprule" in latex
    assert r"\midrule" in latex
    assert r"\bottomrule" in latex
    assert "Stanford Clover" in latex
    assert "Our System" in latex


def test_latex_exporter_highlight():
    """Kiểm tra bôi đậm chỉ số tốt hơn giữa 2 phương pháp."""
    clover_stats = {
        "pass_at_1_rate": 40.0,
        "pass_at_k_rate": 60.0,
        "spec_tampering_rate": 15.0,
        "avg_repair_loops": 2.0,
        "avg_duration_sec": 30.0,
    }
    our_stats = {
        "pass_at_1_rate": 70.0,  # Cao hơn -> bôi đậm
        "pass_at_k_rate": 100.0, # Cao hơn -> bôi đậm
        "spec_tampering_rate": 0.0,  # Thấp hơn -> bôi đậm
        "avg_repair_loops": 1.2, # Thấp hơn -> bôi đậm
        "avg_duration_sec": 18.5, # Thấp hơn -> bôi đậm
        "cegar_repaired_count": 4,
    }

    latex = LaTeXExporter.generate_clover_comparison_table(clover_stats, our_stats)
    assert r"\textbf{70.0\%}" in latex
    assert r"\textbf{100.0\%}" in latex
    assert r"\textbf{0.0\%}" in latex
    assert r"\textbf{1.20}" in latex
    assert r"\textbf{18.5}" in latex


def test_latex_ablation_matrix_table():
    """Kiểm tra bảng ma trận bóc tách đa thành phần kỹ thuật."""
    configs = [
        {"name": "Full System (Ours)", "is_full": True, "pass_at_1_rate": 70.0, "pass_at_k_rate": 95.0, "spec_tampering_rate": 0.0, "avg_repair_loops": 1.3},
        {"name": "w/o Topology", "is_full": False, "pass_at_1_rate": 60.0, "pass_at_k_rate": 85.0, "spec_tampering_rate": 0.0, "avg_repair_loops": 1.7},
        {"name": "w/o Normalizer", "is_full": False, "pass_at_1_rate": 45.0, "pass_at_k_rate": 70.0, "spec_tampering_rate": 0.0, "avg_repair_loops": 2.1},
        {"name": "Clover Baseline", "is_full": False, "pass_at_1_rate": 35.0, "pass_at_k_rate": 55.0, "spec_tampering_rate": 18.0, "avg_repair_loops": 2.5},
    ]
    matrix_latex = LaTeXExporter.generate_ablation_matrix_table(configs)
    assert r"\begin{tabular}" in matrix_latex
    assert r"\textbf{Full System (Ours)}" in matrix_latex
    assert r"-10.0\%" in matrix_latex  # delta pass@3
    assert r"-25.0\%" in matrix_latex
