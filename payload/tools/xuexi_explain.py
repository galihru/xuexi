from __future__ import annotations

import argparse
from pathlib import Path

from llama_cpp import Llama


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    files = sorted((root / "src").rglob("*.py"))
    model = Llama(model_path=str(args.model), n_ctx=8192, n_threads=4, verbose=False)
    sections = ["# Xuexi Code Explanation", ""]
    for path in files:
        relative = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        numbered = "\n".join(f"{i:>5} | {line}" for i, line in enumerate(lines, 1))
        prompt = f"""
请使用规范、准确、专业的简体中文解释文件 `{relative}`。
必须以源代码为依据，保留所有标识符，不得虚构功能。
按函数、类和必要的行号范围说明数学逻辑与程序流程。

```text
{numbered[:42000]}
```
"""
        response = model.create_chat_completion(
            messages=[
                {"role": "system", "content": "你是严谨的软件工程与数学文档编写者。只输出 Markdown。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2200,
        )
        text = response["choices"][0]["message"]["content"]
        sections.extend([f"## `{relative}`", "", str(text).strip(), ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(sections), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
