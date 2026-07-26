from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any

from .config import load_config
from .evaluator import Evaluation, evaluate, write_evaluation
from .llm import LocalModel
from .paper import EquationRecord, select_equations, write_equation_index
from .repository import snapshot, tree
from .safety import apply_files, validate_proposal
from .state import load_state, record_cycle, save_state


SYSTEM_PROMPT = """
你是“学习（Xuexi）”，一个在本地运行的严谨数学软件研究代理。
你的任务是阅读 Wang–Zahl 关于三维 Kakeya 集的论文、检查当前代码、提出受限代码修改、运行验证并改进文档。

强制规则：
1. 所有面向读者的文字必须使用规范、自然、专业的简体中文。
2. 只能依据提供的论文文本和代码，不得声称数值实验证明了论文定理。
3. 必须区分“严格数学结论”“有限分辨率数值诊断”“启发式解释”。
4. 不得访问网络、文件系统、密钥、环境变量或执行外部命令。
5. 生成的 Python 只能使用 math、dataclasses、typing、numpy。
6. 不得修改工作流、安全模块、凭据逻辑、测试框架或论文 PDF。
7. 返回一个 JSON 对象，不得在 JSON 外添加任何文字。
8. JSON 必须包含 summary、target_equations、files、expected_gain、risks。
9. files 是对象数组，每项包含 path 与完整 content。
10. 修改必须能通过现有测试，并在数值意义上增加公式覆盖或提高研究说明质量。
""".strip()

REVIEW_SYSTEM_PROMPT = """
你是学习代理的独立复核器。请检查候选修改是否忠实于论文、是否把数值实验误写成证明、是否保持简体中文一致性、是否存在不必要的静态硬编码，以及是否真正增加公式覆盖或研究质量。
只返回 JSON 对象，字段必须为 approved、weaknesses、revision_instruction。approved 只能是 true 或 false。
""".strip()


def _equation_context(records: list[EquationRecord], maximum_characters: int) -> str:
    parts: list[str] = []
    used = 0
    for record in records:
        block = (
            f"\n### 公式 ({record.label}) · 第 {record.page} 页 · {record.section}\n"
            f"{record.context}\n"
        )
        if used + len(block) > maximum_characters:
            break
        parts.append(block)
        used += len(block)
    return "".join(parts)


def _proposal_prompt(
    root: Path,
    config: dict[str, Any],
    state: dict[str, Any],
    targets: list[EquationRecord],
    baseline: Evaluation,
    previous_feedback: str,
) -> str:
    agent_cfg = config["agent"]
    repository_text = snapshot(root, int(agent_cfg["max_repository_characters"]))
    paper_text = _equation_context(targets, int(agent_cfg["max_paper_characters"]))
    writable = "\n".join(f"- {path}" for path in config["safety"]["writable_paths"])
    return f"""
当前目标是让代码真正形成“阅读论文 → 提出改进 → 写入候选代码 → 测试 → 自我批评 → 接受或回退 → 重新渲染”的循环。

当前代理状态：
```json
{json.dumps(state, ensure_ascii=False, indent=2)}
```

当前基准评估：
```json
{json.dumps(asdict(baseline), ensure_ascii=False, indent=2)}
```

本轮重点论文公式：
{paper_text}

仓库结构：
```text
{tree(root)}
```

当前关键代码：
{repository_text}

允许修改的完整路径只有：
{writable}

生成模块接口：
- `strategy.py` 必须提供 `mutate_parameters(parameters, context)` 和 `research_hypotheses(context)`。
- `equation_extensions.py` 必须提供 `EQUATION_LABELS` 与 `evaluate(metrics, parameters)`。
- `evaluate` 返回字典数组；每项至少包含 label、status、observed、reference、ratio、passed、note。
- README.md 必须包含 Mermaid 架构图，并说明代理的真实边界。
- docs/AI_RESEARCH_NOTE.md 必须记录论文依据、假设、数值限制、自我批评和下一步。
- docs/EQUATION_COVERAGE.md 必须说明论文共有 254 个编号公式，区分已执行、数值诊断、仅证明链条三类。

上一次失败或批评反馈：
{previous_feedback or '无。'}

请产生一组小而有效的改进。不要重写整个项目。优先把本轮公式转化为可验证的数值诊断或更准确的解释。
""".strip()


def _candidate_copy(root: Path) -> Path:
    temporary = Path(tempfile.mkdtemp(prefix="xuexi-candidate-"))
    ignored = shutil.ignore_patterns(
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".agent-evaluation",
        "artifacts",
        "site",
        "*.gguf",
    )
    shutil.copytree(root, temporary / "repo", dirs_exist_ok=True, ignore=ignored)
    return temporary / "repo"


def _summarize_failure(error: Exception | None, evaluation: Evaluation | None) -> str:
    parts: list[str] = []
    if error is not None:
        parts.append(f"验证异常：{type(error).__name__}: {error}")
    if evaluation is not None:
        parts.append(f"候选得分：{evaluation.score}")
        if not evaluation.tests_passed:
            parts.append("测试失败：\n" + evaluation.test_output[-6000:])
        if not evaluation.simulation_passed:
            parts.append("模拟失败：\n" + evaluation.simulation_output[-6000:])
    return "\n\n".join(parts)[-12000:]


