"""Module điều khiển vòng lặp kiểm định hình thức khép kín (Pass@K Pipeline Controller).

Kết nối Generator/Repair Agent, SpecLocker, DafnyEngine và DiagnosticParser thành một chu trình Actor-Critic khép kín.
"""

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional
from core.spec_locker import SpecLocker
from core.template_preserver import TemplatePreserver
from core.syntax_normalizer import SyntaxNormalizer
from core.dafny_engine import DafnyEngine, VerifyResult
from core.diagnostic_parser import DiagnosticParser
from core.topology_detector import TopologyDetector, AlgorithmTopology
from core.ast_localizer import ASTLocalizer
from agents.llm_agent import LLMAgent

# Ngưỡng tương đồng mã nguồn để phát hiện vòng lặp nghẽn
STAGNATION_THRESHOLD = 0.90


@dataclass
class IterationLog:
    """Ghi nhận chi tiết từng lượt kiểm định và sửa lỗi."""
    iteration: int
    code: str
    is_spec_valid: bool
    is_verified: bool
    error_message: str
    error_taxonomy: str


@dataclass
class PipelineResult:
    """Kết quả tổng hợp của toàn bộ chu trình Pass@K cho một bài toán."""
    task_name: str
    is_success: bool
    total_iterations: int
    final_code: str
    history: List[IterationLog] = field(default_factory=list)
    failure_reason: str = ""


