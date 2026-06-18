"""
entities/npc/navigation/chase_player.py — 追击玩家策略

HunterSnake 使用。BFS最短路径寻路，追踪玩家蛇头。
缓存路径，仅在目标移动或路径被阻断时重新计算。
"""
from __future__ import annotations
from collections import deque
from .base_strategy import NavigationStrategy, NavContext
from .obstacle_avoidance import ObstacleAvoidance

CARDINALS: list[tuple[int, int]] = [(0, -1), (0, 1), (-1, 0), (1, 0)]


class ChasePlayerStrategy(NavigationStrategy):
    """BFS追击玩家 + 障碍规避"""

    RECALC_INTERVAL = 3       # 每N步重新计算路径
    MAX_PATH_LENGTH = 40      # BFS最大搜索深度

    def __init__(self):
        self._cached_path: list[tuple[int, int]] = []
        self._step_counter: int = 0
        self._last_player_pos: tuple[int, int] | None = None

    @property
    def strategy_name(self) -> str:
        return "ChasePlayer"

    def next_direction(self, ctx: NavContext) -> tuple[int, int]:
        snake = ctx.snake
        current_dir = snake.current_direction
        head = snake.head
        self_tag = f"npc:{snake.npc_type.npc_id}"
        self._step_counter += 1

        player_pos = ctx.player_head

        # BFS寻路到玩家
        if player_pos:
            need_recalc = (
                self._step_counter % self.RECALC_INTERVAL == 0 or
                not self._cached_path or
                player_pos != self._last_player_pos or
                not self._is_path_valid(head)
            )
            if need_recalc:
                self._cached_path = self._bfs(head, player_pos, ctx)
                self._last_player_pos = player_pos

            # 沿路径走
            if self._cached_path and len(self._cached_path) >= 2:
                next_cell = self._cached_path[1]
                preferred = [(next_cell[0] - head[0], next_cell[1] - head[1])]
                return ObstacleAvoidance.pick_best_direction(
                    head, snake.body, ctx.collision_mgr, current_dir,
                    self_tag=self_tag, preferred_dirs=preferred,
                )

        # 没有路径或没有玩家位置 → 随机漫步
        return ObstacleAvoidance.pick_best_direction(
            head, snake.body, ctx.collision_mgr, current_dir,
            self_tag=self_tag,
        )

    def _is_path_valid(self, head: tuple[int, int]) -> bool:
        """检查缓存路径是否仍然有效（当前头是否在路径起点附近）"""
        if not self._cached_path:
            return False
        return head == self._cached_path[0]

    def _bfs(
        self, start: tuple[int, int], goal: tuple[int, int], ctx: NavContext,
    ) -> list[tuple[int, int]]:
        """
        BFS搜索从 start 到 goal 的最短路径。
        避开占据图中有实体的格子，但允许经过目标（玩家头）。
        """
        if start == goal:
            return [start]

        queue = deque()
        queue.append(start)
        visited: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

        while queue:
            current = queue.popleft()

            # 深度限制
            path_len = 0
            node = current
            while node is not None:
                path_len += 1
                node = visited[node]
            if path_len > self.MAX_PATH_LENGTH:
                break

            for dx, dy in CARDINALS:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)

                if neighbor in visited:
                    continue

                # 目标格允许（即使被占据）
                if neighbor == goal:
                    # 重建路径
                    path = [neighbor]
                    node = current
                    while node is not None:
                        path.append(node)
                        node = visited[node]
                    path.reverse()
                    return path

                # 非目标格必须空闲
                if ctx.collision_mgr.is_free(nx, ny):
                    visited[neighbor] = current
                    queue.append(neighbor)

        return []  # 无路径
