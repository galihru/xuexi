from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from llama_cpp import Llama


class LocalModel:
    """本地 GGUF 模型封装。"""

    def __init__(self, model_path: Path, config: dict[str, Any]) -> None:
        self.max_output_tokens = int(config.get("max_output_tokens", 4096))
        self.temperature = float(config.get("temperature", 0.12))
        self.top_p = float(config.get("top_p", 0.9))
        self.model = Llama(
            model_path=str(model_path),
            n_ctx=int(config.get("context_size", 8192)),
            n_batch=256,
            n_threads=2,
            seed=int(config.get("seed", 20250224)),
            verbose=False,
        )

    def chat(self, system: str, user: str, max_tokens: int | None = None) -> str:
        response = self.model.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=max_tokens or self.max_output_tokens,
        )
        content = response["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("本地模型返回了空内容。")
        return content.strip()

    def json(self, system: str, user: str) -> dict[str, Any]:
        text = self.chat(system, user)
        candidates = [text]
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if fenced:
            candidates.insert(0, fenced.group(1))
        first = text.find("{")
        last = text.rfind("}")
        if first >= 0 and last > first:
            candidates.append(text[first : last + 1])
        for candidate in candidates:
            try:
                value = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        raise ValueError("模型输出不是有效的 JSON 对象。")
