from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

import fitz


EQUATION_PATTERN = re.compile(r"\((\d+\.\d+)\)")
SECTION_PATTERN = re.compile(r"^\s*((?:[1-9]|1[0-2])(?:\.\d+)?)\s+([^\n]{3,140})$", re.MULTILINE)


@dataclass(frozen=True)
class EquationRecord:
    label: str
    page: int
    section: str
    context: str


def _clean(text: str) -> str:
    text = text.replace("\x00", " ").replace("\xad", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages(pdf_path: Path) -> list[str]:
    """逐页提取论文文本。"""
    document = fitz.open(pdf_path)
    try:
        return [_clean(page.get_text("text")) for page in document]
    finally:
        document.close()


def extract_equations(pdf_path: Path) -> list[EquationRecord]:
    """提取所有编号公式及其页面上下文。"""
    records: list[EquationRecord] = []
    seen: set[str] = set()
    current_section = ""

    for page_number, page in enumerate(extract_pages(pdf_path), start=1):
        for match in EQUATION_PATTERN.finditer(page):
            label = match.group(1)
            if label in seen:
                continue
            seen.add(label)
            before = page[: match.start()]
            headings = list(SECTION_PATTERN.finditer(before))
            if headings:
                heading = headings[-1]
                current_section = f"{heading.group(1)} {heading.group(2).strip()}"
            start = max(0, match.start() - 1100)
            end = min(len(page), match.end() + 520)
            records.append(
                EquationRecord(
                    label=label,
                    page=page_number,
                    section=current_section,
                    context=_clean(page[start:end]),
                )
            )

    records.sort(key=lambda item: tuple(int(x) for x in item.label.split(".")))
    return records


def write_equation_index(pdf_path: Path, output: Path) -> list[EquationRecord]:
    records = extract_equations(pdf_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return records


def load_equation_index(path: Path) -> list[EquationRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [EquationRecord(**item) for item in raw]


def select_equations(
    records: list[EquationRecord],
    reviewed: set[str],
    implemented: set[str],
    batch_size: int,
) -> list[EquationRecord]:
    """优先选择尚未实现且尚未复核的公式。"""
    priority_sections = {1, 4, 5, 7, 8, 9, 10, 11, 12}

    def key(record: EquationRecord) -> tuple[int, int, int]:
        chapter = int(record.label.split(".")[0])
        return (
            0 if record.label not in implemented else 1,
            0 if record.label not in reviewed else 1,
            0 if chapter in priority_sections else 1,
        )

    ordered = sorted(records, key=lambda record: (key(record), tuple(map(int, record.label.split(".")))))
    return ordered[: max(1, batch_size)]
