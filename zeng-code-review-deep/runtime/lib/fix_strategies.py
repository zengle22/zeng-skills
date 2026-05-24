"""Fix strategy classification and validation."""

from __future__ import annotations

from enum import Enum


class FixStrategy(str, Enum):
    """Supported fix strategies per ADR-058 §3.5.2."""

    MINIMAL_CHANGE = "MINIMAL_CHANGE"
    REFACTOR = "REFACTOR"
    ADD_TEST = "ADD_TEST"
    UPDATE_CONTRACT = "UPDATE_CONTRACT"
    REMOVE_CODE = "REMOVE_CODE"

    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in {m.value for m in cls}


STRATEGY_DESCRIPTIONS = {
    FixStrategy.MINIMAL_CHANGE: "最小范围修改（加 guard、改判断条件）",
    FixStrategy.REFACTOR: "结构调整（提取函数、重命名、简化复杂度）",
    FixStrategy.ADD_TEST: "补充测试用例",
    FixStrategy.UPDATE_CONTRACT: "更新 API 文档、DTO、类型定义",
    FixStrategy.REMOVE_CODE: "删除死代码、重复实现、调试代码",
}


def classify_strategy(severity: str, dimension: str, description: str) -> FixStrategy:
    """Heuristic strategy classifier based on issue attributes.

    This is a rule-based fallback when the fix-planner agent does not
    provide an explicit strategy. It should not replace the agent's
    judgment for complex cases.
    """
    desc_lower = description.lower()
    dim_lower = dimension.lower()

    if "test" in dim_lower or "coverage" in desc_lower:
        return FixStrategy.ADD_TEST
    if "dto" in dim_lower or "contract" in dim_lower or "api" in dim_lower:
        return FixStrategy.UPDATE_CONTRACT
    if "orphaned" in desc_lower or "dead code" in desc_lower or "debug" in desc_lower:
        return FixStrategy.REMOVE_CODE
    if severity == "P0" and ("boundary" in desc_lower or "null" in desc_lower or "zero" in desc_lower):
        return FixStrategy.MINIMAL_CHANGE
    if severity == "P1" and ("complexity" in desc_lower or "extract" in desc_lower):
        return FixStrategy.REFACTOR
    if severity in {"P0", "P1"}:
        return FixStrategy.MINIMAL_CHANGE
    return FixStrategy.REMOVE_CODE
