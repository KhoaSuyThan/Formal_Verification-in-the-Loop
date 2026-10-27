"""Dafny project verification with an explicit, separate soundness audit."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from core.dafny_engine import DafnyEngine
from core.spec_locker import SpecLocker


@dataclass(frozen=True)
class FormalCheck:
    status: str
    command: tuple[str, ...]
    output: str
    return_code: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"path escapes checkout: {relative}")
    return path


def _run(command: Sequence[str], cwd: Path, timeout: int) -> FormalCheck:
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return FormalCheck("timeout", tuple(command), str(exc), None)
    output = (proc.stdout or "") + (proc.stderr or "")
    return FormalCheck("passed" if proc.returncode == 0 else "failed", tuple(command), output, proc.returncode)


def audit_has_findings(output: str) -> bool:
    """Prefer Dafny auditor's finding count over unrelated compiler warnings."""
    match = re.search(r"Dafny auditor completed with\s+(\d+)\s+findings", output, re.I)
    return int(match.group(1)) > 0 if match else "warning:" in output.lower()


def verify_project(
    root: Path,
    files: Sequence[str],
    *,
    protected_sources: dict[str, str] | None = None,
    timeout_sec: int = 60,
    engine: DafnyEngine | None = None,
) -> tuple[FormalCheck, FormalCheck]:
    """Return (verification, audit); never infer Python correctness from either."""
    root = root.resolve()
    if not files:
        skipped = FormalCheck("not_applicable", (), "No Dafny files attached to this task", None)
        return skipped, skipped
    engine = engine or DafnyEngine(timeout_sec=timeout_sec)
    if not engine.is_available():
        unavailable = FormalCheck("unavailable", (), "Dafny executable is unavailable", None)
        return unavailable, unavailable
    targets = [_inside(root, item) for item in files]
    if any(not target.is_file() for target in targets):
        missing = FormalCheck("failed", (), "Dafny project file missing", None)
        return missing, missing
    arguments = [str(path) for path in targets]
    verify = _run([str(engine.dafny_bin), "verify", "--verification-time-limit", str(timeout_sec), *arguments], root, timeout_sec + 15)
    if verify.status == "passed" and "0 errors" not in verify.output:
        verify = FormalCheck("failed", verify.command, verify.output, verify.return_code)
    audit = _run([str(engine.dafny_bin), "audit", *arguments], root, timeout_sec + 15)
    audit_issues: list[str] = []
    if audit_has_findings(audit.output):
        audit_issues.append("dafny_audit_warning")
    for relative, original in (protected_sources or {}).items():
        path = _inside(root, relative)
        if not path.is_file():
            audit_issues.append(f"protected_file_removed:{relative}")
            continue
        candidate = path.read_text(encoding="utf-8")
        spec_check = SpecLocker.validate(original, candidate)
        audit_issues.extend(f"{relative}:{issue}" for issue in spec_check.issues)
        # Whole-file protection is required for reviewer-owned specification files.
        if hashlib.sha256(original.encode()).digest() != hashlib.sha256(candidate.encode()).digest():
            audit_issues.append(f"protected_file_changed:{relative}")
    if audit_issues:
        audit = FormalCheck("failed", audit.command, audit.output + "\n" + "\n".join(audit_issues), audit.return_code)
    return verify, audit
