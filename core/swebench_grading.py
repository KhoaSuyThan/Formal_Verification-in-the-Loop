"""Interpret the official SWE-bench run summary without conflating failures and errors."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def dataset_sha256(name_or_path: str) -> str | None:
    path = Path(name_or_path)
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def instance_status(summary: dict[str, Any], instance_id: str) -> str:
    """Return a result for one submitted instance from the harness ID lists."""
    if instance_id in summary.get("resolved_ids", []):
        return "passed"
    if instance_id in summary.get("unresolved_ids", []):
        return "failed"
    if instance_id in summary.get("empty_patch_ids", []):
        return "empty_patch"
    if instance_id in summary.get("error_ids", []):
        return "harness_error"
    if instance_id in summary.get("incomplete_ids", []):
        return "not_run"
    raise ValueError(f"SWE-bench summary has no verdict for {instance_id}")
