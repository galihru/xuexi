from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath
from typing import Any


FORBIDDEN_CALLS = {"eval", "exec", "compile", "open", "input", "__import__", "breakpoint"}
FORBIDDEN_ATTRIBUTES = {"system", "popen", "spawn", "fork", "remove", "unlink", "rmtree", "rmdir", "rename", "replace"}


def validate_relative_path(path: str, writable_paths: set[str]) -> str:
    normalized = PurePosixPath(path).as_posix()
    if normalized.startswith("/") or ".." in PurePosixPath(normalized).parts:
        raise ValueError(f"非法路径：{path}")
    if normalized not in writable_paths:
        raise ValueError(f"模型无权修改：{normalized}")
    return normalized


def validate_python_source(source: str, allowed_import_roots: set[str]) -> None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in allowed_import_roots:
                    raise ValueError(f"禁止导入模块：{root}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root not in allowed_import_roots and root != "__future__":
                raise ValueError(f"禁止导入模块：{root}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                raise ValueError(f"禁止调用函数：{node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in FORBIDDEN_ATTRIBUTES:
                raise ValueError(f"禁止调用属性：{node.func.attr}")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            raise ValueError("生成模块不得使用 global 或 nonlocal。")


def validate_proposal(
    proposal: dict[str, Any],
    writable_paths: set[str],
    allowed_import_roots: set[str],
    maximum_bytes: int,
) -> list[tuple[str, str]]:
    files = proposal.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("提案必须包含非空 files 数组。")

    validated: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in files:
        if not isinstance(item, dict):
            raise ValueError("files 中的每个项目必须是对象。")
        raw_path = item.get("path")
        content = item.get("content")
        if not isinstance(raw_path, str) or not isinstance(content, str):
            raise ValueError("path 与 content 必须是字符串。")
        path = validate_relative_path(raw_path, writable_paths)
        if path in seen:
            raise ValueError(f"重复文件：{path}")
        seen.add(path)
        if len(content.encode("utf-8")) > maximum_bytes:
            raise ValueError(f"文件过大：{path}")
        if path.endswith(".py"):
            validate_python_source(content, allowed_import_roots)
        validated.append((path, content.rstrip() + "\n"))
    return validated


def apply_files(root: Path, files: list[tuple[str, str]]) -> None:
    for relative, content in files:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
