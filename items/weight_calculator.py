"""
items/weight_calculator.py — 动态权重计算引擎

核心职责：
1. 根据当前游戏状态动态计算每个道具类型的实际权重
2. 提供加权随机选择函数
3. 所有修正因子集中管理，方便调参
"""
import random
from typing import Optional

from .item_defs import CAT_BASIC, CAT_LUCKY, CAT_BUFF, CAT_DEBUFF, CAT_OBSTACLE


# ── 修正因子：场上数量压制 ──────────────────────────


def calc_screen_count_modifier(current_count: int, max_count: int) -> float:
    """
    当前数量越接近上限，权重越低（平方衰减）。
    
    公式: 1.0 - (current / max)²
    例: 0/4 → 1.0,  2/4 → 0.75,  3/4 → 0.4375,  4/4 → 0.0
    """
    if max_count <= 0:
        return 0.0
    ratio = current_count / max_count
    return 1.0 - (ratio * ratio)


# ── 修正因子：蛇长 ──────────────────────────────────

# 默认系数（可由 WeightConfig 覆盖）
_len_obstacle_coeff = 0.05
_len_debuff_coeff = 0.05
_len_lucky_coeff = -0.02


def set_length_coefficients(obstacle: float, debuff: float, lucky: float):
    """设置蛇长因子系数"""
    global _len_obstacle_coeff, _len_debuff_coeff, _len_lucky_coeff
    _len_obstacle_coeff = obstacle
    _len_debuff_coeff = debuff
    _len_lucky_coeff = lucky


def calc_length_modifier(category: str, snake_length: int) -> float:
    """
    蛇长因子：障碍物/减益类随蛇长增加权重，幸运类降低。
    """
    length_factor = max(0, snake_length - 3)
    if category in (CAT_OBSTACLE, CAT_DEBUFF):
        coeff = _len_obstacle_coeff if category == CAT_OBSTACLE else _len_debuff_coeff
        return 1.0 + length_factor * coeff
    elif category == CAT_LUCKY:
        return max(0.5, 1.0 + length_factor * _len_lucky_coeff)
    return 1.0


# ── 修正因子：分数 ──────────────────────────────────

_score_suppress_factor = 0.1


def set_score_suppress_factor(factor: float):
    """设置分数压制因子"""
    global _score_suppress_factor
    _score_suppress_factor = factor


def calc_score_modifier(category: str, score: int, early_max_score: int) -> float:
    """
    分数因子：稀有类（幸运/增益）在达到分数阈值后权重逐步提升。
    """
    if category in (CAT_LUCKY, CAT_BUFF):
        if score < early_max_score:
            return _score_suppress_factor
        return min(2.0, _score_suppress_factor + (score - early_max_score) / early_max_score)
    return 1.0


# ── 权重表构建 ──────────────────────────────────────


def build_weight_table(
    allowed_item_ids: list[str],
    snake_length: int,
    score: int,
    current_counts: dict[str, int],
    phase_multipliers: dict[str, float],
    early_max_score: int,
    item_defs: dict,
    weight_overrides: dict[str, int] | None = None,
    enabled_overrides: dict[str, bool] | None = None,
) -> dict[str, int]:
    """
    根据当前游戏状态，构建所有允许道具的"实际权重"表。
    
    参数：
        allowed_item_ids:  当前阶段允许生成的道具 ID 列表
        snake_length:      当前蛇长
        score:             当前分数
        current_counts:    场上各道具现有数量 {item_id: count}
        phase_multipliers: 阶段倍率表 {category: multiplier}
        early_max_score:   前期分数上限（来自 settings）
        item_defs:         道具定义注册表 {item_id: ItemDef}
    
    返回：
        {item_id: effective_weight}  权重 ≤ 0 的条目会被调用方过滤
    """
    weight_table: dict[str, int] = {}

    for item_id in allowed_item_ids:
        defn = item_defs.get(item_id)
        if defn is None:
            continue

        # 检查启用开关
        if enabled_overrides and enabled_overrides.get(item_id, True) is False:
            continue

        # 1. 基础权重（支持覆盖）
        if weight_overrides and item_id in weight_overrides:
            w = float(weight_overrides[item_id])
        else:
            w = float(defn.base_weight)
        if w <= 0:
            continue

        # 2. 场上数量压制
        count = current_counts.get(item_id, 0)
        w *= calc_screen_count_modifier(count, defn.max_on_screen)
        if w <= 0:
            continue

        # 3. 蛇长因子
        w *= calc_length_modifier(defn.category, snake_length)

        # 4. 分数因子
        w *= calc_score_modifier(defn.category, score, early_max_score)

        # 5. 阶段分类倍率
        cat_mult = phase_multipliers.get(defn.category, 1.0)
        w *= cat_mult

        # 取整，最低为 0
        effective = max(0, int(round(w)))
        if effective > 0:
            weight_table[item_id] = effective

    return weight_table


# ── 加权随机选择 ────────────────────────────────────


def pick_item_by_weight(weight_table: dict[str, int]) -> Optional[str]:
    """
    按权重表加权随机选取一个道具 ID。
    权重越高，被选中的概率越大。
    
    算法：轮盘赌（累积分布函数）
    """
    total = sum(weight_table.values())
    if total <= 0:
        return None

    roll = random.randint(1, total)
    cumulative = 0
    for item_id, weight in weight_table.items():
        cumulative += weight
        if roll <= cumulative:
            return item_id

    return None  # 不应到达这里
