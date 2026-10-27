"""Module khóa hợp đồng Dafny và phát hiện các cách né chứng minh rõ ràng."""

import hashlib
import json
import re
from dataclasses import dataclass


from typing import Optional, Set


@dataclass(frozen=True)
class SpecAuditResult:
    valid: bool
    issues: tuple[str, ...]


_DECLARATION = re.compile(r"(?m)^\s*(?:(?:ghost|static|opaque)\s+)*(method|function|predicate|lemma)\s+([A-Za-z_]\w*)\b")
_CLAUSE = re.compile(r"(?m)^\s*(requires|ensures|modifies|reads|decreases)\s+([^\n{;]+)")
_TRUST_ESCAPE = re.compile(r"\bassume\b|\{:\s*(?:axiom|verify\s+false|extern)\b", re.I)


class SpecLocker:
    """Bảo vệ hợp đồng của các khai báo gốc trong mã Dafny."""

    @staticmethod
    def extract_clauses(dafny_code: str) -> Set[str]:
        """Trích xuất tập hợp tất cả các mệnh đề ensures đã chuẩn hóa trong mã nguồn Dafny.

        - Loại bỏ comment (// ... và /* ... */).
        - Chuẩn hóa khoảng trắng và dấu chấm phẩy để không bị sai lệch do định dạng.
        """
        # Loại bỏ block comment /* ... */
        clean_code = re.sub(r'/\*.*?\*/', '', dafny_code, flags=re.DOTALL)
        # Loại bỏ line comment // ...
        clean_code = re.sub(r'//.*', '', clean_code)

        # Bắt từng mệnh đề ensures: từ sau từ khóa ensures đến dấu chấm phẩy hoặc ký tự xuống dòng / mở ngoặc nhọn
        pattern = re.compile(r'\bensures\s+([^;{\n]+)(?:;)?', re.MULTILINE)
        matches = pattern.findall(clean_code)

        clauses = set()
        for m in matches:
            norm = re.sub(r'[\s;]+', '', m)
            if norm:
                clauses.add(norm)
        return clauses

    @classmethod
    def extract_ensures(cls, dafny_code: str) -> str:
        """Trích xuất và chuẩn hóa tất cả các mệnh đề ensures nối thành chuỗi theo thứ tự."""
        clauses = sorted(list(cls.extract_clauses(dafny_code)))
        return ";".join(clauses)

    @classmethod
    def get_hash(cls, dafny_code: str) -> str:
        """Tính SHA-256 cho hợp đồng và định nghĩa pure, dùng khi không có raw spec."""
        payload = {"contracts": cls._contracts(dafny_code), "pure_bodies": cls._pure_bodies(dafny_code)}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    @staticmethod
    def _without_comments(code: str) -> str:
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
        return re.sub(r"//[^\n]*", "", code)

    @classmethod
    def _contracts(cls, code: str) -> dict[str, tuple[str, tuple[tuple[str, str], ...]]]:
        clean = cls._without_comments(code)
        matches = list(_DECLARATION.finditer(clean))
        contracts: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {}
        for match in matches:
            rest = clean[match.end():]
            body_start = rest.find("{")
            next_decl = next((m.start() - match.end() for m in matches if m.start() > match.start()), len(rest))
            header = rest[:min(body_start if body_start >= 0 else next_decl, next_decl)]
            clauses = tuple((kind, re.sub(r"\s+", "", value)) for kind, value in _CLAUSE.findall(header))
            signature = re.sub(r"\s+", "", _CLAUSE.split(header, maxsplit=1)[0].rstrip(";"))
            contracts[match.group(2)] = (match.group(1) + signature, clauses)
        return contracts

    @classmethod
    def _pure_bodies(cls, code: str) -> dict[str, str]:
        clean = cls._without_comments(code)
        matches = list(_DECLARATION.finditer(clean))
        bodies: dict[str, str] = {}
        for index, match in enumerate(matches):
            if match.group(1) not in {"function", "predicate", "lemma"}:
                continue
            limit = matches[index + 1].start() if index + 1 < len(matches) else len(clean)
            opening = clean.find("{", match.end(), limit)
            if opening < 0:
                continue
            depth = 0
            for pos in range(opening, len(clean)):
                if clean[pos] == "{":
                    depth += 1
                elif clean[pos] == "}":
                    depth -= 1
                    if depth == 0:
                        bodies[match.group(2)] = re.sub(r"\s+", "", clean[opening:pos + 1])
                        break
        return bodies

    @classmethod
    def validate(cls, original: str, candidate: str) -> SpecAuditResult:
        """Preserve every original declaration contract and reject explicit proof escapes.

        This is a conservative lexical gate. `dafny audit` remains mandatory for
        formal claims because a text scanner cannot establish specification quality.
        """
        issues: list[str] = []
        original_contracts = cls._contracts(original)
        new_contracts = cls._contracts(candidate)
        for name, contract in original_contracts.items():
            if new_contracts.get(name) != contract:
                issues.append(f"contract_changed:{name}")
        new_pure_bodies = cls._pure_bodies(candidate)
        for name, body in cls._pure_bodies(original).items():
            if new_pure_bodies.get(name) != body:
                issues.append(f"pure_definition_changed:{name}")
        if not original_contracts and cls.extract_clauses(original) != cls.extract_clauses(candidate):
            issues.append("ensures_changed")
        clean = cls._without_comments(candidate)
        if _TRUST_ESCAPE.search(clean):
            issues.append("unproved_assumption_or_axiom")
        return SpecAuditResult(not issues, tuple(issues))

    @classmethod
    def is_valid(cls, original_hash: str, new_code: str, raw_spec: Optional[str] = None) -> bool:
        """Kiểm tra hợp đồng gốc; fallback dùng mã băm khi thiếu raw spec."""
        if raw_spec:
            return cls.validate(raw_spec, new_code).valid

        return cls.get_hash(new_code) == original_hash
