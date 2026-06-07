"""
entities/npc/navigation/obstacle_avoidance.py — 障碍规避组件

为所有导航策略提供共享的障碍检测和方向过滤能力。
不单独作为策略使用，而是被其他策略组合调用。
"""
from __future__ import annotations
import random
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from entities.npc.collision_manager import CollisionManager

# 四个基本方向 + 空方向
CARDINALS: list[tuple[int, int]] = [(0, -1), (0, 1), (-1, 0), (1, 0)]


class ObstacleAvoidance:
    """
    障碍规避组件 — 被导航策略组合使用。

    提供：
    - 过滤掉前方有障碍的方向
    - 对剩余方向按优先级排序（当前方向 > 左右偏转 > 反向）
    - 前瞻检测（看前方N格是否畅通）
    """

    # 前瞻格数
    LOOKAHEAD = 3

    @staticmethod
    def filter_safe_directions(
        head: tuple[int, int],
        body: list[tuple[int, int]],
        collision_mgr: 'CollisionManager',
        current_dir: tuple[int, int],
        self_tag: Optional[str] = None,
    ) -> list[tuple[int, int]]:
        """
        返回所有安全的移动方向（排除反向和会导致碰撞的方向）。

        直接委托给 CollisionManager.get_safe_directions()。
        """
        return collision_mgr.get_safe_directions(
            head, body, current_dir, self_tag=self_tag,
        )

    @classmethod
    def pick_best_direction(
        cls,
        head: tuple[int, int],
        body: list[tuple[int, int]],
        collision_mgr: 'CollisionManager',
        current_dir: tuple[int, int],
        *,
        self_tag: Optional[str] = None,
        preferred_dirs: Optional[list[tuple[int, int]]] = None,
    ) -> tuple[int, int]:
        """
        从安全方向中选出最优方向。

        优先级：
        1. preferred_dirs 中第一个同时安全的（如朝向道具、朝向玩家）
        2. 当前方向（如果安全）
        3. 随机安全方向
        4. 反向（最后手段）
        """
        safe = collision_mgr.get_safe_directions(
            head, body, current_dir, self_tag=self_tag,
        )

        if not safe:
            # 绝境：返回反向
            return (-current_dir[0], -current_dir[1])

        # 优先：preferred_dirs 中第一个安全的
        if preferred_dirs:
            for d in preferred_dirs:
                if d in safe:
                    return d

        # 次选：保持当前方向
        if current_dir in safe:
            return current_dir

        # 再次：随机选一个安全的
        return random.choice(safe)

    @classmethod
    def lookahead_clear(
        cls,
        head: tuple[int, int],
        direction: tuple[int, int],
        collision_mgr: 'CollisionManager',
        steps: int = None,
    ) -> int:
        """
        前瞻检测：沿 direction 方向，连续多少格是畅通的。

        返回连续空闲格数（0 表示第一格就被阻挡）。
        """
        if steps is None:
            steps = cls.LOOKAHEAD
        count = 0
        hx, hy = head
        dx, dy = direction
        for i in range(1, steps + 1):
            nx, ny = hx + dx * i, hy + dy * i
            if collision_mgr.is_free(nx, ny):
                count += 1
            else:
                break
        return count

    @classmethod
    def direction_toward(
        cls,
        head: tuple[int, int],
        target: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """
        返回从 head 指向 target 的偏好方向列表（按优先级排序）。

        先对齐较远轴，再对齐较近轴。
        例如：head=(5,5), target=(10,8) → 优先右，其次下
        """
        dx = target[0] - head[0]
        dy = target[1] - head[1]

        result = []
        if abs(dx) >= abs(dy):
            # 水平轴更远，优先水平
            result.append((1 if dx > 0 else -1, 0))
            if dy != 0:
                result.append((0, 1 if dy > 0 else -1))
        else:
            # 垂直轴更远，优先垂直
            result.append((0, 1 if dy > 0 else -1))
            if dx != 0:
                result.append((1 if dx > 0 else -1, 0))
        return result
