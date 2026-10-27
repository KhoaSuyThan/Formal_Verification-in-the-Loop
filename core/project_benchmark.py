"""Isolated-checkout evaluation for multi-file Python repair tasks.

The Python test outcome and Dafny outcome remain separate evidence fields.
"""

from __future__ import annotations

import ast
import json
import hashlib
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from agents.patch_agent import PatchReply
from core.project_context import select_context
from core.project_formal import verify_project


_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIFF_PATH = re.compile(r"^diff --git a/(.+) b/(.+)$", re.M)


class PatchAgent(Protocol):
    model: str

    def generate_patch(self, prompt: str) -> PatchReply: ...


@dataclass(frozen=True)
class ProjectTask:
    id: str
    repo_url: str
    base_commit: str
    issue: str
    category: str
    allowed_paths: tuple[str, ...] = ()
    setup: tuple[tuple[str, ...], ...] = ()
    public_tests: tuple[tuple[str, ...], ...] = ()
    hidden_tests: tuple[tuple[str, ...], ...] = ()
    formal_files: tuple[str, ...] = ()
    protected_files: tuple[str, ...] = ()
    context_budget_chars: int = 24000
    backend: str = "local"
    source_metadata: dict[str, Any] = field(default_factory=dict)
    formal_review_status: str = "not_reviewed"

    @classmethod
    def load(cls, path: Path) -> "ProjectTask":
        data = json.loads(path.read_text(encoding="utf-8"))
        repo = data["repo"]
        task = cls(
            id=data["id"], repo_url=repo["url"], base_commit=repo["base_commit"],
            issue=data["issue"], category=data["category"],
            allowed_paths=tuple(data.get("allowed_paths", [])),
            setup=tuple(tuple(c) for c in data.get("setup", [])),
            public_tests=tuple(tuple(c) for c in data.get("public_tests", [])),
            hidden_tests=tuple(tuple(c) for c in data.get("hidden_tests", [])),
            formal_files=tuple(data.get("formal_files", [])),
            protected_files=tuple(data.get("protected_files", [])),
            context_budget_chars=int(data.get("context_budget_chars", 24000)),
            backend=data.get("backend", "local"),
            source_metadata=data.get("source", {}),
            formal_review_status=data.get("formal_review_status", "not_reviewed"),
        )
        if not task.id or not task.issue or not _COMMIT.fullmatch(task.base_commit):
            raise ValueError(f"Invalid task ID, issue, or pinned commit: {path}")
        if task.backend not in {"local", "swebench"}:
            raise ValueError(f"Unsupported backend: {task.backend}")
        return task


@dataclass
class CommandResult:
    status: str
    command: list[str] = field(default_factory=list)
    exit_code: int | None = None
    output: str = ""
    seconds: float = 0.0


def _run(command: list[str], cwd: Path, timeout_sec: int) -> CommandResult:
    start = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout_sec)
        return CommandResult("passed" if proc.returncode == 0 else "failed", command, proc.returncode,
                             ((proc.stdout or "") + (proc.stderr or ""))[-10000:], time.monotonic() - start)
    except subprocess.TimeoutExpired as exc:
        return CommandResult("timeout", command, None, str(exc), time.monotonic() - start)


def _clone(task: ProjectTask, destination: Path) -> None:
    source = task.repo_url
    command = ["git", "clone", "--quiet", "--no-checkout"]
    if source.startswith("https://"):
        command += ["--filter=blob:none"]
    else:
        command += ["--no-hardlinks"]
    result = _run(command + [source, str(destination)], destination.parent, 600)
    if result.status != "passed":
        raise RuntimeError(f"Could not clone {source}: {result.output}")
    checkout = _run(["git", "checkout", "--quiet", "--detach", task.base_commit], destination, 300)
    if checkout.status != "passed":
        raise RuntimeError(f"Could not checkout {task.base_commit}: {checkout.output}")


def _patch_paths(patch: str) -> list[str]:
    paths = []
    for old, new in _DIFF_PATH.findall(patch):
        if old != new:
            raise ValueError("Renames are not accepted by the benchmark runner")
        path = Path(new)
        if path.is_absolute() or ".." in path.parts or path.parts[0].startswith("."):
            raise ValueError(f"Unsafe patch path: {new}")
        paths.append(new)
    if not paths:
        raise ValueError("Response does not contain a git diff")
    return paths


