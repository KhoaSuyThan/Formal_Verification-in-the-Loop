"""Regression checks for bounded, independent benchmark execution."""

import threading
import time
import unittest
import csv
import sys
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from core.batch_execution import iter_completed
from core import token_tracker


class TestBatchExecution(unittest.TestCase):
    def test_parallel_cases_keep_ids_and_bound_active_workers(self):
        active = 0
        peak = 0
        lock = threading.Lock()

        def worker(value):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.025)
            with lock:
                active -= 1
            return value * value

        completed = list(iter_completed(range(8), worker, workers=3))
        self.assertEqual(sorted(completed), [(i, i, i * i) for i in range(8)])
        self.assertTrue(1 < peak <= 3)

    def test_serial_and_stop_behavior(self):
        self.assertEqual(list(iter_completed([1, 2, 3], lambda value: value + 1)), [
            (0, 1, 2), (1, 2, 3), (2, 3, 4),
        ])
        called = []
        stop = threading.Event()

        def worker(value):
            called.append(value)
            stop.set()
            return value

        completed = list(iter_completed(range(8), worker, workers=2, stop_requested=stop.is_set))
        self.assertLessEqual(len(called), 2)
        self.assertEqual(len(completed), len(called))
        with self.assertRaises(ValueError):
            list(iter_completed([1], lambda value: value, workers=0))

    def test_worker_error_is_not_silently_counted(self):
        def worker(value):
            if value == 2:
                raise RuntimeError("case failed")
            return value

        with self.assertRaisesRegex(RuntimeError, "case failed"):
            list(iter_completed([1, 2, 3], worker, workers=2))

    def test_token_totals_are_preserved_under_threads(self):
        with TemporaryDirectory() as directory:
            gemini_path = str(Path(directory) / "gemini.json")
            groq_path = str(Path(directory) / "groq.json")
            with patch.object(token_tracker, "TRACKER_FILE", gemini_path), patch.object(
                token_tracker, "GROQ_TRACKER_FILE", groq_path
            ):
                with ThreadPoolExecutor(max_workers=8) as executor:
                    list(executor.map(lambda _: token_tracker.record_gemini_tokens(2, 3, 5), range(40)))
                    list(executor.map(lambda _: token_tracker.record_groq_tokens(1, 4, 5), range(40)))
                gemini = token_tracker.get_gemini_token_usage()
                groq = token_tracker.get_groq_token_usage()
                self.assertEqual((gemini["total_requests"], gemini["total_tokens"]), (40, 200))
                self.assertEqual((groq["total_requests"], groq["total_tokens"]), (40, 200))

    def test_cli_benchmark_keeps_all_case_rows_in_input_order(self):
        from core.pipeline_controller import PipelineResult
        from experiments import run_benchmark

        class FakeAgent:
            def __init__(self, **kwargs):
                pass

        class FakeEngine:
            def __init__(self, **kwargs):
                pass

            def is_available(self):
                return True

        class FakeController:
            def __init__(self, **kwargs):
                pass

            def run_task(self, raw_spec, task_name):
                time.sleep(0.02 if task_name == "a" else 0.005)
                return PipelineResult(task_name, True, 1, raw_spec)

        with TemporaryDirectory() as directory:
            root = Path(directory)
            cases = root / "data" / "benchmarks" / "sample"
            cases.mkdir(parents=True)
            for name in ("a", "b", "c"):
                (cases / f"{name}.dfy").write_text("method Foo() {}", encoding="utf-8")
            argv = ["run_benchmark", "--benchmark", "sample", "--model", "fake", "--workers", "2",
                    "--config", "absent.yaml"]
            original_cwd = Path.cwd()
            try:
                import os
                os.chdir(root)
                with patch.object(sys, "argv", argv), patch.object(run_benchmark, "LLMAgent", FakeAgent), patch.object(
                    run_benchmark, "DafnyEngine", FakeEngine
                ), patch.object(run_benchmark, "PipelineController", FakeController):
                    run_benchmark.main()
            finally:
                os.chdir(original_cwd)
            csv_file = next((root / "artifacts" / "results").glob("benchmark_sample_*.csv"))
            with csv_file.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["task_name"] for row in rows], ["a", "b", "c"])
            self.assertTrue(all(row["workers"] == "2" for row in rows))


if __name__ == "__main__":
    unittest.main()
