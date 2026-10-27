"""Evaluate proof-hint restoration separately from repository repair."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv

from core.batch_execution import iter_completed
from core.dafny_engine import DafnyEngine
from core.project_formal import audit_has_findings
from core.spec_locker import SpecLocker


_HINT_START = ("invariant ", "decreases ", "assert ", "reveal ")


def _candidate(raw: str) -> str:
    match = re.search(r"```dafny\s*\n(.*?)```", raw, re.S | re.I)
    return (match.group(1) if match else raw).strip() + "\n"


def _only_hints_added(original: str, candidate: str) -> bool:
    source = [line.strip() for line in original.splitlines() if line.strip()]
    output = [line.strip() for line in candidate.splitlines() if line.strip()]
    for tag, _, _, start, end in difflib.SequenceMatcher(None, source, output, autojunk=False).get_opcodes():
        if tag not in {"equal", "insert"}:
            return False
        if tag == "insert" and any(not line.startswith(_HINT_START) for line in output[start:end]):
            return False
    return True


def _ask_model(model: str, source: str, feedback: str, max_tokens: int) -> tuple[str, dict]:
    import litellm
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": "Restore missing Dafny proof hints. Add only invariant, decreases, assert or reveal lines. Preserve every existing line and contract exactly. Never use assume, axioms or verification bypasses. Return the complete .dfy file in a dafny code fence."},
            {"role": "user", "content": f"Source:\n```dafny\n{source}\n```\n\nVerifier feedback:\n{feedback[-4000:]}"},
        ],
        max_tokens=max_tokens,
        timeout=180,
    )
    usage = getattr(response, "usage", None)
    try:
        cost = float(litellm.completion_cost(completion_response=response))
    except Exception:
        cost = None
    return response.choices[0].message.content or "", {"prompt_tokens": getattr(usage, "prompt_tokens", None),
                                                         "completion_tokens": getattr(usage, "completion_tokens", None),
                                                         "cost_usd": cost, "resolved_model": getattr(response, "model", None)}


def run_one(path: Path, expected_hash: str, model: str, max_attempts: int) -> dict:
    original = path.read_text(encoding="utf-8")
    if hashlib.sha256(original.encode()).hexdigest() != expected_hash:
        raise ValueError(f"Pinned benchmark file was changed: {path}")
    engine = DafnyEngine(timeout_sec=30)
    if not engine.is_available():
        raise RuntimeError("Dafny is unavailable")
    feedback = ""
    attempts = []
    start = time.monotonic()
    for attempt_no in range(1, max_attempts + 1):
        raw, usage = _ask_model(model, original, feedback, max_tokens=8192)
        candidate = _candidate(raw)
        integrity = SpecLocker.validate(original, candidate)
        line_safe = _only_hints_added(original, candidate)
        hint_safe = line_safe and not re.search(r"\bdecreases\s*\*|\{:\s*(?:axiom|verify\s+false|extern)\b", candidate, re.I)
        attempt = {"number": attempt_no, "usage": usage, "hint_integrity_valid": hint_safe,
                   "original_code_preserved": line_safe, "strict_contract_issues": list(integrity.issues)}
        if not hint_safe:
            feedback = "Only add proof hints; preserve every original source line and contract."
            attempt["status"] = "invalid_candidate"
            attempts.append(attempt)
            continue
        result = engine.verify(candidate, extract_counterexample=False)
        attempt["dafny_output"] = result.output[-5000:]
        if result.is_verified:
            with tempfile.TemporaryDirectory(prefix="dafnybench-audit-") as tmp:
                target = Path(tmp) / "candidate.dfy"
                target.write_text(candidate, encoding="utf-8")
                audit = subprocess.run([str(engine.dafny_bin), "audit", str(target)], text=True,
                                       capture_output=True, timeout=45)
                attempt["audit_output"] = (audit.stdout + audit.stderr)[-5000:]
                attempt["status"] = "passed" if audit.returncode == 0 and not audit_has_findings(attempt["audit_output"]) else "audit_failed"
        else:
            attempt["status"] = "verification_failed"
        attempts.append(attempt)
        if attempt["status"] == "passed":
            break
        feedback = attempt.get("dafny_output", "") + "\n" + attempt.get("audit_output", "")
    return {"task_id": path.stem, "suite": "dafnybench20", "model": model,
            "status": attempts[-1]["status"], "attempts": attempts,
            "elapsed_seconds": time.monotonic() - start}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", help="One task ID; default is all 20")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--workers", type=int, default=1,
                        help="Independent cases in parallel (1-8; default 1)")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if args.max_attempts < 1:
        parser.error("--max-attempts must be positive")
    if not 1 <= args.workers <= 8:
        parser.error("--workers must be between 1 and 8")
    suite = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "dafnybench20"
    index = json.loads((suite / "index.json").read_text(encoding="utf-8"))
    tasks = [entry for entry in index["tasks"] if not args.task or entry["id"] == args.task]
    if not tasks:
        parser.error(f"No such task: {args.task}")
    completed = iter_completed(
        tasks,
        lambda entry: run_one(suite / entry["file"], entry["hint_sha256"], args.model, args.max_attempts),
        workers=args.workers,
    )
    results_by_index = {}
    for index, _, result in completed:
        results_by_index[index] = result
        print(f"[dafnybench {len(results_by_index)}/{len(tasks)}] "
              f"{result['task_id']}: {result['status']}", flush=True)
    results = [results_by_index[index] for index in sorted(results_by_index)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"suite": "dafnybench20", "model": args.model,
                                       "workers": args.workers,
                                       "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Completed {len(results)} tasks; verified and audited: {sum(x['status'] == 'passed' for x in results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
