"""Module điều khiển vòng lặp kiểm định hình thức khép kín (Pass@K Pipeline Controller).

Kết nối Generator/Repair Agent, SpecLocker, DafnyEngine và DiagnosticParser thành một chu trình Actor-Critic khép kín.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from core.spec_locker import SpecLocker
from core.dafny_engine import DafnyEngine, VerifyResult
from core.diagnostic_parser import DiagnosticParser
from agents.llm_agent import LLMAgent


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

    def run_task(self, raw_spec: str, task_name: str = "sample_task") -> PipelineResult:
        """Thực thi chu trình kiểm định và tự sửa lỗi khép kín cho một đề bài Dafny."""
        original_hash = SpecLocker.get_hash(raw_spec)
        history: List[IterationLog] = []

        if self.verbose:
            print(f"\n[Pha 1: Sinh mã ban đầu] Đang yêu cầu LLM sinh mã thuật toán...")

        prompt = (
            f"Hãy hoàn thiện phương thức Dafny sau để vượt qua kiểm định hình thức Z3:\n\n"
            f"{raw_spec}"
        )
        current_code = self.agent.generate_code(prompt)

        # Vòng lặp kiểm định & tự sửa lỗi
        for k in range(1, self.max_k + 1):
            if self.verbose:
                print(f"\n---> [Vòng lặp Pass@{k}/{self.max_k}]")
                print(f"[Mã nguồn hiện tại]:\n{current_code}\n")

            # 1. Kiểm tra tính toàn vẹn của mệnh đề ensures (Chống gian lận)
            spec_valid = SpecLocker.is_valid(original_hash, current_code)
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

            # Trường hợp kiểm định thất bại: Bóc tách lỗi Z3 và phân loại taxonomy
            err_msg = DiagnosticParser.extract_error(verify_res.output)
            err_cat = DiagnosticParser.classify_error(err_msg)

            if self.verbose:
                print(f"❌ [Dafny Engine]: Kiểm định thất bại.")
                print(f"   Loại lỗi: {err_cat}")
                print(f"   Chi tiết: {err_msg}")

            log_entry = IterationLog(
                iteration=k,
                code=current_code,
                is_spec_valid=True,
                is_verified=False,
                error_message=err_msg,
                error_taxonomy=err_cat
            )
            history.append(log_entry)

            # 3. Pha sửa lỗi (Repair Phase) nếu chưa chạm ngưỡng max_k
            if k < self.max_k:
                if self.verbose:
                    print(f"\n[Pha sửa lỗi {k} -> {k+1}] Đang gửi mã lỗi sang Repair Agent để vá mã...")
                current_code = self.agent.repair_code(current_code, err_msg, raw_spec)

        return PipelineResult(
            task_name=task_name,
            is_success=False,
            total_iterations=self.max_k,
            final_code=current_code,
            history=history,
            failure_reason=f"Không thể chứng minh tính đúng đắn sau {self.max_k} vòng lặp."
        )
