"""
entities/npc/spawn_manager.py — NPC出生管理器

核心职责：
1. 在网格上查找安全的出生位置（安全区域选址）
2. 渐进式出生：只创建蛇头，交由 NPCSnake.UNFOLDING 状态逐步拉长身体
3. 确保蛇头有至少 1~2 格初始移动空间

选址策略：
- 扫描网格，寻找附近无障碍物、无玩家蛇身、无其他NPC蛇身的空白格
- 验证候选点的四个方向中至少 2 个方向有足够的移动空间
- 优先选择远离玩家和障碍物的位置
- 若严格条件无法满足，逐步放宽约束
"""
from __future__ import annotations
import random
from typing import Optional

from settings import GRID_WIDTH, GRID_HEIGHT
from .npc_base import NPCSnake
from .npc_types import NPCTypeDef


# ── 方向向量（上下左右）──────────────────────────
CARDINAL_DIRECTIONS: list[tuple[int, int]] = [
    (0, -1),   # 上
    (0, 1),    # 下
    (-1, 0),   # 左
    (1, 0),    # 右
]


class SpawnManager:
    """NPC出生管理器 — 安全选址 + 渐进式创建"""

    # 选址参数
    MAX_SPAWN_ATTEMPTS: int = 200       # 最大选址尝试次数
    MIN_CLEAR_DIRECTIONS: int = 2       # 最少需要的畅通方向数
    MIN_CLEARANCE_PER_DIR: int = 2      # 每个方向至少需要多少空闲格
    SAFE_ZONE_MARGIN: int = 3           # 安全区域额外边距

    def __init__(self):
        self._rng = random.Random()

    # ── 公开接口 ──

    def try_spawn(
        self,
        npc_type: NPCTypeDef,
        player_body: list[tuple[int, int]],
        npc_bodies: list[list[tuple[int, int]]],
        obstacles: Optional[set[tuple[int, int]]] = None,
    ) -> Optional[NPCSnake]:
        """
        尝试在安全位置创建一个NPC蛇实例。

        参数：
            npc_type:   NPC类型配置
            player_body: 玩家蛇身坐标列表
            npc_bodies:  所有已存在NPC蛇身列表的列表
            obstacles:   额外障碍物坐标集（可选）

        返回：
            成功则返回 NPCSnake 实例（处于 UNFOLDING 状态），失败返回 None。
        """
        # 随机目标长度
        target_length = self._rng.randint(npc_type.min_length, npc_type.max_length)

        # 构建全局占据集
        occupied = self._build_occupied_set(player_body, npc_bodies, obstacles)

        # 选址
        result = self._find_safe_position(target_length, occupied)
        if result is None:
            return None

        head_pos, direction = result

        # 创建NPC蛇实例（渐进式出生：仅蛇头）
        npc = NPCSnake(
            npc_type=npc_type,
            head_pos=head_pos,
            direction=direction,
            target_length=target_length,
        )
        return npc

    # ── 占据集构建 ──

    def _build_occupied_set(
        self,
        player_body: list[tuple[int, int]],
        npc_bodies: list[list[tuple[int, int]]],
        obstacles: Optional[set[tuple[int, int]]] = None,
    ) -> set[tuple[int, int]]:
        """构建全局不可用坐标集合"""
        occupied: set[tuple[int, int]] = set()

        # 玩家蛇身
        for cell in player_body:
            # 玩家蛇身可能在网格外（撞墙判定之前），过滤掉越界坐标
            if 0 <= cell[0] < GRID_WIDTH and 0 <= cell[1] < GRID_HEIGHT:
                occupied.add(cell)

        # 其他NPC蛇身
        for body in npc_bodies:
            for cell in body:
                if 0 <= cell[0] < GRID_WIDTH and 0 <= cell[1] < GRID_HEIGHT:
                    occupied.add(cell)

        # 额外障碍物
        if obstacles:
            for cell in obstacles:
                if 0 <= cell[0] < GRID_WIDTH and 0 <= cell[1] < GRID_HEIGHT:
                    occupied.add(cell)

        return occupied

    # ── 安全选址核心 ──

    def _find_safe_position(
        self,
        target_length: int,
        occupied: set[tuple[int, int]],
    ) -> Optional[tuple[tuple[int, int], tuple[int, int]]]:
        """
        查找安全的出生位置。

        算法：
        1. 随机采样候选点
        2. 对每个候选点验证：
           a. 该点未被占据
           b. 至少 MIN_CLEAR_DIRECTIONS 个方向有 MIN_CLEARANCE_PER_DIR 格空闲
           c. 周围安全区域内的占用率不超过阈值
        3. 若找到，选择一个指向空旷区域的方向

        返回 (head_pos, direction) 或 None。
        """
        # 计算安全检测半径（基于目标蛇长）
        safe_radius = max(target_length // 2 + self.SAFE_ZONE_MARGIN, 4)

        best_candidates: list[tuple[tuple[int, int], tuple[int, int], int]] = []
        # (head_pos, direction, score) — score越高越好

        for _ in range(self.MAX_SPAWN_ATTEMPTS):
            gx = self._rng.randint(0, GRID_WIDTH - 1)
            gy = self._rng.randint(0, GRID_HEIGHT - 1)

            if (gx, gy) in occupied:
                continue

            # 验证方向畅通性
            clear_directions = self._get_clear_directions(gx, gy, occupied)
            if len(clear_directions) < self.MIN_CLEAR_DIRECTIONS:
                continue

            # 验证安全区域内占用率
            occupancy_rate = self._calc_zone_occupancy(gx, gy, safe_radius, occupied)
            if occupancy_rate > 0.35:  # 周围超过35%被占据则放弃
                continue

            # 对每个畅通方向评分，选最佳
            for direction in clear_directions:
                score = self._score_direction(gx, gy, direction, occupied, player_head=None)
                best_candidates.append(((gx, gy), direction, score))

        if not best_candidates:
            return None

        # 按评分降序排列，取最高分
        best_candidates.sort(key=lambda x: x[2], reverse=True)
        head_pos, direction, _ = best_candidates[0]
        return head_pos, direction

    # ── 方向畅通性检测 ──

    def _get_clear_directions(
        self, gx: int, gy: int, occupied: set[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """
        返回从 (gx, gy) 出发，至少 MIN_CLEARANCE_PER_DIR 格内无阻碍的方向列表。
        """
        clear = []
        for dx, dy in CARDINAL_DIRECTIONS:
            blocked = False
            for step in range(1, self.MIN_CLEARANCE_PER_DIR + 1):
                nx, ny = gx + dx * step, gy + dy * step
                # 越界也算阻碍
                if not (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT):
                    blocked = True
                    break
                if (nx, ny) in occupied:
                    blocked = True
                    break
            if not blocked:
                clear.append((dx, dy))
        return clear

    # ── 区域占用率计算 ──

    def _calc_zone_occupancy(
        self, cx: int, cy: int, radius: int, occupied: set[tuple[int, int]],
    ) -> float:
        """
        计算以 (cx, cy) 为中心、radius 为半径的方形区域内，
        被占据格子的比例。
        """
        x0 = max(0, cx - radius)
        y0 = max(0, cy - radius)
        x1 = min(GRID_WIDTH - 1, cx + radius)
        y1 = min(GRID_HEIGHT - 1, cy + radius)

        total = (x1 - x0 + 1) * (y1 - y0 + 1)
        if total == 0:
            return 1.0

        occupied_count = sum(
            1 for x in range(x0, x1 + 1)
            for y in range(y0, y1 + 1)
            if (x, y) in occupied
        )
        return occupied_count / total

    # ── 方向评分 ──

    def _score_direction(
        self,
        gx: int, gy: int,
        direction: tuple[int, int],
        occupied: set[tuple[int, int]],
        player_head: Optional[tuple[int, int]] = None,
    ) -> int:
        """
        对候选方向打分。分数越高越优。

        评分规则：
        - 沿该方向连续空闲格数越多，分越高（上限 8 格）
        - 方向指向地图边缘扣分
        - （可选）方向远离玩家加分
        """
        dx, dy = direction
        score = 0

        # 连续空闲格数
        free_steps = 0
        for step in range(1, 9):  # 最多看 8 格
            nx, ny = gx + dx * step, gy + dy * step
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if (nx, ny) not in occupied:
                    free_steps += 1
                else:
                    break
            else:
                break
        score += free_steps * 10  # 每格 10 分

        # 远离玩家（如果提供了玩家蛇头位置）
        if player_head:
            px, py = player_head
            dist_before = abs(gx - px) + abs(gy - py)
            dist_after = abs(gx + dx - px) + abs(gy + dy - py)
            if dist_after > dist_before:
                score += 20  # 远离玩家加分

        return score
