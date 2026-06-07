"""
entities/npc/navigation/greedy_item.py — 贪心道具策略

ForagingSnake 使用。扫描场上道具，向最近的可达道具移动。
检测范围内无道具时回退为随机漫步。
"""
from __future__ import annotations
import random
from .base_strategy import NavigationStrategy, NavContext
from .obstacle_avoidance import ObstacleAvoidance


class GreedyItemStrategy(NavigationStrategy):
    """贪心道具采集 + 障碍规避"""

    DETECTION_RANGE = 12  # 道具检测范围（曼哈顿距离）

    @property
    def strategy_name(self) -> str:
        return "GreedyItem"

    def next_direction(self, ctx: NavContext) -> tuple[int, int]:
        snake = ctx.snake
        current_dir = snake.current_direction
        head = snake.head
        self_tag = f"npc:{snake.npc_type.npc_id}"

        # 扫描最近道具
        nearest = self._find_nearest_item(head, ctx)
        if nearest is not None:
            # 计算朝向道具的偏好方向
            preferred = ObstacleAvoidance.direction_toward(head, nearest)
            return ObstacleAvoidance.pick_best_direction(
                head, snake.body, ctx.collision_mgr, current_dir,
                self_tag=self_tag, preferred_dirs=preferred,
            )

        # 没有道具在检测范围内 → 随机漫步
        if random.random() < 0.15:
            safe = ctx.collision_mgr.get_safe_directions(
                head, snake.body, current_dir, self_tag=self_tag,
            )
            if safe:
                return random.choice(safe)

        return ObstacleAvoidance.pick_best_direction(
            head, snake.body, ctx.collision_mgr, current_dir,
            self_tag=self_tag,
        )

    def _find_nearest_item(self, head, ctx):
        """找到曼哈顿距离最近的道具位置，返回其网格坐标或None"""
        best_dist = self.DETECTION_RANGE + 1
        best_pos = None
        for item in ctx.items:
            if item.picked:
                continue
            # 道具中心网格坐标
            ix = int(item.fx)
            iy = int(item.fy)
            dist = abs(head[0] - ix) + abs(head[1] - iy)
            if dist < best_dist:
                best_dist = dist
                best_pos = (ix, iy)
        return best_pos
