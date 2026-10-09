"""Bộ kiểm thử đơn vị cho Cấu trúc Dữ liệu Quy Nạp (Inductive Data Structures: Trees & Lists).

Kiểm tra:
1. Nhận diện hình thái giải thuật (Algorithmic Topology) RECURSIVE_TREE và LINKED_LIST.
2. Khung chỉ dẫn ràng buộc cấu trúc (Inductive Directive) với cấu trúc match-case.
3. Đăng ký tự động 35 bài toán trong danh mục benchmark.
4. Tính toàn vẹn của 5 tệp đặc tả quy nạp Dafny 4.x mới.
"""

import unittest
from pathlib import Path

from core.topology_detector import TopologyDetector, AlgorithmTopology
from web_demo.helpers import (
    get_benchmark_tasks,
    get_flat_task_registry,
    get_preset_labels,
    load_task_spec,
)


class TestInductiveStructures(unittest.TestCase):
    """Kiểm tra toàn diện mở rộng Cây nhị phân và Danh sách liên kết quy nạp."""

    def setUp(self):
        self.inductive_dir = Path("data/benchmarks/advanced_inductive")

    def test_benchmark_files_exist_and_structure(self):
        """Kiểm tra 5 tệp benchmark quy nạp tồn tại đầy đủ các thẻ đánh dấu cấu trúc chuẩn."""
        expected_files = [
            "tree_size_height.dfy",
            "bst_search.dfy",
            "bst_insert.dfy",
            "linked_list_reverse.dfy",
            "linked_list_stats.dfy",
        ]
        for fname in expected_files:
            file_path = self.inductive_dir / fname
            self.assertTrue(file_path.exists(), f"Tệp benchmark {fname} phải tồn tại trên đĩa")
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("// pure-end", content, f"{fname} phải có thẻ // pure-end")
            self.assertIn("// post-conditions-end", content, f"{fname} phải có thẻ // post-conditions-end")
            self.assertIn("// impl-start", content, f"{fname} phải có thẻ // impl-start")
            self.assertIn("// impl-end", content, f"{fname} phải có thẻ // impl-end")

    def test_topology_detection_recursive_tree(self):
        """Kiểm tra nhận diện RECURSIVE_TREE cho các bài toán Cây nhị phân và BST."""
        tree_files = ["tree_size_height.dfy", "bst_search.dfy", "bst_insert.dfy"]
        for fname in tree_files:
            content = (self.inductive_dir / fname).read_text(encoding="utf-8")
            top = TopologyDetector.detect(content)
            self.assertEqual(
                top,
                AlgorithmTopology.RECURSIVE_TREE,
                f"{fname} phải được nhận diện là RECURSIVE_TREE, nhưng nhận được {top}"
            )

    def test_topology_detection_linked_list(self):
        """Kiểm tra nhận diện LINKED_LIST cho các bài toán Danh sách liên kết đại số."""
        list_files = ["linked_list_reverse.dfy", "linked_list_stats.dfy"]
        for fname in list_files:
            content = (self.inductive_dir / fname).read_text(encoding="utf-8")
            top = TopologyDetector.detect(content)
            self.assertEqual(
                top,
                AlgorithmTopology.LINKED_LIST,
                f"{fname} phải được nhận diện là LINKED_LIST, nhưng nhận được {top}"
            )

    def test_topology_directive_recursive_tree(self):
        """Kiểm tra chỉ dẫn ràng buộc cấu trúc sinh ra khớp mẫu match-case cho Cây."""
        directive = TopologyDetector.get_topology_directive(AlgorithmTopology.RECURSIVE_TREE)
        self.assertIn("RECURSIVE TREE / BST", directive)
        self.assertIn("datatype Tree", directive)
        self.assertIn("match t", directive)
        self.assertIn("case Leaf =>", directive)
        self.assertIn("case Node", directive)
        self.assertIn("KHÔNG CẦN viết `decreases`", directive)

    def test_topology_directive_linked_list(self):
        """Kiểm tra chỉ dẫn ràng buộc cấu trúc sinh ra khớp mẫu match-case cho Danh sách."""
        directive = TopologyDetector.get_topology_directive(AlgorithmTopology.LINKED_LIST)
        self.assertIn("INDUCTIVE LINKED LIST", directive)
        self.assertIn("datatype List", directive)
        self.assertIn("match l", directive)
        self.assertIn("case Nil =>", directive)
        self.assertIn("case Cons", directive)

    def test_registry_expansion_35_tasks(self):
        """Kiểm tra việc mở rộng danh mục benchmark lên 35 bài toán."""
        tasks = get_benchmark_tasks()
        self.assertIn("Advanced Inductive Structures (Cây & Danh Sách)", tasks)
        self.assertEqual(len(tasks["Advanced Inductive Structures (Cây & Danh Sách)"]), 5)

        registry = get_flat_task_registry()
        self.assertEqual(len(registry), 35, "Tổng số bài toán sau Bước 5 phải là 35 bài")

        inductive_tasks = [k for k, v in registry.items() if v["group"] == "Inductive"]
        self.assertEqual(len(inductive_tasks), 5, "Nhóm Inductive phải có đúng 5 bài toán")

    def test_preset_inductive(self):
        """Kiểm tra preset 'inductive' trả về đúng 5 nhãn bài toán."""
        preset = get_preset_labels("inductive")
        self.assertEqual(len(preset), 5)
        self.assertTrue(all("[Inductive]" in label for label in preset))

    def test_load_inductive_task_spec(self):
        """Kiểm tra việc đọc đặc tả bài toán quy nạp thông qua load_task_spec."""
        spec = load_task_spec("data/benchmarks/advanced_inductive/bst_search.dfy")
        self.assertTrue(len(spec) > 50)
        self.assertIn("predicate is_bst", spec)
        self.assertIn("method bst_search", spec)


if __name__ == "__main__":
    unittest.main()