class PipelineController:
    """Bộ điều phối vòng lặp khép kín Formal Verification-in-the-Loop."""

    def __init__(
        self,
        agent: LLMAgent,
        engine: DafnyEngine,
        max_k: int = 3,
        verbose: bool = True
    ):
        """Khởi tạo controller với agent sinh mã, engine kiểm định và số vòng lặp tối đa."""
        self.agent = agent
        self.engine = engine
        self.max_k = max_k
        self.verbose = verbose

    @staticmethod
    def _is_stagnated(prev_code: str, new_code: str) -> bool:
        """Phát hiện vòng lặp nghẽn bằng cách so sánh độ tương đồng mã nguồn."""
        if not prev_code or not new_code:
            return False
        ratio = SequenceMatcher(None, prev_code.strip(), new_code.strip()).ratio()
        return ratio >= STAGNATION_THRESHOLD

    def _postprocess_code(self, raw_spec: str, generated_code: str) -> str:
        """Chuỗi hậu xử lý mã sinh ra: TemplatePreserver → SyntaxNormalizer."""
        code = TemplatePreserver.preserve_code(raw_spec, generated_code)
        code = SyntaxNormalizer.normalize(code)
        return code

    def run_task(self, raw_spec: str, task_name: str = "sample_task") -> PipelineResult:
        """Thực thi chu trình kiểm định và tự sửa lỗi khép kín cho một đề bài Dafny."""
        original_hash = SpecLocker.get_hash(raw_spec)
        history: List[IterationLog] = []

        topology = TopologyDetector.detect(raw_spec)
        topology_directive = TopologyDetector.get_topology_directive(topology)

        if self.verbose:
            print(f"\n[Pha 1: Sinh mã ban đầu | Hình thái: {topology.value}] Đang yêu cầu LLM sinh mã...")

        directive_text = f"\n\n{topology_directive}\n" if topology_directive else ""
        prompt = (
            f"Hãy hoàn thiện phương thức Dafny sau để vượt qua kiểm định hình thức Z3:\n\n"
            f"{raw_spec}"
            f"{directive_text}"
        )

        current_code = self.agent.generate_code(prompt)
        # Hậu xử lý: bảo toàn template + chuẩn hóa cú pháp
        current_code = self._postprocess_code(raw_spec, current_code)

        # Vòng lặp kiểm định & tự sửa lỗi
        for k in range(1, self.max_k + 1):
            if self.verbose:
                print(f"\n---> [Vòng lặp Pass@{k}/{self.max_k}]")
                print(f"[Mã nguồn hiện tại]:\n{current_code}\n")

            # 1. Kiểm tra tính toàn vẹn của mệnh đề ensures (Chống gian lận)
            spec_valid = SpecLocker.is_valid(original_hash, current_code, raw_spec=raw_spec)
            if not spec_valid:
                if self.verbose:
                    print(f"❌ [Spec-Locking]: CẢNH BÁO! LLM đã tự ý sửa đổi mệnh đề ensures gốc.")
                log_entry = IterationLog(
                    iteration=k,
                    code=current_code,
                    is_spec_valid=False,
                    is_verified=False,
                    error_message="AI tự ý sửa đổi hoặc xóa bỏ điều kiện ensures gốc.",
                    error_taxonomy="SpecTamperingViolation"
                )
                history.append(log_entry)
                return PipelineResult(
                    task_name=task_name,
                    is_success=False,
                    total_iterations=k,
                    final_code=current_code,
                    history=history,
                    failure_reason="SpecTamperingViolation: Vi phạm tính toàn vẹn đặc tả ensures."
                )

            if self.verbose:
                print("🛡️ [Spec-Locking]: HỢP LỆ (100% khớp mã băm SHA-256).")

            # 2. Thực hiện kiểm định hình thức bằng Dafny/Z3
            verify_res: VerifyResult = self.engine.verify(current_code)

            if verify_res.is_verified:
                if self.verbose:
                    print(f"🏆 [Dafny Engine]: KIỂM ĐỊNH THÀNH CÔNG! Z3 đã chứng minh tính đúng đắn 100%.")
                log_entry = IterationLog(
                    iteration=k,
                    code=current_code,
                    is_spec_valid=True,
                    is_verified=True,
                    error_message="",
                    error_taxonomy="None"
                )
                history.append(log_entry)
                return PipelineResult(
                    task_name=task_name,
                    is_success=True,
                    total_iterations=k,
                    final_code=current_code,
                    history=history
                )

            # Trường hợp kiểm định thất bại: Dùng Semantic Diagnostic Engine bóc tách lỗi chi tiết
            detailed_feedback, err_cat = DiagnosticParser.format_diagnostic_feedback(current_code, verify_res.output)
            summary_err = DiagnosticParser.extract_error(verify_res.output, current_code)

            if self.verbose:
                print(f"❌ [Dafny Engine]: Kiểm định thất bại.")
                print(f"   Loại lỗi: {err_cat}")
                print(f"   Chi tiết: {summary_err}")

            log_entry = IterationLog(
                iteration=k,
                code=current_code,
                is_spec_valid=True,
                is_verified=False,
                error_message=summary_err,
                error_taxonomy=err_cat
            )
            history.append(log_entry)

            # 3. Pha sửa lỗi (Repair Phase) nếu chưa chạm ngưỡng max_k
            if k < self.max_k:
                if self.verbose:
                    print(f"\n[Pha sửa lỗi {k} -> {k+1}] Đang gửi chẩn đoán ngữ nghĩa sang Repair Agent để vá mã...")

                # Lần sửa thứ nhất với thông tin chẩn đoán giàu ngữ cảnh
                repair_feedback = detailed_feedback
                if topology == AlgorithmTopology.DIRECT:
                    repair_feedback = f"{topology_directive}\n\n{detailed_feedback}"

                repaired_code = self.agent.repair_code(current_code, repair_feedback, raw_spec)
                repaired_code = self._postprocess_code(raw_spec, repaired_code)

                # Phát hiện Stagnation ngay lập tức: Nếu mã mới sinh trùng lặp >= 90% với mã hiện tại
                if self._is_stagnated(current_code, repaired_code):
                    if self.verbose:
                        print(f"⚡ [Stagnation Detected]: Mã sửa đổi trùng lặp >= 90% với mã lỗi — kích hoạt thử lại với nhiệt độ cao và chiến thuật phá nghẽn...")

                    original_temp = self.agent.temperature
                    self.agent.temperature = min(0.7, original_temp + 0.4)

                    failed_attempts = "\n".join(
                        f"Lượt {log.iteration}: [{log.error_taxonomy}] {log.error_message}"
                        for log in history if not log.is_verified
                    )
                    enriched_feedback = (
                        f"{detailed_feedback}\n\n"
                        f"⚠️ CẢNH BÁO NGHẼN MÃ NGUỒN (STAGNATION DETECTED):\n"
                        f"Bạn vừa sinh ra đoạn mã gần như trùng khớp 100% với mã đã bị Z3 bác bỏ trước đó.\n"
                        f"Lịch sử lỗi các lượt trước:\n{failed_attempts}\n\n"
                        f"YÊU CẦU BẮT BUỘC ĐỂ PHÁ NGHẼN:\n"
                        f"1. BẠN ĐÃ QUÊN THÊM INVARIANT: Đọc kỹ phần '[HÀNH ĐỘNG BẮT BUỘC]' trong hướng dẫn chẩn đoán ở trên.\n"
                        f"2. BẮT BUỘC chèn ít nhất một mệnh đề `invariant` cụ thể tương ứng vào sau từ khóa `while`.\n"
                        f"3. TUYỆT ĐỐI KHÔNG gửi lại mã nguồn cũ mà không bổ sung mệnh đề invariant mới."
                    )
                    repaired_code = self.agent.repair_code(current_code, enriched_feedback, raw_spec)
                    repaired_code = self._postprocess_code(raw_spec, repaired_code)
                    self.agent.temperature = original_temp

                current_code = repaired_code

        return PipelineResult(
            task_name=task_name,
            is_success=False,
            total_iterations=self.max_k,
            final_code=current_code,
            history=history,
            failure_reason=f"Không thể chứng minh tính đúng đắn sau {self.max_k} vòng lặp."
        )