def run_agent(
    root: Path,
    model_path: Path,
    config_path: Path,
    paper_path: Path,
    rounds: int | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    state_path = root / "state/agent_state.json"
    state = load_state(state_path)
    index_path = root / "knowledge/equations.json"
    records = write_equation_index(paper_path, index_path)
    if len(records) != 254:
        raise RuntimeError(f"论文公式索引应为 254 条，实际得到 {len(records)} 条。")

    targets = select_equations(
        records,
        reviewed=set(state.get("reviewed_equations", [])),
        implemented=set(state.get("implemented_equations", [])),
        batch_size=int(config["agent"]["equation_batch_size"]),
    )
    target_labels = [record.label for record in targets]
    baseline = evaluate(root, quick=True)
    local_model = LocalModel(model_path, config["model"])
    total_rounds = rounds or int(config["agent"]["rounds_per_run"])
    writable_paths = set(config["safety"]["writable_paths"])
    allowed_imports = set(config["safety"]["allowed_import_roots"])
    maximum_bytes = int(config["agent"]["generated_file_limit_bytes"])
    minimum_gain = float(config["agent"].get("minimum_score_gain", 0.25))

    accepted_files: list[tuple[str, str]] | None = None
    accepted_evaluation: Evaluation | None = None
    feedback = ""
    attempts: list[dict[str, Any]] = []

    for round_number in range(1, total_rounds + 1):
        candidate_root: Path | None = None
        proposal: dict[str, Any] | None = None
        candidate_evaluation: Evaluation | None = None
        error: Exception | None = None
        review: dict[str, Any] | None = None
        try:
            proposal = local_model.json(
                SYSTEM_PROMPT,
                _proposal_prompt(root, config, state, targets, baseline, feedback),
            )
            files = validate_proposal(
                proposal,
                writable_paths=writable_paths,
                allowed_import_roots=allowed_imports,
                maximum_bytes=maximum_bytes,
            )
            candidate_root = _candidate_copy(root)
            apply_files(candidate_root, files)
            candidate_evaluation = evaluate(candidate_root, quick=True)
            gain = candidate_evaluation.score - baseline.score
            review_payload = {
                "target_equations": target_labels,
                "proposal_summary": proposal.get("summary", ""),
                "expected_gain": proposal.get("expected_gain", ""),
                "risks": proposal.get("risks", []),
                "candidate_evaluation": asdict(candidate_evaluation),
                "files": [
                    {"path": path, "content": content[:18000]}
                    for path, content in files
                ],
            }
            review = local_model.json(
                REVIEW_SYSTEM_PROMPT,
                json.dumps(review_payload, ensure_ascii=False, indent=2),
            )
            review_approved = review.get("approved") is True
            if (
                candidate_evaluation.tests_passed
                and candidate_evaluation.simulation_passed
                and gain >= minimum_gain
                and review_approved
            ):
                accepted_files = files
                accepted_evaluation = candidate_evaluation
                break
            feedback = _summarize_failure(None, candidate_evaluation)
            if not review_approved:
                feedback += "\n\n独立复核未批准：" + json.dumps(review, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            error = exc
            feedback = _summarize_failure(exc, candidate_evaluation)
        finally:
            attempts.append(
                {
                    "round": round_number,
                    "accepted": accepted_files is not None,
                    "error": None if error is None else f"{type(error).__name__}: {error}",
                    "score": None if candidate_evaluation is None else candidate_evaluation.score,
                    "gain": None if candidate_evaluation is None else candidate_evaluation.score - baseline.score,
                    "summary": "" if proposal is None else str(proposal.get("summary", "")),
                    "review": review,
                }
            )
            if candidate_root is not None:
                shutil.rmtree(candidate_root.parent, ignore_errors=True)

    accepted = accepted_files is not None and accepted_evaluation is not None
    if accepted:
        apply_files(root, accepted_files or [])
        final_evaluation = evaluate(root, quick=True)
        implemented = set(state.get("implemented_equations", []))
        implemented.update(final_evaluation.equation_labels)
        state["implemented_equations"] = sorted(implemented, key=lambda value: tuple(map(int, value.split("."))))
        message = "候选代码通过测试、模拟和增益门槛，已接受。"
    else:
        final_evaluation = baseline
        message = "本轮候选未同时满足安全、测试、模拟和得分增益门槛，已全部回退。"

    record_cycle(
        state,
        accepted=accepted,
        score_before=baseline.score,
        score_after=final_evaluation.score,
        targets=target_labels,
        model=config["model"]["repository"],
        message=message,
    )
    save_state(state_path, state)
    write_evaluation(root / "state/latest_evaluation.json", final_evaluation)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accepted": accepted,
        "message": message,
        "targets": target_labels,
        "baseline": asdict(baseline),
        "final": asdict(final_evaluation),
        "attempts": attempts,
    }
    (root / "state/latest_cycle.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report
