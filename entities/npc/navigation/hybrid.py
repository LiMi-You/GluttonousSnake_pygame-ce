"""
entities/npc/navigation/hybrid.py — 混合策略

LootSnake 使用。大部分时间随机漫步，偶尔切换为贪心道具模式。
使用计时器控制模式切换频率。
"""
from __future__ import annotations
import random
from .base_strategy import NavigationStrategy, NavContext
from .obstacle_avoidance import ObstacleAvoidance


class HybridStrategy(NavigationStrategy):
    """混合：随机漫步 + 偶尔贪心道具"""

    GREEDY_CHANCE = 0.15     # 每步切换到贪心模式的概率
    DETECTION_RANGE = 10     # 贪心模式下的道具检测范围

    def __init__(self):
        self._greedy_mode: bool = False
        self._greedy_steps: int = 0
        self._max_greedy_steps: int = 8

    @property
    def strategy_name(self) -> str:
        return "Hybrid"

    def next_direction(self, ctx: NavContext) -> tuple[int, int]:
        snake = ctx.snake
        current_dir = snake.current_direction
        head = snake.head
        self_tag = f"npc:{snake.npc_type.npc_id}"

        # 模式切换
        if self._greedy_mode:
            self._greedy_steps += 1
            if self._greedy_steps >= self._max_greedy_steps:
                self._greedy_mode = False
        else:
            if random.random() < self.GREEDY_CHANCE:
                self._greedy_mode = True
                self._greedy_steps = 0
                self._max_greedy_steps = random.randint(5, 12)

        # 贪心模式：向最近道具移动
        if self._greedy_mode:
            nearest = self._find_nearest_item(head, ctx)
            if nearest is not None:
                preferred = ObstacleAvoidance.direction_toward(head, nearest)
                return ObstacleAvoidance.pick_best_direction(
                    head, snake.body, ctx.collision_mgr, current_dir,
                    self_tag=self_tag, preferred_dirs=preferred,
                )

        # 随机漫步模式
        if random.random() < 0.12:
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
        best_dist = self.DETECTION_RANGE + 1
        best_pos = None
        for item in ctx.items:
            if item.picked:
                continue
            ix, iy = int(item.fx), int(item.fy)
            dist = abs(head[0] - ix) + abs(head[1] - iy)
            if dist < best_dist:
                best_dist = dist
                best_pos = (ix, iy)
        return best_pos
