from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluator import evaluate, write_evaluation
from .paper import write_equation_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="学习自主研究代理")
    subparsers = parser.add_subparsers(dest="command", required=True)

    agent = subparsers.add_parser("agent", help="运行有界自主研究循环")
    agent.add_argument("--root", type=Path, default=Path("."))
    agent.add_argument("--model", type=Path, required=True)
    agent.add_argument("--config", type=Path, default=Path("config/agent.yaml"))
    agent.add_argument("--paper", type=Path, default=Path("paper/2502.17655v1.pdf"))
    agent.add_argument("--rounds", type=int, default=None)

    index = subparsers.add_parser("index-paper", help="重建论文公式索引")
    index.add_argument("--paper", type=Path, default=Path("paper/2502.17655v1.pdf"))
    index.add_argument("--output", type=Path, default=Path("knowledge/equations.json"))

    check = subparsers.add_parser("evaluate", help="评估当前代码")
    check.add_argument("--root", type=Path, default=Path("."))
    check.add_argument("--output", type=Path, default=Path("state/latest_evaluation.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "agent":
        from .agent import run_agent

        report = run_agent(
            root=args.root.resolve(),
            model_path=args.model.resolve(),
            config_path=args.config.resolve(),
            paper_path=args.paper.resolve(),
            rounds=args.rounds,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.command == "index-paper":
        records = write_equation_index(args.paper.resolve(), args.output.resolve())
        print(f"已索引 {len(records)} 个编号公式。")
        return 0
    if args.command == "evaluate":
        result = evaluate(args.root.resolve(), quick=True)
        write_evaluation(args.output.resolve(), result)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
