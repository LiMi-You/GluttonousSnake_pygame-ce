"""
entities/npc/navigation/wander.py — 大范围游走策略

MythicSnake 使用。保持当前方向长时间移动，遇障碍时偏转。
偶尔随机转向制造大范围游走效果。
"""
from __future__ import annotations
import random
from .base_strategy import NavigationStrategy, NavContext
from .obstacle_avoidance import ObstacleAvoidance


class WanderStrategy(NavigationStrategy):
    """大范围游走 + 障碍规避"""

    TURN_CHANCE = 0.08       # 每步随机转向概率（很低，保持大方向）
    DIRECTION_HOLD_MIN = 15  # 至少保持方向的最小步数

    def __init__(self):
        self._steps_in_direction: int = 0

    @property
    def strategy_name(self) -> str:
        return "Wander"

    def next_direction(self, ctx: NavContext) -> tuple[int, int]:
        snake = ctx.snake
        current_dir = snake.current_direction
        head = snake.head
        self_tag = f"npc:{snake.npc_type.npc_id}"
        self._steps_in_direction += 1

        # 长时间保持方向后，偶尔转向
        if self._steps_in_direction > self.DIRECTION_HOLD_MIN and random.random() < self.TURN_CHANCE:
            safe = ctx.collision_mgr.get_safe_directions(
                head, snake.body, current_dir, self_tag=self_tag,
            )
            if safe:
                chosen = random.choice(safe)
                if chosen != current_dir:
                    self._steps_in_direction = 0
                return chosen

        # 前瞻检测：如果前方即将被堵，提前转向
        lookahead = ObstacleAvoidance.lookahead_clear(
            head, current_dir, ctx.collision_mgr, steps=3,
        )
        if lookahead < 2:
            # 前方快堵了，转
            safe = ctx.collision_mgr.get_safe_directions(
                head, snake.body, current_dir, self_tag=self_tag,
            )
            if safe and len(safe) > 1:
                # 排除当前方向和反向，在剩余中随机选
                others = [d for d in safe
                          if d != current_dir and d != (-current_dir[0], -current_dir[1])]
                if others:
                    self._steps_in_direction = 0
                    return random.choice(others)

        return ObstacleAvoidance.pick_best_direction(
            head, snake.body, ctx.collision_mgr, current_dir,
            self_tag=self_tag,
        )
