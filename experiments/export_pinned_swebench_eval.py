"""Export the pinned 30-row evaluator dataset, including held-out test patches.

The output must stay private to the evaluator and must never enter an agent
prompt or a tracked benchmark manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from pathlib import Path

from experiments.import_swebench_subset import DATASET, REVISION, SELECTION


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/private/swebench_verified_pinned30.jsonl"))
    args = parser.parse_args()
    found = {}
    for offset in range(0, 500, 100):
        query = urllib.parse.urlencode({"dataset": DATASET, "revision": REVISION,
                                        "config": "default", "split": "test", "offset": offset, "length": 100})
        with urllib.request.urlopen("https://datasets-server.huggingface.co/rows?" + query, timeout=60) as stream:
            rows = json.load(stream)["rows"]
        for entry in rows:
            row = entry["row"]
            if row["instance_id"] in SELECTION:
                found[row["instance_id"]] = row
    if set(found) != set(SELECTION):
        raise RuntimeError(f"Pinned dataset missing: {sorted(set(SELECTION) - set(found))}")
    manifest_dir = Path(__file__).resolve().parents[1] / "data/benchmarks/python_projects"
    for task_id, row in found.items():
        manifest = json.loads((manifest_dir / f"{task_id}.json").read_text(encoding="utf-8"))
        if row["base_commit"] != manifest["repo"]["base_commit"] or row["problem_statement"] != manifest["issue"]:
            raise RuntimeError(f"Pinned evaluator row does not match manifest: {task_id}")
    payload = "".join(json.dumps(found[task_id], ensure_ascii=False) + "\n" for task_id in sorted(found))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    digest = hashlib.sha256(payload.encode()).hexdigest()
    metadata = {"dataset": DATASET, "revision": REVISION, "rows": len(found), "sha256": digest,
                "contains_hidden_tests_and_gold_patches": True}
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(found)} evaluator rows; sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
