"""Materialize the fixed 30-task SWE-bench Verified pilot without gold patches.

Source rows are pinned to a dataset revision. Running this script is optional:
the generated manifests are checked in and usable without Hugging Face access.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path


DATASET = "princeton-nlp/SWE-bench_Verified"
REVISION = "c104f840cc67f8b6eec6f759ebc8b2693d585d4a"
SELECTION = {
    "django__django-10554": "data_logic", "django__django-11138": "boundary",
    "django__django-11400": "data_logic", "django__django-11885": "data_logic",
    "django__django-12325": "boundary", "django__django-13121": "multi_module",
    "django__django-13344": "multi_module", "django__django-14011": "boundary",
    "django__django-14631": "multi_module", "django__django-15629": "multi_module",
    "pydata__xarray-2905": "boundary", "pydata__xarray-3095": "data_logic",
    "pydata__xarray-3151": "boundary", "pydata__xarray-3305": "data_logic",
    "pydata__xarray-3677": "data_logic", "pydata__xarray-3993": "multi_module",
    "pydata__xarray-4687": "data_logic", "pydata__xarray-6938": "data_logic",
    "pydata__xarray-6992": "boundary", "pydata__xarray-7393": "boundary",
    "sphinx-doc__sphinx-10673": "boundary", "sphinx-doc__sphinx-11510": "boundary",
    "sphinx-doc__sphinx-7462": "boundary", "sphinx-doc__sphinx-7590": "multi_module",
    "sphinx-doc__sphinx-8120": "multi_module", "sphinx-doc__sphinx-8548": "multi_module",
    "sphinx-doc__sphinx-8551": "data_logic", "sphinx-doc__sphinx-8593": "multi_module",
    "sphinx-doc__sphinx-9229": "data_logic", "sphinx-doc__sphinx-9461": "multi_module",
}


def main() -> None:
    output = Path(__file__).resolve().parents[1] / "data" / "benchmarks" / "python_projects"
    output.mkdir(parents=True, exist_ok=True)
    candidate_file = output / "formal_candidates.json"
    draft_ids = ({item["id"] for item in json.loads(candidate_file.read_text(encoding="utf-8"))["tasks"]}
                 if candidate_file.exists() else set())
    found = {}
    for offset in range(0, 500, 100):
        query = urllib.parse.urlencode({"dataset": DATASET, "revision": REVISION, "config": "default",
                                        "split": "test", "offset": offset, "length": 100})
        with urllib.request.urlopen("https://datasets-server.huggingface.co/rows?" + query, timeout=60) as stream:
            rows = json.load(stream)["rows"]
        for entry in rows:
            row = entry["row"]
            if row["instance_id"] in SELECTION:
                found[row["instance_id"]] = row
    missing = set(SELECTION) - set(found)
    if missing:
        raise RuntimeError(f"Pinned dataset is missing tasks: {sorted(missing)}")
    for instance_id, category in sorted(SELECTION.items()):
        row = found[instance_id]
        repo = row["repo"]
        manifest = {
            "id": instance_id, "backend": "swebench", "category": category,
            "repo": {"url": f"https://github.com/{repo}.git", "base_commit": row["base_commit"]},
            "issue": row["problem_statement"],
            "source": {"dataset": DATASET, "revision": REVISION, "split": "test",
                       "instance_id": instance_id, "difficulty": row.get("difficulty")},
            "allowed_paths": [], "formal_files": [], "protected_files": [],
            "formal_review_status": ("draft_pending_human_review" if instance_id in draft_ids
                                     else "not_reviewed"),
        }
        (output / f"{instance_id}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {"dataset": DATASET, "revision": REVISION, "total_tasks": len(SELECTION),
             "categories": {name: sum(value == name for value in SELECTION.values())
                            for name in sorted(set(SELECTION.values()))},
             "tasks": sorted(SELECTION)}
    (output / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(SELECTION)} pinned manifests to {output}")


if __name__ == "__main__":
    main()
