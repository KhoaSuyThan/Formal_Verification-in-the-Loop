"""Import 20 pinned DafnyBench hint-restoration tasks and validate references."""

from __future__ import annotations

import hashlib
import difflib
import json
import subprocess
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


COMMIT = "0cd28feed9cd0179b07fdb9d002f8c39063658e4"
KEYS = [
    "CS494-final-project_tmp_tmp7nof55uq_bubblesort_no_hints.dfy",
    "Dafny-Exercises_tmp_tmpjm75muf__Session3Exercises_ExerciseMaximum_no_hints.dfy",
    "Dafny-Exercises_tmp_tmpjm75muf__Session9Exercises_ExerciseSeqMaxSum_no_hints.dfy",
    "DafnyProjects_tmp_tmp2acw_s4s_RawSort_no_hints.dfy",
    "DafnyProjects_tmp_tmp2acw_s4s_partitionOddEven_no_hints.dfy",
    "Dafny_tmp_tmp0wu8wmfr_Heimaverkefni 2_BinarySearchDec_no_hints.dfy",
    "Final-Project-Dafny_tmp_tmpmcywuqox_Attempts_Insertion_Sorted_Standard_no_hints.dfy",
    "HATRA-2022-Paper_tmp_tmp5texxy8l_copilot_verification_Sort Array_sort_array_no_hints.dfy",
    "Program-Verification-Dataset_tmp_tmpgbdrlnu__Dafny_advanced examples_MatrixMultiplication_no_hints.dfy",
    "Program-Verification-Dataset_tmp_tmpgbdrlnu__Dafny_verified algorithms_lol_sort_no_hints.dfy",
    "Software-Verification_tmp_tmpv4ueky2d_Non-overlapping Intervals_non_overlapping_intervals_no_hints.dfy",
    "dafl_tmp_tmp_r3_8w3y_dafny_examples_uiowa_binary-search_no_hints.dfy",
    "Dafny_Verify_tmp_tmphq7j0row_dataset_detailed_examples_SelectionSort_no_hints.dfy",
    "formal_verication_dafny_tmp_tmpwgl2qz28_Challenges_ex1_no_hints.dfy",
    "Dafny-Exercises_tmp_tmpjm75muf__Session2Exercises_ExerciseFibonacci_no_hints.dfy",
    "dafl_tmp_tmp_r3_8w3y_dafny_examples_uiowa_modifying-arrays_no_hints.dfy",
    "dafny-language-server_tmp_tmpkir0kenl_Test_dafny2_SegmentSum_no_hints.dfy",
    "AssertivePrograming_tmp_tmpwf43uz0e_MergeSort_no_hints.dfy",
    "Program-Verification-Dataset_tmp_tmpgbdrlnu__Dafny_algorithms and leetcode_leetcode_validAnagram_no_hints.dfy",
    "cs245-verification_tmp_tmp0h_nxhqp_power_no_hints.dfy",
]


def _download(path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/sun-wendy/DafnyBench/{COMMIT}/" + urllib.parse.quote(path)
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def _verify(source: bytes) -> bool:
    with tempfile.TemporaryDirectory(prefix="dafnybench-import-") as tmp:
        path = Path(tmp) / "task.dfy"
        path.write_bytes(source)
        result = subprocess.run(["dafny", "verify", "--allow-warnings", "--verification-time-limit", "20", str(path)],
                                text=True, capture_output=True, timeout=45)
        return result.returncode == 0 and "0 errors" in result.stdout and "time out" not in result.stdout.lower()


def _audit_clean(source: bytes) -> bool:
    with tempfile.TemporaryDirectory(prefix="dafnybench-audit-") as tmp:
        path = Path(tmp) / "task.dfy"
        path.write_bytes(source)
        result = subprocess.run(["dafny", "audit", str(path)], text=True, capture_output=True, timeout=45)
        match = re.search(r"Dafny auditor completed with\s+(\d+)\s+findings", result.stdout + result.stderr, re.I)
        return result.returncode == 0 and match is not None and int(match.group(1)) == 0


def _hint_restorable(hint: bytes, gold: bytes) -> bool:
    source = [line.strip() for line in hint.decode().splitlines() if line.strip()]
    target = [line.strip() for line in gold.decode().splitlines() if line.strip()]
    for tag, _, _, start, end in difflib.SequenceMatcher(None, source, target, autojunk=False).get_opcodes():
        if tag not in {"equal", "insert"}:
            return False
        if tag == "insert" and any(not line.startswith(("invariant ", "decreases ", "assert ", "reveal ")) for line in target[start:end]):
            return False
    return True


def main() -> None:
    tree_url = "https://api.github.com/repos/sun-wendy/DafnyBench/git/trees/" + COMMIT + "?recursive=1"
    with urllib.request.urlopen(urllib.request.Request(tree_url, headers={"User-Agent": "FVIL-importer"}), timeout=60) as response:
        paths = {entry["path"] for entry in json.load(response)["tree"]}
    out = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "dafnybench20"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for filename in KEYS:
        hint_path = "DafnyBench/dataset/hints_removed/" + filename
        gold_path = "DafnyBench/dataset/ground_truth/" + filename.replace("_no_hints.dfy", ".dfy")
        if hint_path not in paths or gold_path not in paths:
            raise RuntimeError(f"Upstream task pair missing: {filename}")
        hint = _download(hint_path)
        gold = _download(gold_path)
        if not _verify(gold):
            raise RuntimeError(f"Gold program does not verify with installed Dafny: {filename}")
        if not _audit_clean(gold) or not _hint_restorable(hint, gold):
            raise RuntimeError(f"Gold program is not audit-clean/restorable by allowed hints: {filename}")
        if _verify(hint):
            raise RuntimeError(f"Hints-removed program already verifies: {filename}")
        (out / filename).write_bytes(hint)
        records.append({"id": filename[:-4], "file": filename, "hint_sha256": hashlib.sha256(hint).hexdigest(),
                        "gold_sha256": hashlib.sha256(gold).hexdigest(), "upstream_hint_path": hint_path,
                        "upstream_gold_path": gold_path})
    index = {"source": "https://github.com/sun-wendy/DafnyBench", "commit": COMMIT,
             "task_type": "restore_proof_hints", "tasks": records}
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported and checked {len(records)} DafnyBench tasks")


if __name__ == "__main__":
    main()
