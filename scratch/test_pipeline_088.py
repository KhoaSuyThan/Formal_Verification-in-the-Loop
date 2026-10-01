import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.llm_agent import LLMAgent
from core.dafny_engine import DafnyEngine
from core.pipeline_controller import PipelineController

def main():
    spec_path = Path("data/benchmarks/humaneval_dafny/088-sort_array.dfy")
    spec_content = spec_path.read_text(encoding="utf-8")
    
    agent = LLMAgent(model_name="ollama/qwen2.5-coder:7b", temperature=0.0)
    engine = DafnyEngine(timeout_sec=30)
    controller = PipelineController(agent=agent, engine=engine, max_k=3, verbose=True)
    
    print("Bắt đầu kiểm thử bài 088-sort_array...")
    res = controller.run_task(raw_spec=spec_content, task_name="088-sort_array")
    print(f"\nKết quả: Success = {res.is_success}, Iterations = {res.total_iterations}")
    if res.is_success:
        print("MÃ CHỨNG MINH THÀNH CÔNG:\n", res.final_code)
    else:
        print("Lý do thất bại:", res.failure_reason)

if __name__ == "__main__":
    main()
