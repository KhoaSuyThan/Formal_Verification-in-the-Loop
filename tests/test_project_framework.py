"""No network/model calls: exercise the repository workflow with a fake agent."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import hashlib
from pathlib import Path

from agents.patch_agent import PatchReply
from core.dafny_engine import DafnyEngine
from core.project_benchmark import ProjectTask, evaluate_task
from core.project_context import select_context
from core.project_formal import verify_project
from core.spec_locker import SpecLocker
from core.swebench_grading import instance_status
from experiments.evaluate_project_reports import paired_report
from experiments.run_dafnybench20 import run_one


PATCH = """diff --git a/pkg/a.py b/pkg/a.py
--- a/pkg/a.py
+++ b/pkg/a.py
@@ -1,2 +1,2 @@
 def step(n):
-    return n + 1
+    return n + 2
diff --git a/pkg/b.py b/pkg/b.py
--- a/pkg/b.py
+++ b/pkg/b.py
@@ -1,4 +1,4 @@
 from pkg.a import step

 def total(n):
-    return step(n)
+    return step(n) + 1
"""


class FakeAgent:
    model = "fake/patch-agent"

    def generate_patch(self, prompt: str) -> PatchReply:
        assert "Relevant repository files" in prompt
        return PatchReply(PATCH, prompt_tokens=10, completion_tokens=20, cost_usd=0.0)


class ProjectFrameworkTests(unittest.TestCase):
    def test_multi_file_patch_and_separate_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "upstream"
            (repo / "pkg").mkdir(parents=True)
            (repo / "tests").mkdir()
            (repo / "pkg/__init__.py").write_text("", encoding="utf-8")
            (repo / "pkg/a.py").write_text("def step(n):\n    return n + 1\n", encoding="utf-8")
            (repo / "pkg/b.py").write_text("from pkg.a import step\n\ndef total(n):\n    return step(n)\n", encoding="utf-8")
            (repo / "tests/test_total.py").write_text(
                "import unittest\nfrom pkg.b import total\nclass TestTotal(unittest.TestCase):\n"
                "    def test_total(self):\n        self.assertEqual(total(2), 5)\n", encoding="utf-8")
            for command in (["git", "init", "-q"], ["git", "config", "user.email", "test@example.com"],
                            ["git", "config", "user.name", "Test"], ["git", "add", "."],
                            ["git", "commit", "-qm", "base"]):
                subprocess.run(command, cwd=repo, check=True)
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            manifest = Path(tmp) / "task.json"
            manifest.write_text(json.dumps({"id": "local-001", "category": "multi_module",
                                            "repo": {"url": str(repo), "base_commit": commit},
                                            "issue": "Repair pkg/a.py and pkg/b.py to make total(2) equal 5",
                                            "allowed_paths": ["pkg"],
                                            "public_tests": [["{python}", "-m", "unittest", "discover", "-s", "tests"]]}),
                                encoding="utf-8")
            task = ProjectTask.load(manifest)
            report = evaluate_task(task, FakeAgent(), max_attempts=1)
            self.assertEqual(report["python_tests"]["status"], "passed")
            self.assertEqual(report["dafny_verification"]["status"], "not_applicable")
            self.assertEqual(report["spec_audit"]["status"], "not_applicable")
            self.assertEqual(report["final_patch"].count("diff --git"), 2)
            self.assertTrue(report["attempts"][0]["context"])
            self.assertEqual(report["total_prompt_tokens"], 10)
            with_hidden = {**json.loads(manifest.read_text(encoding="utf-8")),
                           "hidden_tests": [["{python}", "-c", "assert False, 'hidden oracle'"]]}
            manifest.write_text(json.dumps(with_hidden), encoding="utf-8")
            hidden_report = evaluate_task(ProjectTask.load(manifest), FakeAgent(), max_attempts=3)
            self.assertEqual(hidden_report["python_tests"]["status"], "failed")
            self.assertEqual(len(hidden_report["attempts"]), 1)
            self.assertTrue(hidden_report["python_tests"]["hidden"])

    def test_context_budget_and_contract_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "logic.py").write_text("def search_target(items):\n    return items[0]\n" * 200, encoding="utf-8")
            context = select_context(repo, "search_target error in logic.py", budget_chars=600)
            self.assertLessEqual(len(context.text), 600)
            self.assertTrue(context.files[0].truncated)
        original = "method M(x: int) returns (y: int)\n  requires x > 0\n  ensures y > 0\n{}"
        changed = "method M(x: int) returns (y: int)\n  requires x > 10\n  ensures y > 0\n{ y := 1; }"
        self.assertFalse(SpecLocker.validate(original, changed).valid)

    def test_paired_metrics_do_not_merge_validators(self):
        base = {"schema_version": 1, "task_id": "t", "model": "m", "mode": "baseline", "base_commit": "a" * 40,
                "backend": "local", "python_tests": {"status": "failed"},
                "dafny_verification": {"status": "not_applicable"}, "spec_audit": {"status": "not_applicable"},
                "attempts": [{}], "elapsed_seconds": 1.0}
        improved = {**base, "mode": "framework", "python_tests": {"status": "passed"},
                    "attempts": [{}, {}], "elapsed_seconds": 2.0}
        result = paired_report([base, improved])
        self.assertEqual(result["paired_tasks"], 1)
        self.assertEqual(result["python_pass_delta"], 1.0)
        self.assertIsNone(result["framework"]["dafny_verification"]["rate"])

    def test_swebench_summary_uses_id_lists_and_keeps_errors_separate(self):
        summary = {"resolved_instances": 1, "resolved_ids": ["good"],
                   "unresolved_ids": ["wrong"], "empty_patch_ids": ["empty"],
                   "error_ids": ["broken"], "incomplete_ids": ["missing"]}
        self.assertEqual(instance_status(summary, "good"), "passed")
        self.assertEqual(instance_status(summary, "wrong"), "failed")
        self.assertEqual(instance_status(summary, "empty"), "empty_patch")
        self.assertEqual(instance_status(summary, "broken"), "harness_error")
        self.assertEqual(instance_status(summary, "missing"), "not_run")
        with self.assertRaises(ValueError):
            instance_status(summary, "unknown")

    def test_multi_file_dafny_project_and_audit(self):
        if not DafnyEngine().is_available():
            self.skipTest("Dafny is not installed")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "dfyconfig.toml").write_text('includes = ["src/**/*.dfy"]\n', encoding="utf-8")
            (root / "src/a.dfy").write_text("method A(x: int) returns (y: int)\n  ensures y > x\n{ y := x + 1; }\n", encoding="utf-8")
            (root / "src/b.dfy").write_text("method B(x: int) returns (y: int)\n  ensures y >= x\n{ y := x; }\n", encoding="utf-8")
            verification, audit = verify_project(root, ["dfyconfig.toml"], timeout_sec=20)
            self.assertEqual(verification.status, "passed", verification.output)
            self.assertEqual(audit.status, "passed", audit.output)

    def test_dafny_hint_runner_preserves_program(self):
        if not DafnyEngine().is_available():
            self.skipTest("Dafny is not installed")
        original = ("method Count(n: nat) returns (s: nat)\n  ensures s == n\n"
                    "{\n  var i := 0;\n  s := 0;\n  while i < n\n  {\n"
                    "    s := s + 1;\n    i := i + 1;\n  }\n}\n")
        candidate = original.replace("  while i < n\n  {", "  while i < n\n    invariant i <= n\n    invariant s == i\n    decreases n - i\n  {")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "count.dfy"
            source.write_text(original, encoding="utf-8")
            with patch("experiments.run_dafnybench20._ask_model", return_value=(f"```dafny\n{candidate}```", {})):
                result = run_one(source, hashlib.sha256(original.encode()).hexdigest(), "fake", 1)
        self.assertEqual(result["status"], "passed", result["attempts"])

    def test_pinned_benchmark_manifests(self):
        root = Path(__file__).resolve().parents[1] / "data/benchmarks"
        python_suite = root / "python_projects"
        index = json.loads((python_suite / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["total_tasks"], 30)
        self.assertEqual(sorted(index["categories"].values()), [10, 10, 10])
        self.assertEqual(len({ProjectTask.load(python_suite / f"{item}.json").base_commit for item in index["tasks"]}), 30)
        review = json.loads((python_suite / "formal_candidates.json").read_text(encoding="utf-8"))
        self.assertEqual(len(review["tasks"]), 10)
        self.assertTrue({item["id"] for item in review["tasks"]}.issubset(index["tasks"]))
        draft = (python_suite / review["draft_file"]).read_text(encoding="utf-8")
        self.assertTrue(all(f"module {item['draft_module']}" in draft for item in review["tasks"]))
        self.assertTrue(all(ProjectTask.load(python_suite / f"{item['id']}.json").formal_review_status ==
                            "draft_pending_human_review" for item in review["tasks"]))
        dafny_index = json.loads((root / "dafnybench20/index.json").read_text(encoding="utf-8"))
        self.assertEqual(len(dafny_index["tasks"]), 20)
        self.assertEqual(len(json.loads((root / "spec_traps/cases.json").read_text(encoding="utf-8"))["cases"]), 10)


if __name__ == "__main__":
    unittest.main()
