"""
entities/npc/navigation/random_walk.py — 随机漫步策略

StandardSnake 使用。在安全方向中随机选择，偏好保持当前方向。
偶尔（~20%概率）随机转向增加变化。
"""
from __future__ import annotations
import random
from .base_strategy import NavigationStrategy, NavContext
from .obstacle_avoidance import ObstacleAvoidance


class RandomWalkStrategy(NavigationStrategy):
    """随机漫步 + 障碍规避"""

    TURN_CHANCE = 0.20  # 每步随机转向的概率

    @property
    def strategy_name(self) -> str:
        return "RandomWalk"

    def next_direction(self, ctx: NavContext) -> tuple[int, int]:
        snake = ctx.snake
        current_dir = snake.current_direction

        # 偶尔随机转向
        if random.random() < self.TURN_CHANCE:
            safe = ctx.collision_mgr.get_safe_directions(
                snake.head, snake.body, current_dir,
                self_tag=f"npc:{snake.npc_type.npc_id}",
            )
            if safe:
                return random.choice(safe)

        # 保持当前方向（如不安全则回退到安全方向中随机选）
        return ObstacleAvoidance.pick_best_direction(
            snake.head, snake.body, ctx.collision_mgr, current_dir,
            self_tag=f"npc:{snake.npc_type.npc_id}",
        )
