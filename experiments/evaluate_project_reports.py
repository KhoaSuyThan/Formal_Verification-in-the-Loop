"""Paired, evidence-separated metrics for baseline and framework runs."""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path


def _rate(items: list[dict], field: str) -> dict:
    eligible = [item for item in items if item[field]["status"] in {"passed", "failed"}]
    successes = sum(item[field]["status"] == "passed" for item in eligible)
    return {"passed": successes, "evaluated": len(eligible),
            "rate": successes / len(eligible) if eligible else None}


def _summary(rows: list[dict]) -> dict:
    feedback_attempts = [x for x in rows if x.get("mode") == "framework" and len(x["attempts"]) > 1]
    feedback_successes = sum(x["python_tests"]["status"] == "passed" for x in feedback_attempts)
    return {
        "tasks": len(rows),
        "python_tests": _rate(rows, "python_tests"),
        "dafny_verification": _rate(rows, "dafny_verification"),
        "spec_audit": _rate(rows, "spec_audit"),
        "python_outcomes": {status: sum(x["python_tests"]["status"] == status for x in rows)
                            for status in sorted({x["python_tests"]["status"] for x in rows})},
        "repair_after_feedback": {"passed": feedback_successes, "attempted": len(feedback_attempts),
                                  "rate": feedback_successes / len(feedback_attempts) if feedback_attempts else None},
        "timeouts": sum(x[field]["status"] == "timeout" for x in rows for field in ("python_tests", "dafny_verification", "spec_audit")),
        "mean_seconds": statistics.mean(x["elapsed_seconds"] for x in rows) if rows else None,
        "total_cost_usd_known": sum(x.get("total_cost_usd") or 0.0 for x in rows),
        "cost_coverage": sum(x.get("total_cost_usd") is not None for x in rows),
        "total_prompt_tokens_known": sum(x.get("total_prompt_tokens") or 0 for x in rows),
        "total_completion_tokens_known": sum(x.get("total_completion_tokens") or 0 for x in rows),
    }


def paired_report(reports: list[dict]) -> dict:
    by_key: dict[tuple[str, str], dict[str, dict]] = {}
    for row in reports:
        if row.get("schema_version") != 1 or row.get("mode") not in {"baseline", "framework"}:
            continue
        key = (row["task_id"], row["model"])
        if row["mode"] in by_key.setdefault(key, {}):
            raise ValueError(f"Duplicate mode for {key}: {row['mode']}")
        by_key[key][row["mode"]] = row
    pairs = [value for value in by_key.values() if set(value) == {"baseline", "framework"}]
    for pair in pairs:
        a, b = pair["baseline"], pair["framework"]
        if (a["base_commit"], a["backend"], a.get("command_timeout_sec"), a.get("context_budget_chars"),
            a.get("source"), a.get("max_attempts"), a.get("python_version"),
            a["python_tests"].get("dataset"), a["python_tests"].get("dataset_sha256")) != (
            b["base_commit"], b["backend"], b.get("command_timeout_sec"), b.get("context_budget_chars"),
            b.get("source"), b.get("max_attempts"), b.get("python_version"),
            b["python_tests"].get("dataset"), b["python_tests"].get("dataset_sha256")):
            raise ValueError(f"Mismatched environment for task {a['task_id']}")
    baseline = [x["baseline"] for x in pairs]
    framework = [x["framework"] for x in pairs]
    scored = [(int(b["python_tests"]["status"] == "passed"), int(a["python_tests"]["status"] == "passed"))
              for a, b in zip(baseline, framework)
              if a["python_tests"]["status"] in {"passed", "failed"} and b["python_tests"]["status"] in {"passed", "failed"}]
    delta = None
    interval = None
    if scored:
        delta = statistics.mean(b - a for b, a in scored)
        rng = random.Random(42)
        samples = sorted(statistics.mean(sample[0] - sample[1] for sample in (rng.choice(scored) for _ in scored)) for _ in range(2000))
        interval = [samples[49], samples[1949]]
    return {"paired_tasks": len(pairs), "unpaired": [list(key) for key, value in by_key.items() if len(value) != 2],
            "baseline": _summary(baseline), "framework": _summary(framework),
            "python_pass_delta": delta, "paired_bootstrap_95pct": interval,
            "note": "Python tests, Dafny verification and audit have separate denominators; no composite correctness score."}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for path in sorted(args.reports_dir.rglob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if row.get("schema_version") == 1:
            rows.append(row)
    result = paired_report(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
