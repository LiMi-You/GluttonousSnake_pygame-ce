"""
utils/helpers.py — 通用工具函数

包含 12 方向向量表（钟表方向）、随机方向选取等功能。
"""
import math
import random

# ── 12 方向向量表（钟表方向）─────────────────────────
# 360° 等分 12 份，每份 30°
# 索引  0 → 0°(右),  3 → 90°(下),  6 → 180°(左),  9 → 270°(上)
# 注意: pygame 坐标系 y 轴向下，sin 正值 = 向下

CLOCK_DIRECTIONS: list[tuple[float, float]] = [
    (math.cos(math.radians(i * 30)), math.sin(math.radians(i * 30)))
    for i in range(12)
]
# 手动展开以明确每个方向：
#  0: ( 1.000,  0.000) → 右
#  1: ( 0.866,  0.500) → 右下
#  2: ( 0.500,  0.866) → 右下
#  3: ( 0.000,  1.000) → 下
#  4: (-0.500,  0.866) → 左下
#  5: (-0.866,  0.500) → 左下
#  6: (-1.000,  0.000) → 左
#  7: (-0.866, -0.500) → 左上
#  8: (-0.500, -0.866) → 左上
#  9: ( 0.000, -1.000) → 上
# 10: ( 0.500, -0.866) → 右上
# 11: ( 0.866, -0.500) → 右上

NUM_DIRECTIONS = len(CLOCK_DIRECTIONS)


def get_random_direction() -> tuple[tuple[float, float], int]:
    """返回一个随机方向向量及其索引"""
    idx = random.randint(0, NUM_DIRECTIONS - 1)
    return CLOCK_DIRECTIONS[idx], idx


def get_new_direction(current_idx: int) -> tuple[tuple[float, float], int]:
    """
    返回一个与当前方向不同的随机方向。
    避免撞墙后随机到同一方向导致连续反弹。
    """
    idx = random.randint(0, NUM_DIRECTIONS - 1)

    # 如果只有 1 个方向可选（12>1，实际上不会），直接返回
    if NUM_DIRECTIONS <= 1:
        return CLOCK_DIRECTIONS[idx], idx

    # 避免与当前相同
    while idx == current_idx:
        idx = random.randint(0, NUM_DIRECTIONS - 1)

    return CLOCK_DIRECTIONS[idx], idx


def is_within_range(
    fx: float, fy: float,
    origin_x: float, origin_y: float,
    move_range: int,
) -> bool:
    """
    判断道具当前位置是否在允许的移动范围内。
    使用圆形范围判断（原点为中心，move_range/2 为半径）。
    """
    half_range = move_range / 2.0
    dx = fx - origin_x
    dy = fy - origin_y
    return (dx * dx + dy * dy) <= (half_range * half_range)
