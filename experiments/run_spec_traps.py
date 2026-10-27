"""Report contract tampering separately from weak but formally valid contracts."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from core.dafny_engine import DafnyEngine
from core.project_formal import audit_has_findings
from core.spec_locker import SpecLocker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", help="Run one trap ID; default is all 10")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = json.loads((root / "data/benchmarks/spec_traps/cases.json").read_text(encoding="utf-8"))
    cases = [case for case in suite["cases"] if not args.case or case["id"] == args.case]
    if not cases:
        parser.error(f"No such case: {args.case}")
    engine = DafnyEngine(timeout_sec=20)
    if not engine.is_available():
        parser.error("Dafny is unavailable")
    results = []
    for case in cases:
        original = (root / case["original_file"]).read_text(encoding="utf-8") if "original_file" in case else case["original"]
        candidate = case["candidate"]
        integrity = SpecLocker.validate(original, candidate)
        verified = engine.verify(candidate, extract_counterexample=False)
        with tempfile.TemporaryDirectory(prefix="fvil-trap-") as tmp:
            path = Path(tmp) / "trap.dfy"
            path.write_text(candidate, encoding="utf-8")
            audit = subprocess.run([str(engine.dafny_bin), "audit", str(path)], text=True,
                                   capture_output=True, timeout=30)
        audit_output = audit.stdout + audit.stderr
        audit_clean = audit.returncode == 0 and not audit_has_findings(audit_output)
        witness_status = "not_applicable"
        witness_output = ""
        if case.get("witness"):
            with tempfile.TemporaryDirectory(prefix="fvil-witness-") as tmp:
                path = Path(tmp) / "witness.dfy"
                path.write_text(candidate + "\n" + case["witness"], encoding="utf-8")
                try:
                    witness = subprocess.run([str(engine.dafny_bin), "run", str(path)], text=True,
                                             capture_output=True, timeout=45)
                    witness_output = (witness.stdout + witness.stderr)[-1000:]
                    witness_status = ("counterexample_observed" if witness.returncode != 0
                                      and "[Program halted]" in witness_output else
                                      "not_detected" if witness.returncode == 0 else "execution_error")
                except subprocess.TimeoutExpired:
                    witness_status = "timeout"
        results.append({
            "id": case["id"], "kind": case["kind"], "contract_gate": "passed" if integrity.valid else "rejected",
            "contract_issues": list(integrity.issues), "dafny_verification": "passed" if verified.is_verified else "failed",
            "dafny_output": verified.output[-1000:], "dafny_audit": "passed" if audit_clean else "failed",
            "audit_output": audit_output[-1000:],
            "semantic_review": "required" if case["kind"] == "weak_spec" else "not_applicable",
            "semantic_witness": witness_status, "witness_output": witness_output,
            "reason": case.get("reason", ""),
        })
    report = {"suite": "spec_traps_v1", "results": results,
              "tamper_or_bypass_rejected": sum(x["contract_gate"] == "rejected" for x in results if x["kind"] != "weak_spec"),
              "weak_specs_requiring_review": sum(x["kind"] == "weak_spec" for x in results),
              "weak_spec_counterexamples": sum(x["semantic_witness"] == "counterexample_observed" for x in results)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