def _apply_patch(repo: Path, patch: str, task: ProjectTask) -> list[str]:
    paths = _patch_paths(patch)
    for path in paths:
        if task.allowed_paths and not any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in task.allowed_paths):
            raise ValueError(f"Patch path is outside allowed_paths: {path}")
        if path in task.protected_files or path.endswith(".dfy"):
            raise ValueError(f"Agent may not edit protected formal source: {path}")
        if task.backend == "swebench" and (not path.endswith(".py") or Path(path).name.startswith("test_")
                                             or "tests" in Path(path).parts):
            raise ValueError(f"SWE-bench pilot accepts source Python patches only: {path}")
        if any(part in {".git", ".venv", "__pycache__"} for part in Path(path).parts):
            raise ValueError(f"Unsafe patch path: {path}")
    check = subprocess.run(["git", "apply", "--check", "-"], cwd=repo, input=patch, text=True, capture_output=True)
    if check.returncode:
        raise ValueError(f"Patch does not apply: {check.stderr[-3000:]}")
    applied = subprocess.run(["git", "apply", "-"], cwd=repo, input=patch, text=True, capture_output=True)
    if applied.returncode:
        raise ValueError(f"Patch application failed: {applied.stderr[-3000:]}")
    for path in paths:
        if (repo / path).exists():
            subprocess.run(["git", "add", "-N", "--", path], cwd=repo, capture_output=True)
    return paths


def _commands(commands: tuple[tuple[str, ...], ...], cwd: Path, python: Path, timeout: int) -> list[CommandResult]:
    results = []
    for command in commands:
        argv = [piece.replace("{python}", str(python)).replace("{repo}", str(cwd)) for piece in command]
        outcome = _run(argv, cwd, timeout)
        results.append(outcome)
        if outcome.status != "passed":
            break
    return results


def _syntax_check(repo: Path, paths: list[str]) -> CommandResult:
    start = time.monotonic()
    try:
        for relative in paths:
            if relative.endswith(".py") and (repo / relative).exists():
                ast.parse((repo / relative).read_text(encoding="utf-8"), filename=relative)
    except (SyntaxError, UnicodeError) as exc:
        return CommandResult("failed", ["ast.parse", *paths], None, str(exc), time.monotonic() - start)
    return CommandResult("passed", ["ast.parse", *paths], 0, "Python syntax parsed", time.monotonic() - start)


