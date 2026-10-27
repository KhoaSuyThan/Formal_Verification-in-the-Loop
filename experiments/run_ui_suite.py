"""Track one complete new benchmark suite launched from Streamlit."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DAFNY_LINE = re.compile(r"^\[dafnybench (\d+)/20\]")
PYTHON_LINE = re.compile(r"^\[(baseline|framework) (\d+)/30\]")


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, choices=("dafnybench20", "python30"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--grade", action="store_true")
    parser.add_argument("--swebench-dataset")
    parser.add_argument("--swebench-task-repo", type=Path)
    args = parser.parse_args()
    if args.max_attempts < 1 or not 1 <= args.workers <= 4:
        parser.error("max-attempts must be positive; workers must be 1-4")
    if args.grade and args.suite != "python30":
        parser.error("Docker grading applies only to Python issues")

    run_dir = args.run_dir.resolve()
    status_path = run_dir / "status.json"
    dafny_output = run_dir / "dafnybench20.json"
    python_output = run_dir / "python_pilot"
    status = {
        "state": "running", "suite": args.suite, "model": args.model,
        "pid": os.getpid(), "grade": args.grade, "max_attempts": args.max_attempts,
        "workers": args.workers, "started_at": datetime.now(timezone.utc).isoformat(),
        "dafny_done": 0, "baseline_done": 0, "framework_done": 0,
        "total_steps": 20 if args.suite == "dafnybench20" else 60,
        "result_file": str(dafny_output) if args.suite == "dafnybench20" else None,
        "result_dir": str(python_output) if args.suite == "python30" else None,
    }
    _write(status_path, status)
    try:
        if args.suite == "dafnybench20":
            command = [sys.executable, "-m", "experiments.run_dafnybench20",
                       "--model", args.model, "--max-attempts", str(args.max_attempts),
                       "--workers", str(args.workers), "--output", str(dafny_output)]
        else:
            command = [sys.executable, "-m", "experiments.run_project_suite",
                       "--model", args.model, "--max-attempts", str(args.max_attempts),
                       "--limit", "30", "--workers", str(args.workers),
                       "--output-dir", str(python_output)]
            if args.grade:
                command.append("--grade")
                if args.swebench_dataset:
                    command += ["--swebench-dataset", args.swebench_dataset]
                if args.swebench_task_repo:
                    command += ["--swebench-task-repo", str(args.swebench_task_repo)]

        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1,
                                   env=os.environ.copy())
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            dafny = DAFNY_LINE.match(line)
            python = PYTHON_LINE.match(line)
            if dafny:
                status["dafny_done"] = int(dafny.group(1))
            elif python:
                status[f"{python.group(1)}_done"] = int(python.group(2))
                if args.grade and int(python.group(2)) == 30:
                    status["stage"] = f"Đang chấm Docker: {python.group(1)}"
            if dafny or python:
                _write(status_path, status)
        code = process.wait()
        if code:
            raise RuntimeError(f"Bộ chạy kết thúc với mã {code}; xem run.log")

        if args.suite == "dafnybench20":
            rows = json.loads(dafny_output.read_text(encoding="utf-8"))["results"]
            status["dafny_done"] = len(rows)
            status["verified_and_audited"] = sum(row["status"] == "passed" for row in rows)
        else:
            status["python_statuses"] = {}
            for mode in ("baseline", "framework"):
                rows = [json.loads(path.read_text(encoding="utf-8"))
                        for path in sorted((python_output / mode).glob("*.json"))]
                status[f"{mode}_done"] = len(rows)
                status["python_statuses"][mode] = {
                    outcome: sum(row["python_tests"]["status"] == outcome for row in rows)
                    for outcome in sorted({row["python_tests"]["status"] for row in rows})
                }
        status["state"] = "completed"
        status["finished_at"] = datetime.now(timezone.utc).isoformat()
        _write(status_path, status)
        _write(run_dir / "summary.json", status)
        return 0
    except Exception as exc:
        status["state"] = "failed"
        status["error"] = str(exc)
        status["finished_at"] = datetime.now(timezone.utc).isoformat()
        _write(status_path, status)
        print(f"Suite failed: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
