"""Evaluate proof-hint restoration separately from repository repair."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Đảm bảo import được các module từ thư mục gốc của dự án
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

from core.batch_execution import iter_completed
from core.dafny_engine import DafnyEngine
from core.project_formal import audit_has_findings
from core.spec_locker import SpecLocker


_HINT_START = ("invariant ", "decreases ", "assert ", "reveal ", "calc ")
_ALLOWED_HINT_PATTERN = re.compile(
    r"^(?:invariant\b|decreases\b|assert\b|reveal\b|calc\b|//|/\*|\*|\*/)",
    re.IGNORECASE
)


def _candidate(raw: str) -> str:
    match = re.search(r"```dafny\s*\n(.*?)```", raw, re.S | re.I)
    return (match.group(1) if match else raw).strip() + "\n"


def _get_line_violations(original: str, candidate: str) -> list[str]:
    """Phát hiện các dòng bị xóa, sửa trái phép hoặc chèn không phải proof hint."""
    source = [line.strip() for line in original.splitlines() if line.strip()]
    output = [line.strip() for line in candidate.splitlines() if line.strip()]
    violations = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, source, output, autojunk=False).get_opcodes():
        if tag == "delete":
            deleted_snippet = " | ".join(source[i1:min(i2, i1 + 3)])
            violations.append(f"Original line(s) deleted: '{deleted_snippet}'")
        elif tag == "replace":
            orig_snippet = " | ".join(source[i1:min(i2, i1 + 3)])
            mod_snippet = " | ".join(output[j1:min(j2, j1 + 3)])
            violations.append(f"Original line(s) modified: from '{orig_snippet}' to '{mod_snippet}'")
        elif tag == "insert":
            for line in output[j1:j2]:
                if not _ALLOWED_HINT_PATTERN.match(line):
                    violations.append(f"Disallowed inserted line (not a proof hint): '{line[:80]}'")
    return violations


def _only_hints_added(original: str, candidate: str) -> bool:
    """Kiểm tra mã ứng viên chỉ thêm các dòng proof hint hợp lệ và không làm mất code gốc."""
    return len(_get_line_violations(original, candidate)) == 0


def _ask_model(model: str, source: str, feedback: str, max_tokens: int) -> tuple[str, dict]:
    """Gọi LLM phục vụ khôi phục proof hint với system prompt chặt chẽ và ví dụ few-shot."""
    system_prompt = (
        "You are an expert Dafny formal verification assistant.\n"
        "Your task is PROOF HINT RESTORATION.\n"
        "The input Dafny program has complete specifications (requires/ensures) but lacks loop invariants, "
        "termination metrics (decreases), or assertions needed by Dafny's verifier.\n\n"
        "STRICT CONSTRAINTS (Zero-Tolerance for Spec Tampering):\n"
        "1. DO NOT modify, delete, or rewrite ANY existing line of code, method signature, contract (requires, ensures), or predicate/function definition.\n"
        "2. ONLY INSERT valid proof annotations:\n"
        "   - 'invariant <condition>;' on loops\n"
        "   - 'decreases <expression>;' on loops or recursive functions\n"
        "   - 'assert <condition>;' or 'calc { ... }' or 'reveal <id>;' inside method/function bodies\n"
        "3. NEVER use 'assume', 'decreases *', '{:axiom}', or '{:verify false}'.\n"
        "4. Return the complete .dfy file enclosed in a single ```dafny ... ``` code block.\n\n"
        "FEW-SHOT EXAMPLE:\n"
        "// Given Input:\n"
        "method Sum(n: nat) returns (s: nat)\n"
        "  ensures s == n * (n + 1) / 2\n"
        "{\n"
        "  s := 0;\n"
        "  var i := 0;\n"
        "  while i < n\n"
        "  {\n"
        "    i := i + 1;\n"
        "    s := s + i;\n"
        "  }\n"
        "}\n\n"
        "// Correct Output (preserves all original lines verbatim, adds only invariants/decreases):\n"
        "```dafny\n"
        "method Sum(n: nat) returns (s: nat)\n"
        "  ensures s == n * (n + 1) / 2\n"
        "{\n"
        "  s := 0;\n"
        "  var i := 0;\n"
        "  while i < n\n"
        "    invariant 0 <= i <= n\n"
        "    invariant s == i * (i + 1) / 2\n"
        "    decreases n - i\n"
        "  {\n"
        "    i := i + 1;\n"
        "    s := s + i;\n"
        "  }\n"
        "}\n"
        "```"
    )

    user_content = f"Source to restore hints for:\n```dafny\n{source}\n```\n"
    if feedback.strip():
        user_content += (
            f"\nFeedback from previous attempt:\n{feedback[-4000:]}\n\n"
            "REMINDER: Preserve 100% of original lines verbatim; ONLY insert loop invariants/decreases/assertions!"
        )

    # Nếu dùng mô hình Gemini, ưu tiên gọi qua LLMAgent REST API trực tiếp tránh lỗi Vertex AI
    if "gemini" in model.lower():
        from agents.llm_agent import LLMAgent
        agent = LLMAgent(model_name=model, timeout_sec=120)
        try:
            code = agent._call_gemini_rest(system_prompt, user_content, timeout_sec=120) or ""
            if not code.strip():
                # Phản hồi rỗng do mô hình không sinh mã, KHÔNG mặc định quy chụp là quota fatal
                return "", {
                    "resolved_model": model, "method": "gemini_rest", "fatal_error": False,
                    "error_type": "empty_response", "message": "Mô hình trả về chuỗi rỗng"
                }
            return code, {"resolved_model": model, "method": "gemini_rest", "fatal_error": False}
        except Exception as exc:
            err_str = str(exc).lower()
            if any(k in err_str for k in ("429", "rate limit", "resource_exhausted")):
                err_type = "api_quota_or_rate_limit"
                is_fatal = True
            elif any(k in err_str for k in ("401", "403", "auth", "api_key", "permission_denied")):
                err_type = "api_auth_error"
                is_fatal = True
            elif any(k in err_str for k in ("credit", "billing", "quota")):
                err_type = "api_credit_exhausted"
                is_fatal = True
            else:
                err_type = "api_network_error"
                is_fatal = False
            return "", {"resolved_model": model, "method": "gemini_rest", "fatal_error": is_fatal,
                        "error_type": err_type, "message": str(exc)}

    import litellm
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=max_tokens,
            timeout=180,
        )
    except Exception as exc:
        err_str = str(exc).lower()
        if any(k in err_str for k in ("credit", "billing", "insufficient_quota")):
            err_type = "api_credit_exhausted"
            is_fatal = True
        elif any(k in err_str for k in ("rate limit", "429", "ratelimit", "tpm", "rpm")):
            err_type = "api_quota_or_rate_limit"
            is_fatal = True
        elif any(k in err_str for k in ("auth", "401", "403", "invalid_api_key", "authentication")):
            err_type = "api_auth_error"
            is_fatal = True
        elif "model_not_found" in err_str or "does not exist" in err_str:
            err_type = "api_model_not_found"
            is_fatal = True
        else:
            err_type = "api_call_error"
            is_fatal = False
        return "", {
            "resolved_model": model,
            "fatal_error": is_fatal,
            "error_type": err_type,
            "message": str(exc)
        }

    usage = getattr(response, "usage", None)
    try:
        cost = float(litellm.completion_cost(completion_response=response))
    except Exception:
        cost = None
    return response.choices[0].message.content or "", {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "cost_usd": cost,
        "resolved_model": getattr(response, "model", None),
        "fatal_error": False
    }


def _collect_provenance(model: str, max_attempts: int, workers: int, engine: DafnyEngine) -> dict:
    """Thu thập đầy đủ metadata môi trường và trạng thái git (dirty + diff hash) để đảm bảo tái lập."""
    repo_root = Path(__file__).resolve().parents[1]
    git_commit = "unknown"
    git_dirty = False
    git_diff_sha256 = None
    try:
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        status_out = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        git_dirty = bool(status_out)
        if git_dirty:
            diff_out = subprocess.check_output(
                ["git", "diff", "HEAD"], cwd=repo_root, text=True, stderr=subprocess.DEVNULL
            )
            git_diff_sha256 = hashlib.sha256(diff_out.encode("utf-8")).hexdigest()
    except Exception:
        pass

    dafny_ver = "unknown"
    try:
        res = subprocess.run([str(engine.dafny_bin), "--version"], capture_output=True, text=True, timeout=10)
        dafny_ver = (res.stdout or res.stderr).strip().splitlines()[0]
    except Exception:
        pass

    import platform
    return {
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git_commit,
        "git_dirty": git_dirty,
        "git_diff_sha256": git_diff_sha256,
        "dafny_version": dafny_ver,
        "dafny_bin": str(engine.dafny_bin),
        "model": model,
        "max_attempts": max_attempts,
        "workers": workers,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


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
    fatal_error = False

    for attempt_no in range(1, max_attempts + 1):
        raw, usage = _ask_model(model, original, feedback, max_tokens=8192)
        if usage.get("fatal_error"):
            attempt = {
                "number": attempt_no,
                "usage": usage,
                "status": usage.get("error_type", "api_fatal_error"),
                "hint_integrity_valid": False,
                "original_code_preserved": False,
                "strict_contract_issues": [usage.get("message", "API fatal error")],
            }
            attempts.append(attempt)
            fatal_error = True
            break

        if not raw or not raw.strip():
            status_val = usage.get("error_type", "empty_response")
            attempt = {
                "number": attempt_no,
                "usage": usage,
                "status": status_val,
                "hint_integrity_valid": False,
                "original_code_preserved": False,
                "strict_contract_issues": [usage.get("message", "Model returned empty response")],
            }
            attempts.append(attempt)
            feedback = "Model returned empty response. Please output valid Dafny code."
            continue

        candidate = _candidate(raw)
        integrity = SpecLocker.validate(original, candidate)
        line_safe = _only_hints_added(original, candidate)
        line_violations = _get_line_violations(original, candidate)
        escape_match = re.search(r"\bdecreases\s*\*|\{:\s*(?:axiom|verify\s+false|extern)\b", candidate, re.I)
        hint_safe = line_safe and not escape_match

        all_issues = list(integrity.issues) + line_violations
        if escape_match:
            all_issues.append("Contains forbidden verification bypass/escape (decreases * or {:axiom})")

        is_valid_candidate = hint_safe and integrity.valid
        attempt = {
            "number": attempt_no,
            "usage": usage,
            "hint_integrity_valid": is_valid_candidate,
            "original_code_preserved": line_safe,
            "strict_contract_issues": all_issues
        }

        if not is_valid_candidate:
            feedback = (
                "REJECTED CANDIDATE: Contract or source code tampering detected!\n"
                + "\n".join(f"- {issue}" for issue in all_issues[:10])
                + "\nYou MUST keep every original line unchanged and ONLY add invariants/decreases/assertions."
            )
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

    last_status = attempts[-1]["status"] if attempts else "not_run"
    return {
        "task_id": path.stem,
        "suite": "dafnybench20",
        "model": model,
        "status": last_status,
        "fatal_error": fatal_error,
        "attempts": attempts,
        "elapsed_seconds": time.monotonic() - start
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--task", help="One task ID or filename; default is all 20")
    parser.add_argument("--tasks", help="Comma-separated task IDs or keywords")
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

    engine = DafnyEngine(timeout_sec=30)
    if not engine.is_available():
        parser.error("Dafny CLI is not available")

    provenance = _collect_provenance(args.model, args.max_attempts, args.workers, engine)

    # Lọc bài toán linh hoạt theo ID, filename hoặc từ khóa
    target_tokens = []
    if args.task:
        target_tokens.append(args.task.strip())
    if args.tasks:
        target_tokens.extend([t.strip() for t in args.tasks.split(",") if t.strip()])

    if target_tokens:
        tasks = []
        for entry in index["tasks"]:
            e_id = entry["id"].lower()
            e_file = entry["file"].lower()
            if any(tok.lower() == e_id or tok.lower() == e_file or tok.lower() in e_id or tok.lower() in e_file for tok in target_tokens):
                tasks.append(entry)
    else:
        tasks = index["tasks"]

    if not tasks:
        parser.error(f"No matching tasks found for filter: {target_tokens}")

    print(f"Bắt đầu chạy {len(tasks)} bài toán DafnyBench20 với mô hình: {args.model}...", flush=True)

    suite_aborted = False
    abort_reason = ""

    def stop_check() -> bool:
        return suite_aborted

    def worker_wrapper(entry: dict) -> dict:
        nonlocal suite_aborted, abort_reason
        if suite_aborted:
            return {
                "task_id": entry["file"],
                "suite": "dafnybench20",
                "model": args.model,
                "status": "aborted_due_to_api_error",
                "fatal_error": True,
                "attempts": [],
                "elapsed_seconds": 0.0
            }
        res = run_one(suite / entry["file"], entry["hint_sha256"], args.model, args.max_attempts)
        if res.get("fatal_error"):
            suite_aborted = True
            abort_reason = (
                f"Task {res['task_id']} gặp lỗi API Fatal ({res['status']}). "
                "Đã ngừng xếp lịch task mới; các worker đang chạy song song được phép hoàn tất lượt hiện tại trước khi suite dừng hẳn."
            )
        return res

    completed = iter_completed(
        tasks,
        worker_wrapper,
        workers=args.workers,
        stop_requested=stop_check,
    )
    results_by_index = {}
    for idx, _, result in completed:
        results_by_index[idx] = result
        print(f"[dafnybench {len(results_by_index)}/{len(tasks)}] "
              f"{result['task_id']}: {result['status']} ({result['elapsed_seconds']:.2f}s)", flush=True)

    results = [results_by_index[idx] for idx in sorted(results_by_index)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_payload = {
        "suite": "dafnybench20",
        "provenance": provenance,
        "suite_aborted": suite_aborted,
        "abort_reason": abort_reason if suite_aborted else None,
        "total_tasks_scheduled": len(tasks),
        "total_tasks_evaluated": len(results),
        "results": results
    }
    args.output.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if suite_aborted:
        print(f"\n[DỪNG SỚM TOÀN SUITE]: {abort_reason}")

    passed_count = sum(x["status"] == "passed" for x in results)
    invalid_count = sum(x["status"] == "invalid_candidate" for x in results)
    fatal_count = sum(1 for x in results if x.get("fatal_error"))
    print(f"Hoàn thành {len(results)}/{len(tasks)} bài toán; Verified: {passed_count} | Invalid: {invalid_count} | Fatal API: {fatal_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