def evaluate_task(task: ProjectTask, agent: PatchAgent, *, max_attempts: int = 3,
                  command_timeout_sec: int = 120, use_feedback: bool = True) -> dict[str, Any]:
    """Generate a patch in a disposable checkout and keep evidence by validator."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="fvil-project-") as scratch:
        repo = Path(scratch) / "repo"
        _clone(task, repo)
        python = Path(scratch) / "venv" / "bin" / "python"
        setup: list[CommandResult] = []
        if task.backend == "local":
            setup = [_run([sys.executable, "-m", "venv", str(python.parent.parent)], repo, command_timeout_sec)]
            if setup[0].status == "passed":
                setup += _commands(task.setup, repo, python, command_timeout_sec)
        protected_sources = {path: (repo / path).read_text(encoding="utf-8") for path in task.protected_files}
        report: dict[str, Any] = {
            "schema_version": 1, "task_id": task.id, "category": task.category,
            "backend": task.backend, "repo_url": task.repo_url, "base_commit": task.base_commit,
            "source": task.source_metadata, "formal_review_status": task.formal_review_status,
            "model": agent.model, "max_attempts": max_attempts,
            "command_timeout_sec": command_timeout_sec, "context_budget_chars": task.context_budget_chars,
            "python_version": sys.version.split()[0],
            "setup": [asdict(item) for item in setup], "attempts": [],
            "python_tests": {"status": "not_run"}, "dafny_verification": {"status": "not_applicable"},
            "spec_audit": {"status": "not_applicable"}, "final_patch": "",
        }
        if setup and setup[-1].status != "passed":
            report["failure_reason"] = "setup_failed"
            report["elapsed_seconds"] = time.monotonic() - start
            return report
        feedback = ""
        for index in range(1, max_attempts + 1):
            context = select_context(repo, task.issue, diagnostics=feedback,
                                     budget_chars=task.context_budget_chars, allowed_paths=task.allowed_paths)
            prompt = (f"Issue:\n{task.issue}\n\nRelevant repository files (bounded context):\n{context.text}\n"
                      f"\nAllowed source paths: {', '.join(task.allowed_paths) or 'repository source files'}\n"
                      "Return an incremental unified git diff relative to the current checkout.")
            if feedback and use_feedback:
                prompt += f"\nPrevious validation feedback:\n{feedback[-6000:]}"
            try:
                reply = agent.generate_patch(prompt)
            except Exception as exc:
                report["attempts"].append({"number": index, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                                           "context": context.evidence(), "patch_status": "model_error",
                                           "error": str(exc)[-1000:]})
                report["failure_reason"] = "model_error"
                break
            attempt: dict[str, Any] = {"number": index, "context": context.evidence(),
                                       "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                                       "prompt_tokens": reply.prompt_tokens,
                                       "completion_tokens": reply.completion_tokens,
                                       "cost_usd": reply.cost_usd,
                                       "resolved_model": reply.resolved_model}
            try:
                attempt["changed_paths"] = _apply_patch(repo, reply.patch, task)
            except ValueError as exc:
                attempt["patch_status"] = "failed"
                attempt["error"] = str(exc)
                report["attempts"].append(attempt)
                feedback = str(exc)
                continue
            attempt["patch_status"] = "applied"
            if task.backend == "local":
                public = _commands(task.public_tests, repo, python, command_timeout_sec)
                checks = public
                python_status = "passed" if public and all(x.status == "passed" for x in public) else (public[-1].status if public else "not_configured")
                report["python_tests"] = {"status": python_status,
                                          "public": [asdict(x) for x in public], "hidden": []}
            else:
                python_status = "pending_swebench_harness"
                report["python_tests"] = {"status": python_status, "reason": "Use official Docker harness on exported prediction"}
                syntax = _syntax_check(repo, attempt["changed_paths"])
                attempt["syntax_check"] = asdict(syntax)
            if task.formal_files and task.formal_review_status != "reviewed":
                raise ValueError(f"Formal files for {task.id} require human review before scoring")
            formal, audit = verify_project(repo, task.formal_files, protected_sources=protected_sources,
                                           timeout_sec=command_timeout_sec)
            report["dafny_verification"] = formal.to_dict()
            report["spec_audit"] = audit.to_dict()
            attempt["python_tests_status"] = python_status
            attempt["dafny_verification_status"] = formal.status
            attempt["spec_audit_status"] = audit.status
            report["attempts"].append(attempt)
            if task.backend == "swebench":
                if syntax.status == "passed" or not use_feedback:
                    break
                feedback = syntax.output
                continue
            if python_status == "passed" and formal.status in {"passed", "not_applicable"} and audit.status in {"passed", "not_applicable"}:
                break
            feedback = "\n".join(x.output for x in checks[-2:]) + "\n" + formal.output + "\n" + audit.output
            if not use_feedback:
                break
        diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=repo, text=True, capture_output=True)
        report["final_patch"] = diff.stdout if diff.returncode == 0 else ""
        if task.backend == "local" and task.hidden_tests and report["final_patch"]:
            public_status = report["python_tests"]["status"]
            if public_status in {"passed", "not_configured"}:
                hidden = _commands(task.hidden_tests, repo, python, command_timeout_sec)
                report["python_tests"]["hidden"] = [asdict(item) for item in hidden]
                report["python_tests"]["status"] = (
                    "passed" if hidden and all(item.status == "passed" for item in hidden)
                    else hidden[-1].status if hidden else "not_configured"
                )
        report["total_prompt_tokens"] = (sum(x.get("prompt_tokens") or 0 for x in report["attempts"])
                                         if any(x.get("prompt_tokens") is not None for x in report["attempts"]) else None)
        report["total_completion_tokens"] = (sum(x.get("completion_tokens") or 0 for x in report["attempts"])
                                             if any(x.get("completion_tokens") is not None for x in report["attempts"]) else None)
        report["total_cost_usd"] = (sum(x.get("cost_usd") or 0.0 for x in report["attempts"])
                                    if any(x.get("cost_usd") is not None for x in report["attempts"]) else None)
        report["elapsed_seconds"] = time.monotonic() - start
        return report
