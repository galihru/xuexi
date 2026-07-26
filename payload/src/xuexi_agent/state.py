from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": 2,
            "cycle": 0,
            "last_score": None,
            "last_accepted_at": None,
            "last_model": None,
            "reviewed_equations": [],
            "implemented_equations": [],
            "failed_attempts": 0,
            "history": [],
        }
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("代理状态文件损坏。")
    return value


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def record_cycle(
    state: dict[str, Any],
    *,
    accepted: bool,
    score_before: float,
    score_after: float,
    targets: list[str],
    model: str,
    message: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    state["cycle"] = int(state.get("cycle", 0)) + 1
    state["last_model"] = model
    state["last_score"] = score_after if accepted else score_before
    state["reviewed_equations"] = sorted(
        set(state.get("reviewed_equations", [])) | set(targets),
        key=lambda value: tuple(map(int, value.split("."))),
    )
    if accepted:
        state["last_accepted_at"] = now
        state["failed_attempts"] = 0
    else:
        state["failed_attempts"] = int(state.get("failed_attempts", 0)) + 1
    history = list(state.get("history", []))
    history.append(
        {
            "time": now,
            "accepted": accepted,
            "score_before": score_before,
            "score_after": score_after,
            "targets": targets,
            "message": message,
        }
    )
    state["history"] = history[-40:]
