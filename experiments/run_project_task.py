"""CLI for a pinned, multi-file Python repair task."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import uuid
from pathlib import Path

from dotenv import load_dotenv

from agents.patch_agent import LiteLLMPatchAgent
from core.project_benchmark import ProjectTask, evaluate_task
from core.swebench_grading import dataset_sha256, instance_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one repository repair benchmark task")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--model", required=True, help="Explicit LiteLLM model; Ollama is optional")
    parser.add_argument("--api-base")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--baseline", action="store_true", help="No verifier feedback; same maximum attempt budget")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--swebench-eval", action="store_true", help="Run official Docker harness after patch generation")
    parser.add_argument("--swebench-task-repo", type=Path, help="Optional local task repo for ARM Docker builds")
    parser.add_argument("--swebench-dataset", default="verified", help="Dataset alias or pinned local dataset path")
    args = parser.parse_args()

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    task = ProjectTask.load(args.manifest)
    agent = LiteLLMPatchAgent(args.model, api_base=args.api_base)
    report = evaluate_task(task, agent, max_attempts=args.max_attempts,
                           use_feedback=not args.baseline)
    report["mode"] = "baseline" if args.baseline else "framework"
    if task.backend == "swebench":
        predictions = args.output.with_suffix(".predictions.jsonl")
        predictions.parent.mkdir(parents=True, exist_ok=True)
        predictions.write_text(json.dumps({"instance_id": task.id, "model_name_or_path": args.model,
                                           "model_patch": report["final_patch"]}, ensure_ascii=False) + "\n", encoding="utf-8")
        report["prediction_file"] = str(predictions)
        if args.swebench_eval:
            if not shutil.which("swebench"):
                report["python_tests"] = {"status": "unavailable", "reason": "Install the official SWE-bench harness"}
            else:
                run_id = "fvil-" + uuid.uuid4().hex[:12]
                command = ["swebench", "eval", args.swebench_dataset, "-p", str(predictions), "--run-id", run_id,
                           "-i", task.id, "-j", "1"]
                if args.swebench_task_repo:
                    command += ["--task-repo", str(args.swebench_task_repo)]
                try:
                    proc = subprocess.run(command, text=True, capture_output=True, timeout=7200)
                    summary_path = Path("logs/evaluation") / run_id / "results.json"
                    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else None
                    status = instance_status(summary, task.id) if summary else "harness_error"
                    report["python_tests"] = {"status": status, "backend": "official_swebench_docker",
                                              "run_id": run_id, "dataset": args.swebench_dataset,
                                              "dataset_sha256": dataset_sha256(args.swebench_dataset),
                                              "return_code": proc.returncode, "summary": summary,
                                              "output_tail": (proc.stdout + proc.stderr)[-4000:]}
                except subprocess.TimeoutExpired:
                    report["python_tests"] = {"status": "timeout", "backend": "official_swebench_docker"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {args.output}")
    print("Python tests:", report["python_tests"]["status"])
    print("Dafny verification:", report["dafny_verification"]["status"])
    print("Specification audit:", report["spec_audit"]["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
