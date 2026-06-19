"""
items/movement.py — 新移动引擎

轴锁定为核心的移动系统，支持：
- 轴锁定移动（X或Y轴，范围限制或全场）
- 全场自由移动+边界反弹
- 范围内自由移动+随机换向

与旧系统 _update_moving_items() 功能等价，但架构更清晰。
"""
import math
from settings import GRID_WIDTH, GRID_HEIGHT, MOVE_ITEM_BASE_SPEED


def update_moving_items(items: list, dt_ms: int):
    """每帧更新所有可移动道具的位置"""
    if dt_ms <= 0:
        return

    fps_normal = dt_ms / (1000.0 / 25.0)

    for item in items:
        if not item.defn.is_moving or item.picked:
            continue

        speed = item.defn.move_speed * MOVE_ITEM_BASE_SPEED * fps_normal
        dx, dy = item.move_dir

        item.fx += dx * speed
        item.fy += dy * speed

        _apply_boundary(item, dx, dy)


def _apply_boundary(item, dx: float, dy: float):
    """根据道具配置应用边界约束"""
    axis = item.defn.move_axis_lock
    move_range = item.defn.move_range

    if axis:
        _handle_axis_lock(item, dx, dy, axis, move_range)
    elif move_range > 0:
        _handle_range_free(item, move_range)
    elif item.defn.move_bounce:
        _handle_full_bounce(item)


def _handle_axis_lock(item, dx: float, dy: float, axis: str, move_range: int):
    """轴锁定模式：沿单一轴移动，碰边界反转"""
    if move_range > 0:
        half = move_range / 2.0
        if axis == "x":
            x_min = item.spawn_origin[0] - half
            x_max = item.spawn_origin[0] + half
            if item.fx < x_min or item.fx >= x_max:
                item.move_dir = (-dx, 0)
                item.fx = max(x_min, min(x_max - 0.01, item.fx))
        else:
            y_min = item.spawn_origin[1] - half
            y_max = item.spawn_origin[1] + half
            if item.fy < y_min or item.fy >= y_max:
                item.move_dir = (0, -dy)
                item.fy = max(y_min, min(y_max - 0.01, item.fy))
    else:
        if axis == "x":
            if item.fx < 0:
                item.move_dir = (abs(dx), 0)
                item.fx = 0
            elif item.fx >= GRID_WIDTH:
                item.move_dir = (-abs(dx), 0)
                item.fx = GRID_WIDTH - 0.01
        else:
            if item.fy < 0:
                item.move_dir = (0, abs(dy))
                item.fy = 0
            elif item.fy >= GRID_HEIGHT:
                item.move_dir = (0, -abs(dy))
                item.fy = GRID_HEIGHT - 0.01


def _handle_range_free(item, move_range: int):
    """范围内自由移动：碰边界随机换方向"""
    half = move_range / 2.0
    dx = item.fx - item.spawn_origin[0]
    dy = item.fy - item.spawn_origin[1]
    dist_sq = dx * dx + dy * dy

    if dist_sq > half * half:
        import random
        angle = random.uniform(0, 2 * math.pi)
        item.move_dir = (math.cos(angle), math.sin(angle))
        item.fx = max(
            item.spawn_origin[0] - half,
            min(item.spawn_origin[0] + half, item.fx),
        )
        item.fy = max(
            item.spawn_origin[1] - half,
            min(item.spawn_origin[1] + half, item.fy),
        )


def _handle_full_bounce(item):
    """全场移动：碰地图边界反弹"""
    if item.fx < 0:
        item.move_dir = (-item.move_dir[0], item.move_dir[1])
        item.fx = 0
    elif item.fx >= GRID_WIDTH:
        item.move_dir = (-item.move_dir[0], item.move_dir[1])
        item.fx = GRID_WIDTH - 0.01
    if item.fy < 0:
        item.move_dir = (item.move_dir[0], -item.move_dir[1])
        item.fy = 0
    elif item.fy >= GRID_HEIGHT:
        item.move_dir = (item.move_dir[0], -item.move_dir[1])
        item.fy = GRID_HEIGHT - 0.01
