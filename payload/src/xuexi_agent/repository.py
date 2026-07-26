from __future__ import annotations

from pathlib import Path


INCLUDED_SUFFIXES = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".csv"}
IGNORED_PARTS = {".git", ".venv", "venv", "__pycache__", "artifacts", "site", ".pytest_cache"}


def tree(root: Path, limit: int = 320) -> str:
    rows: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        depth = len(relative.parts) - 1
        marker = "📁" if path.is_dir() else "📄"
        rows.append(f"{'  ' * depth}{marker} {relative.name}")
        if len(rows) >= limit:
            rows.append("…")
            break
    return "\n".join(rows)


def snapshot(root: Path, maximum_characters: int) -> str:
    parts: list[str] = []
    used = 0
    preferred = [
        "src/kakeya_sim/formulas.py",
        "src/kakeya_sim/multiscale.py",
        "src/kakeya_sim/wolff.py",
        "src/kakeya_sim/geometry.py",
        "src/xuexi_agent/generated/strategy.py",
        "src/xuexi_agent/generated/equation_extensions.py",
        "README.md",
    ]
    candidates: list[Path] = []
    for name in preferred:
        path = root / name
        if path.is_file():
            candidates.append(path)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path in candidates:
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() not in INCLUDED_SUFFIXES:
            continue
        candidates.append(path)

    for path in candidates:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        relative = path.relative_to(root).as_posix()
        block = f"\n--- FILE: {relative} ---\n{content[:14000]}\n"
        if used + len(block) > maximum_characters:
            break
        parts.append(block)
        used += len(block)
    return "".join(parts)
