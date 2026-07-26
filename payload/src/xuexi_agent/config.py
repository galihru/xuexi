from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> dict[str, Any]:
    """读取并校验代理配置。"""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("代理配置必须是映射。")
    for key in ("agent", "model", "simulation", "safety"):
        if key not in data or not isinstance(data[key], dict):
            raise ValueError(f"配置缺少节：{key}")
    return data
