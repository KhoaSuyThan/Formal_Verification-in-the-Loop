"""Run the fixed 30-task Python pilot, with optional official Docker grading."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import uuid
from pathlib import Path

from dotenv import load_dotenv

from agents.patch_agent import LiteLLMPatchAgent
from core.batch_execution import iter_completed
from core.project_benchmark import ProjectTask, evaluate_task
from core.swebench_grading import dataset_sha256, instance_status


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-base")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--workers", type=int, default=1,
                        help="Parallel isolated project tasks (1-4; default 1)")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--grade", action="store_true", help="Run the official SWE-bench Docker harness")
    parser.add_argument("--swebench-task-repo", type=Path)
    parser.add_argument("--swebench-dataset", default="verified", help="Dataset alias or pinned local dataset path")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if args.max_attempts < 1 or args.limit < 1 or not 1 <= args.workers <= 4:
        parser.error("attempts and limit must be positive; workers must be 1-4")
    if args.grade and not shutil.which("swebench"):
        parser.error("The official swebench CLI is required for --grade")
    suite = Path(__file__).resolve().parents[1] / "data/benchmarks/python_projects"
    index = json.loads((suite / "index.json").read_text(encoding="utf-8"))
    ids = index["tasks"][:args.limit]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for mode in ("baseline", "framework"):
        def run_case(task_id: str) -> dict:
            report_path = args.output_dir / mode / f"{task_id}.json"
            if report_path.exists():
                report = json.loads(report_path.read_text(encoding="utf-8"))
                if (report.get("task_id") != task_id or report.get("model") != args.model
                        or report.get("mode") != mode or report.get("max_attempts") != args.max_attempts):
                    raise ValueError(f"Existing report uses a different task, model, mode or attempt limit: {report_path}")
            else:
                task = ProjectTask.load(suite / f"{task_id}.json")
                agent = LiteLLMPatchAgent(args.model, api_base=args.api_base)
                report = evaluate_task(task, agent, max_attempts=args.max_attempts,
                                       use_feedback=mode == "framework")
                report["mode"] = mode
                report["workers"] = args.workers
                _write(report_path, report)
            return report

        reports_by_id = {}
        for _, task_id, report in iter_completed(ids, run_case, workers=args.workers):
            reports_by_id[task_id] = report
            print(f"[{mode} {len(reports_by_id)}/{len(ids)}] {task_id}: {report['python_tests']['status']}", flush=True)
        predictions = []
        for task_id in ids:
            report = reports_by_id[task_id]
            predictions.append({"instance_id": task_id, "model_name_or_path": args.model,
                                "model_patch": report.get("final_patch", "")})
        prediction_path = args.output_dir / f"{mode}.predictions.jsonl"
        prediction_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in predictions), encoding="utf-8")
        if args.grade:
            run_id = f"fvil-{mode}-{uuid.uuid4().hex[:12]}"
            command = ["swebench", "eval", args.swebench_dataset, "-p", str(prediction_path), "--run-id", run_id, "-j", "1"]
            if args.swebench_task_repo:
                command += ["--task-repo", str(args.swebench_task_repo)]
            proc = subprocess.run(command, text=True, capture_output=True, timeout=14400)
            summary_path = Path("logs/evaluation") / run_id / "results.json"
            if not summary_path.exists():
                raise RuntimeError(f"SWE-bench did not produce results: {proc.stderr[-3000:]}")
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            for task_id in ids:
                report_path = args.output_dir / mode / f"{task_id}.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report["python_tests"] = {"status": instance_status(summary, task_id),
                                          "backend": "official_swebench_docker", "run_id": run_id,
                                          "dataset": args.swebench_dataset,
                                          "dataset_sha256": dataset_sha256(args.swebench_dataset),
                                          "return_code": proc.returncode}
                _write(report_path, report)
            _write(args.output_dir / f"{mode}.swebench-summary.json", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
