from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


@dataclass(frozen=True)
class Evaluation:
    score: float
    tests_passed: bool
    simulation_passed: bool
    equation_labels: list[str]
    documentation_score: float
    test_output: str
    simulation_output: str


LABEL_PATTERN = re.compile(r"['\"](\d+\.\d+)['\"]")


def _run(command: list[str], root: Path, timeout: int) -> tuple[bool, str]:
    environment = os.environ.copy()
    source = str(root / "src")
    environment["PYTHONPATH"] = source + os.pathsep + environment.get("PYTHONPATH", "")
    completed = subprocess.run(
        command,
        cwd=root,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return completed.returncode == 0, completed.stdout[-16000:]


def equation_labels(root: Path) -> list[str]:
    path = root / "src/xuexi_agent/generated/equation_extensions.py"
    if not path.exists():
        return []
    return sorted(set(LABEL_PATTERN.findall(path.read_text(encoding="utf-8"))), key=lambda value: tuple(map(int, value.split("."))))


def documentation_quality(root: Path) -> float:
    score = 0.0
    readme = root / "README.md"
    note = root / "docs/AI_RESEARCH_NOTE.md"
    coverage = root / "docs/EQUATION_COVERAGE.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        score += min(4.0, len(text) / 3000.0)
        if "```mermaid" in text:
            score += 1.5
        if "自主" in text or "代理" in text:
            score += 0.5
    if note.exists() and len(note.read_text(encoding="utf-8")) > 1200:
        score += 2.0
    if coverage.exists() and "254" in coverage.read_text(encoding="utf-8"):
        score += 2.0
    return min(score, 10.0)


def evaluate(root: Path, quick: bool = True) -> Evaluation:
    tests_ok, tests_output = _run([sys.executable, "-m", "pytest", "-q"], root, timeout=180)
    simulation_command = [
        sys.executable,
        "-m",
        "kakeya_sim",
        "--mode",
        "mixed",
        "--seed",
        "250217655",
        "--tubes",
        "18" if quick else "36",
        "--delta",
        "0.065",
        "--rho",
        "0.26",
        "--resolution",
        "20" if quick else "32",
        "--frames",
        "8" if quick else "36",
        "--fps",
        "8",
        "--output",
        ".agent-evaluation/artifacts",
        "--site-output",
        ".agent-evaluation/site",
    ]
    simulation_ok, simulation_output = _run(simulation_command, root, timeout=300)
    labels = equation_labels(root)
    docs = documentation_quality(root)
    score = (50.0 if tests_ok else 0.0) + (25.0 if simulation_ok else 0.0)
    score += min(15.0, len(labels) * 0.75)
    score += docs
    return Evaluation(
        score=round(score, 4),
        tests_passed=tests_ok,
        simulation_passed=simulation_ok,
        equation_labels=labels,
        documentation_score=docs,
        test_output=tests_output,
        simulation_output=simulation_output,
    )


def write_evaluation(path: Path, evaluation: Evaluation) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(evaluation), ensure_ascii=False, indent=2), encoding="utf-8")
