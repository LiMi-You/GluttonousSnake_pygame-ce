"""
items/difficulty_phases.py — 难度阶段系统

定义游戏各阶段的配置（分数门槛、允许的道具分类、权重倍率）。
支持通过 DifficultyPhaseOverrides 进行运行时覆盖。
"""
from dataclasses import dataclass, field
from .item_defs import ITEM_DEFS


@dataclass
class DifficultyPhase:
    """难度阶段定义"""
    min_score: int
    min_length: int
    allowed_categories: list[str]
    weight_multipliers: dict[str, float] = field(default_factory=dict)


@dataclass
class DifficultyPhaseOverrides:
    """难度阶段运行时覆盖（由调试面板控制）"""
    early_max_score: int = 100000
    early_categories: list[str] = field(default_factory=lambda: ["basic", "lucky"])
    mid_min_score: int = 100000
    mid_categories: list[str] = field(default_factory=lambda: ["basic", "lucky", "buff", "debuff", "obstacle"])
    late_min_length: int = 20
    late_categories: list[str] = field(default_factory=lambda: ["basic", "lucky", "buff", "debuff", "obstacle"])
    late_obstacle_mult: float = 1.5
    late_debuff_mult: float = 1.3


# ── 全局覆盖实例（由 DebugConfig 初始化）──
_phase_overrides: DifficultyPhaseOverrides | None = None


def set_phase_overrides(overrides: DifficultyPhaseOverrides):
    """设置全局阶段覆盖"""
    global _phase_overrides
    _phase_overrides = overrides


def get_phase_overrides() -> DifficultyPhaseOverrides:
    """获取当前阶段覆盖"""
    global _phase_overrides
    if _phase_overrides is None:
        _phase_overrides = DifficultyPhaseOverrides()
    return _phase_overrides


def _build_phases() -> list[DifficultyPhase]:
    """根据当前覆盖值构建阶段列表"""
    o = get_phase_overrides()
    return [
        DifficultyPhase(
            min_score=0, min_length=0,
            allowed_categories=list(o.early_categories),
        ),
        DifficultyPhase(
            min_score=o.mid_min_score, min_length=0,
            allowed_categories=list(o.mid_categories),
        ),
        DifficultyPhase(
            min_score=0, min_length=o.late_min_length,
            allowed_categories=list(o.late_categories),
            weight_multipliers={"obstacle": o.late_obstacle_mult, "debuff": o.late_debuff_mult},
        ),
    ]


# ── 查询函数 ────────────────────────────────────────


def get_active_phases(score: int, length: int) -> list[DifficultyPhase]:
    """返回当前满足条件的所有阶段（叠加模式）"""
    phases = _build_phases()
    active: list[DifficultyPhase] = []
    for phase in phases:
        if score >= phase.min_score and length >= phase.min_length:
            active.append(phase)
    return active


def get_allowed_categories(phases: list[DifficultyPhase]) -> set[str]:
    """从阶段列表合并出允许的道具分类集合"""
    categories: set[str] = set()
    for phase in phases:
        for cat in phase.allowed_categories:
            categories.add(cat)
    return categories


def merge_multipliers(phases: list[DifficultyPhase]) -> dict[str, float]:
    """合并所有阶段的权重倍率（同一分类乘法叠加）"""
    merged: dict[str, float] = {}
    for phase in phases:
        for cat, mult in phase.weight_multipliers.items():
            merged[cat] = merged.get(cat, 1.0) * mult
    return merged


def get_allowed_item_ids(allowed_categories: set[str]) -> list[str]:
    """从允许的分类集合反查道具 ID 列表"""
    return [
        item_id
        for item_id, defn in ITEM_DEFS.items()
        if defn.category in allowed_categories
    ]
