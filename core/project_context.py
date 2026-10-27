"""Bounded, reproducible context selection for repository repair tasks."""

from __future__ import annotations

import ast
import hashlib
import re
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


_STOP = {"the", "and", "for", "with", "from", "that", "this", "when", "error", "python", "test"}
_EXCLUDED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".tox", "build", "dist"}


@dataclass(frozen=True)
class ContextFile:
    path: str
    sha256: str
    chars: int
    truncated: bool
    reason: str


@dataclass(frozen=True)
class ContextBundle:
    text: str
    files: tuple[ContextFile, ...]
    budget_chars: int

    def evidence(self) -> list[dict]:
        return [asdict(item) for item in self.files]


def _tokens(value: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", value.lower())
    normalized = set()
    for word in words:
        for token in word.split("_"):
            if token in _STOP or len(token) < 3:
                continue
            if token == "indices" or token == "indexing":
                token = "index"
            elif token.endswith("ies") and len(token) > 5:
                token = token[:-3] + "y"
            elif token.endswith("s") and len(token) > 4:
                token = token[:-1]
            normalized.add(token)
    return normalized


def _py_metadata(path: Path) -> tuple[set[str], set[str]]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeError, OSError):
        return set(), set()
    imports: set[str] = set()
    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name.lower())
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, (ast.Name, ast.Attribute)):
                symbols.add(func.id.lower() if isinstance(func, ast.Name) else func.attr.lower())
    return imports, symbols


def _excerpt(raw: str, terms: set[str], budget: int) -> str:
    """Keep numbered windows around matching lines instead of the file prefix."""
    lines = raw.splitlines()
    matches = []
    for index, line in enumerate(lines):
        hits = len(_tokens(line) & terms)
        if hits:
            matches.append((hits, index))
    matches.sort(key=lambda item: (-item[0], item[1]))
    chosen: set[int] = set()
    for _, index in matches[:12]:
        chosen.update(range(max(0, index - 3), min(len(lines), index + 5)))
    if not chosen:
        chosen.update(range(min(len(lines), 25)))
    output = []
    last = -2
    for index in sorted(chosen):
        prefix = "...\n" if index > last + 1 else ""
        piece = prefix + f"{index + 1:5d} | {lines[index]}\n"
        if sum(map(len, output)) + len(piece) > budget:
            break
        output.append(piece)
        last = index
    return "".join(output)


def select_context(
    repo: Path,
    issue: str,
    *,
    diagnostics: str = "",
    budget_chars: int = 24000,
    allowed_paths: Iterable[str] = (),
) -> ContextBundle:
    """Rank Python files by issue terms, stack paths, imports and referenced symbols."""
    if budget_chars < 500:
        raise ValueError("budget_chars must be at least 500")
    repo = repo.resolve()
    allowed = tuple(allowed_paths)
    terms = _tokens(issue + " " + diagnostics)
    stack_paths = set(re.findall(r"([\w./-]+\.py)(?::\d+)?", issue + "\n" + diagnostics))
    candidates = [p for p in repo.rglob("*.py") if not any(part in _EXCLUDED or part.startswith(".env") for part in p.relative_to(repo).parts)]
    metadata = {p: _py_metadata(p) for p in candidates}
    named_modules = {p.stem: p for p in candidates}
    scored: list[tuple[int, Path, str]] = []
    for path in candidates:
        relative = path.relative_to(repo).as_posix()
        path_tokens = _tokens(relative)
        imports, symbols = metadata[path]
        score = 5 * len(path_tokens & terms) + 3 * len(symbols & terms)
        if relative in stack_paths or path.name in stack_paths:
            score += 100
        if any(relative.startswith(prefix.rstrip("/") + "/") or relative == prefix for prefix in allowed):
            score += 8
        if path.stem.startswith("test_") or "/tests/" in f"/{relative}/":
            score -= 25
        if score > 0:
            scored.append((score, path, "issue/diagnostic/symbol"))
        for module in imports:
            target = named_modules.get(module)
            if target and target != path and score > 5:
                scored.append((max(1, score // 4), target, f"imported by {relative}"))
    if not scored:
        scored = [(1, p, "fallback") for p in sorted(candidates)[:5]]
    best: dict[Path, tuple[int, str]] = {}
    for score, path, reason in scored:
        if score > best.get(path, (-1, ""))[0]:
            best[path] = (score, reason)
    ordered = sorted(best, key=lambda p: (-best[p][0], p.relative_to(repo).as_posix()))
    chunks: list[str] = []
    evidence: list[ContextFile] = []
    used = 0
    per_file_budget = max(500, min(6000, budget_chars // 5))
    for path in ordered:
        if used >= budget_chars:
            break
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        relative = path.relative_to(repo).as_posix()
        header = f"\n### {relative}\n"
        remaining = budget_chars - used - len(header)
        if remaining < 100:
            break
        content = _excerpt(raw, terms, min(remaining, per_file_budget))
        if not content:
            continue
        chunks.append(header + content)
        used += len(header) + len(content)
        evidence.append(ContextFile(relative, hashlib.sha256(raw.encode()).hexdigest(), len(content), len(content) < len(raw), best[path][1]))
    return ContextBundle("".join(chunks), tuple(evidence), budget_chars)
