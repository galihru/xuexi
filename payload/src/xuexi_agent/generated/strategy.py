"""学习代理生成的模拟策略。

该初始版本保持参数不变。后续代理周期只能在安全验证通过后更新本文件。
"""

from __future__ import annotations

from typing import Any


def mutate_parameters(parameters: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """返回经过代理审查的模拟参数。"""
    return dict(parameters)


def research_hypotheses(context: dict[str, Any]) -> list[dict[str, Any]]:
    """返回需要由数值实验检验的假设。"""
    return []
