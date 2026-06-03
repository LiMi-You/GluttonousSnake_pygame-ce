"""
items/item_manager.py — 道具管理器

核心职责（当前）：
1. 按时间间隔在空白位置生成基础食物
2. 维护场上现有道具实例列表
3. 提供蛇头碰撞检测

后续扩展：权重管理、多类型道具、动态调整等。
"""
import random
import pygame
from typing import Optional

from settings import (
    GRID_WIDTH, GRID_HEIGHT,
    ITEM_SPAWN_INTERVAL, ITEM_MAX_ON_SCREEN, ITEM_BASE_SPAWN_COUNT,
)
from .item_defs import ITEM_DEFS, get_item_def
from .item_base import ItemInstance


class ItemManager:
    """道具管理器 — 生成、碰撞"""

    def __init__(self):
        self.active_items: list[ItemInstance] = []
        self._spawn_accumulator: int = 0    # 生成计时累加器（毫秒）
        self.spawn_interval: int = ITEM_SPAWN_INTERVAL

    # ── 生命周期 ──

    def reset(self):
        """游戏重置时调用"""
        self.active_items.clear()
        self._spawn_accumulator = 0
        # 游戏开始时生成初始数量的道具
        self._spawn_initial_items()

    def _spawn_initial_items(self):
        """游戏开始时生成初始数量的基础食物"""
        for _ in range(ITEM_BASE_SPAWN_COUNT):
            self._spawn_one("score_boost")

    # ── 帧更新 ──

    def update(self, snake_body: list[tuple[int, int]], dt_ms: int):
        """
        每帧调用，驱动生成计时器。
        dt_ms: 帧间时间差（毫秒）
        """
        self._spawn_accumulator += dt_ms

        while self._spawn_accumulator >= self.spawn_interval:
            self._spawn_accumulator -= self.spawn_interval

            if len(self.active_items) < ITEM_MAX_ON_SCREEN:
                self._spawn_one("score_boost")

    # ── 生成逻辑 ──

    def _spawn_one(self, item_id: str):
        """生成一个指定类型的道具"""
        defn = get_item_def(item_id)

        # 检查上限
        count = sum(1 for item in self.active_items if item.item_id == item_id)
        if count >= defn.max_on_screen:
            return

        # 找空闲位置
        pos = self._find_valid_position(defn.grid_w, defn.grid_h, snake_body=[])
        if pos is None:
            return

        gx, gy = pos
        instance = ItemInstance(defn, gx, gy)
        instance.spawn_time = pygame.time.get_ticks()
        self.active_items.append(instance)

    def _find_valid_position(
        self,
        item_w: int,
        item_h: int,
        snake_body: list[tuple[int, int]],
    ) -> Optional[tuple[int, int]]:
        """
        找一个 (item_w × item_h) 的空白矩形区域。
        条件：不碰蛇身、不碰其他道具、不超出网格边界。
        """
        # 收集所有已被占据的格子
        occupied: set[tuple[int, int]] = set(snake_body)
        for item in self.active_items:
            for cell in item.occupied_cells:
                occupied.add(cell)

        max_attempts = 50
        for _ in range(max_attempts):
            gx = random.randint(0, GRID_WIDTH - item_w)
            gy = random.randint(0, GRID_HEIGHT - item_h)

            free = True
            for dx in range(item_w):
                for dy in range(item_h):
                    if (gx + dx, gy + dy) in occupied:
                        free = False
                        break
                if not free:
                    break

            if free:
                return (gx, gy)

        return None

    # ── 碰撞检测 ──

    def check_collision(self, head_pos: tuple[int, int]) -> Optional[ItemInstance]:
        """
        检测蛇头是否与某个道具碰撞。
        返回被碰撞的道具实例，无碰撞则返回 None。
        """
        for item in self.active_items:
            if item.picked:
                continue
            if item.contains(head_pos[0], head_pos[1]):
                item.picked = True
                return item
        return None

    # ── 移除道具 ──

    def remove_item(self, item: ItemInstance):
        """从场上移除一个道具"""
        if item in self.active_items:
            self.active_items.remove(item)
