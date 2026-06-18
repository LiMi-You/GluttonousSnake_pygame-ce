"""
items/difficulty_phases.py — 难度阶段系统

定义游戏各阶段的配置（分数门槛、允许的道具分类、权重倍率）。
所有数值可在测试后调整，逻辑与数据分离。
"""
from dataclasses import dataclass, field
from .item_defs import ITEM_DEFS


@dataclass
class DifficultyPhase:
    """难度阶段定义"""
    min_score: int                         # 进入该阶段的最低分数
    min_length: int                        # 进入该阶段的最低蛇长
    allowed_categories: list[str]          # 允许生成的道具分类列表
    weight_multipliers: dict[str, float]   # 分类 → 权重倍率（乘法叠加）


# ── 阶段配置表 ──────────────────────────────────────
# 叠加模式：所有满足条件的阶段同时生效
#   - pool = 各阶段 allowed_categories 的并集
#   - weight_multipliers = 各阶段的乘法叠加

PHASES: list[DifficultyPhase] = [
    # ── 前期：分数 < 100000 ──
    # 只允许基础食物 + 幸运食物
    # （幸运食物在 calc_score_modifier 中已被压制到 0.1 倍，
    #   这里不需要额外 weight_multiplier）
    DifficultyPhase(
        min_score=0,
        min_length=0,
        allowed_categories=["basic", "lucky"],
        weight_multipliers={},
    ),
    # ── 中期：分数 >= 100000 ──
    # 解锁全部道具类型，幸运食物恢复正常权重
    # （叠加模式下，pool 取并集，自动扩展到全类型）
    DifficultyPhase(
        min_score=100000,
        min_length=0,
        allowed_categories=["basic", "lucky", "buff", "debuff", "obstacle"],
        weight_multipliers={},
    ),
    # ── 后期：蛇长 >= 20 ──
    # 全类型 + 障碍物/减益权重提升（蛇长后空间宝贵，增加挑战性）
    DifficultyPhase(
        min_score=0,
        min_length=20,
        allowed_categories=["basic", "lucky", "buff", "debuff", "obstacle"],
        weight_multipliers={"obstacle": 1.5, "debuff": 1.3},
    ),
]


# ── 查询函数 ────────────────────────────────────────


def get_active_phases(score: int, length: int) -> list[DifficultyPhase]:
    """返回当前满足条件的所有阶段（叠加模式）"""
    active: list[DifficultyPhase] = []
    for phase in PHASES:
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
