"""
entities/npc/npc_base.py — NPC蛇实体基类

NPCSnake 封装了NPC蛇的所有数据与行为：
- 蛇身坐标列表（网格坐标系）
- 方向控制（AI驱动）
- 渐进式出生展开（UNFOLDING → ACTIVE）
- 移动、增长、碰撞检测
- 邻居感知的边框渲染（支持自定义颜色）
"""
from __future__ import annotations
import random
import pygame
from typing import Optional

from settings import (
    CELL_SIZE, MARGIN_LEFT, MARGIN_TOP,
    SNAKE_BORDER_WIDTH, GRID_WIDTH, GRID_HEIGHT,
)
from .npc_types import NPCTypeDef, SpawnState, NavStrategy


class NPCSnake:
    """NPC蛇实体：管理蛇身数据、方向、移动、渲染与AI行为"""

    def __init__(self, npc_type: NPCTypeDef, head_pos: tuple[int, int],
                 direction: tuple[int, int], target_length: int):
        """
        创建NPC蛇实例。

        参数：
            npc_type:      NPC类型配置
            head_pos:      初始蛇头位置（网格坐标，由SpawnManager选址后传入）
            direction:     初始移动方向
            target_length: 目标最终长度（在min_length~max_length之间随机）
        """
        self.npc_type: NPCTypeDef = npc_type
        self.target_length: int = target_length

        # ── 蛇身：渐进式出生 —— 初始只有蛇头 ──
        # 后续通过 UNFOLDING 状态逐步拉长身体
        self.body: list[tuple[int, int]] = [head_pos]

        # ── 方向管理 ──
        self.current_direction: tuple[int, int] = direction
        self.next_direction: tuple[int, int] = direction

        # ── 出生/生命周期状态 ──
        self.spawn_state: SpawnState = SpawnState.UNFOLDING
        self.unfold_remaining: int = target_length - 1  # 还需展开的步数

        # ── 移动计时器（独立于玩家的MOVE_INTERVAL）──
        self._move_accumulator: int = 0

        # ── 是否在本轮移动中吃到了道具 ──
        self.just_ate: bool = False

        # ── AI导航状态（后续阶段接入）──
        self._ai_direction_cooldown: int = 0   # 方向变更冷却（帧计数）
        self._target_item_pos: Optional[tuple[int, int]] = None  # 贪心目标道具位置

    # ── 属性 ──

    @property
    def is_alive(self) -> bool:
        return self.spawn_state not in (SpawnState.DEAD, SpawnState.DESPAWNING)

    @property
    def is_unfolding(self) -> bool:
        return self.spawn_state == SpawnState.UNFOLDING

    @property
    def is_active(self) -> bool:
        return self.spawn_state == SpawnState.ACTIVE

    @property
    def head(self) -> tuple[int, int]:
        return self.body[0]

    @property
    def length(self) -> int:
        return len(self.body)

    @property
    def move_interval_ms(self) -> int:
        return self.npc_type.move_interval_ms

    # ── 方向控制（AI调用） ──

    def set_direction(self, dx: int, dy: int):
        """
        尝试设置下一步方向。
        自动忽略反向指令（防止穿模）。
        """
        if (dx, dy) == (-self.current_direction[0], -self.current_direction[1]):
            return
        self.next_direction = (dx, dy)

    # ── 移动逻辑 ──

    def move(self) -> tuple[int, int]:
        """
        执行一步移动。
        UNFOLDING 状态下不截断尾部，实现渐进式展开。
        返回新的蛇头坐标。
        """
        # 1. 正式应用方向
        self.current_direction = self.next_direction

        # 2. 计算新蛇头
        head = self.body[0]
        new_head = (
            head[0] + self.current_direction[0],
            head[1] + self.current_direction[1],
        )

        # 3. 插入新头
        self.body.insert(0, new_head)

        # 4. 渐进式展开：UNFOLDING 状态下不截尾
        if self.spawn_state == SpawnState.UNFOLDING:
            self.unfold_remaining -= 1
            if self.unfold_remaining <= 0:
                self.spawn_state = SpawnState.ACTIVE
        elif not self.just_ate:
            # ACTIVE 状态正常截尾
            self.body.pop()
        else:
            self.just_ate = False

        return new_head

    def kill(self):
        """标记为死亡"""
        self.spawn_state = SpawnState.DEAD

    # ── 碰撞检测 ──

    def check_self_collision(self) -> bool:
        """检测蛇头是否撞到自身"""
        head = self.body[0]
        return head in self.body[1:]

    def occupies(self, pos: tuple[int, int]) -> bool:
        """检查指定网格坐标是否被蛇身占据"""
        return pos in self.body

    def check_head_collision_with(self, other: NPCSnake) -> bool:
        """检测本蛇头是否与另一条蛇的身体碰撞（含头部对撞）"""
        return self.head in other.body

    # ── 预判 ──

    def predict_next_head(self) -> tuple[int, int]:
        """预判下一步蛇头位置（不实际移动）"""
        head = self.body[0]
        return (
            head[0] + self.next_direction[0],
            head[1] + self.next_direction[1],
        )

    # ── 坐标转换 ──

    @staticmethod
    def grid_to_pixel(grid_x: int, grid_y: int) -> tuple[int, int]:
        """网格坐标 → 像素坐标（格子左上角）"""
        pixel_x = MARGIN_LEFT + grid_x * CELL_SIZE
        pixel_y = MARGIN_TOP + grid_y * CELL_SIZE
        return pixel_x, pixel_y

    # ── 渲染 ──

    def draw(self, screen: pygame.Surface):
        """
        绘制NPC蛇身。
        与玩家蛇使用相同的邻居感知算法，使用NPC类型定义的独立颜色。
        """
        body_set = set(self.body)
        fill_color = self.npc_type.color
        border_color = self.npc_type.border_color

        for x, y in self.body:
            px, py = self.grid_to_pixel(x, y)
            rect = pygame.Rect(px - 1, py - 1, CELL_SIZE + 2, CELL_SIZE + 2)

            # 填充蛇身
            pygame.draw.rect(screen, fill_color, rect)

            # 检查四个方向是否有相邻蛇身
            has_up = (x, y - 1) in body_set
            has_down = (x, y + 1) in body_set
            has_left = (x - 1, y) in body_set
            has_right = (x + 1, y) in body_set

            tl = rect.topleft
            tr = rect.topright
            br = rect.bottomright
            bl = rect.bottomleft

            if not has_up:
                pygame.draw.line(screen, border_color, tl, tr, SNAKE_BORDER_WIDTH)
            if not has_down:
                pygame.draw.line(screen, border_color, bl, br, SNAKE_BORDER_WIDTH)
            if not has_left:
                pygame.draw.line(screen, border_color, tl, bl, SNAKE_BORDER_WIDTH)
            if not has_right:
                pygame.draw.line(screen, border_color, tr, br, SNAKE_BORDER_WIDTH)

    # ── repr ──

    def __repr__(self) -> str:
        return (f"<NPCSnake {self.npc_type.npc_id} "
                f"len={self.length}/{self.target_length} "
                f"state={self.spawn_state.name} "
                f"head={self.head}>")
