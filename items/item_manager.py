"""
items/item_manager.py — 道具管理器

核心职责：
1. 基于动态权重系统在空白位置自动生成道具
2. 维护场上现有道具实例列表
3. 提供蛇头碰撞检测
4. 提供全场清理等扩展接口
"""
import random
import math
import pygame
from typing import Optional

from settings import (
    GRID_WIDTH, GRID_HEIGHT,
    ITEM_SPAWN_INTERVAL, ITEM_MAX_ON_SCREEN, ITEM_BASE_SPAWN_COUNT,
    PHASE_EARLY_MAX_SCORE,
    MOVE_ITEM_BASE_SPEED,
)
from .item_defs import ITEM_DEFS, get_item_def
from .item_base import ItemInstance
from .difficulty_phases import get_active_phases, get_allowed_categories, merge_multipliers, get_allowed_item_ids
from .weight_calculator import build_weight_table, pick_item_by_weight
from utils.helpers import get_random_direction, get_new_direction, is_within_range


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

    def update(
        self,
        snake_body: list[tuple[int, int]],
        dt_ms: int,
        score: int = 0,
        snake_length: int = 3,
    ):
        """
        每帧调用，驱动生成计时器。
        
        参数：
            snake_body: 蛇身坐标列表（用于空闲位置检测）
            dt_ms:      帧间时间差（毫秒）
            score:      当前分数（用于阶段判断）
            snake_length: 当前蛇长（用于权重修正）
        """
        self._spawn_accumulator += dt_ms

        while self._spawn_accumulator >= self.spawn_interval:
            self._spawn_accumulator -= self.spawn_interval

            if len(self.active_items) < ITEM_MAX_ON_SCREEN:
                self._spawn_weighted(score, snake_length)

        # ── 更新可移动道具位置（每帧独立，不受蛇步频限制）──
        self._update_moving_items(dt_ms)

    # ── 生成逻辑 ──

    def _spawn_one(self, item_id: str, forced_pos: Optional[tuple[int, int]] = None):
        """
        生成一个指定类型的道具（强制生成，绕过权重系统）。
        
        用于 NPC 死亡掉落等事件驱动场景。
        forced_pos: 指定生成位置（None 则自动找空闲位）
        """
        defn = get_item_def(item_id)

        # 检查上限
        count = sum(1 for item in self.active_items if item.item_id == item_id)
        if count >= defn.max_on_screen:
            return

        if forced_pos is not None:
            gx, gy = forced_pos
        else:
            # 找空闲位置（可移动道具需额外保证移动范围不越界）
            mr = defn.move_range if defn.is_moving else 0
            pos = self._find_valid_position(defn.grid_w, defn.grid_h, snake_body=[], move_range=mr)
            if pos is None:
                return
            gx, gy = pos

        instance = ItemInstance(defn, gx, gy)
        instance.spawn_time = pygame.time.get_ticks()

        # ── 可移动道具：初始化随机方向 ──
        if defn.is_moving:
            direction, direction_idx = get_random_direction()
            instance.move_dir = direction
            instance.move_dir_idx = direction_idx
            instance.spawn_origin = (instance.fx, instance.fy)

        self.active_items.append(instance)

    def _spawn_weighted(self, score: int, snake_length: int):
        """
        基于动态权重系统选择一个道具类型并生成。
        这是常规生成的核心入口。
        """
        # 1. 确定当前激活的阶段
        active_phases = get_active_phases(score, snake_length)
        if not active_phases:
            # 没有任何阶段激活时，兜底生成基础食物
            self._spawn_one("score_boost")
            return

        # 2. 合并阶段的分类集合与倍率
        allowed_categories = get_allowed_categories(active_phases)
        merged_multipliers = merge_multipliers(active_phases)

        # 3. 获取允许的道具 ID 列表
        allowed_ids = get_allowed_item_ids(allowed_categories)
        if not allowed_ids:
            self._spawn_one("score_boost")
            return

        # 4. 统计场上各道具数量
        current_counts: dict[str, int] = {}
        for item in self.active_items:
            current_counts[item.item_id] = current_counts.get(item.item_id, 0) + 1

        # 5. 构建权重表并选择
        weight_table = build_weight_table(
            allowed_item_ids=allowed_ids,
            snake_length=snake_length,
            score=score,
            current_counts=current_counts,
            phase_multipliers=merged_multipliers,
            early_max_score=PHASE_EARLY_MAX_SCORE,
            item_defs=ITEM_DEFS,
        )

        chosen_id = pick_item_by_weight(weight_table)
        if chosen_id is None:
            # 权重表为空时兜底
            self._spawn_one("score_boost")
            return

        # 6. 生成选中的道具
        self._spawn_one(chosen_id)

    # ── 移动道具更新 ──

    def _update_moving_items(self, dt_ms: int):
        """
        更新所有可移动道具的位置（每帧调用，独立于蛇步频）。
        
        移动逻辑：
        1. 按方向和速度更新小数格坐标 (fx, fy)
        2. 超出移动范围 → 随机换一个新方向
        3. 未来扩展：move_bounce=True → 全场反弹
        """
        if dt_ms <= 0:
            return

        # 速度系数：以 25fps 为基准归一化
        fps_normal = dt_ms / (1000.0 / 25.0)

        for item in self.active_items:
            if not item.defn.is_moving or item.picked:
                continue

            # 每帧移动量（格）
            speed = item.defn.move_speed * MOVE_ITEM_BASE_SPEED * fps_normal

            dx, dy = item.move_dir
            item.fx += dx * speed
            item.fy += dy * speed

            # ── 范围限制：区域内移动（move_range > 0）──
            if item.defn.move_range > 0:
                if not is_within_range(
                    item.fx, item.fy,
                    item.spawn_origin[0], item.spawn_origin[1],
                    item.defn.move_range,
                ):
                    # 超出范围 → 随机换方向 + 拉回边界
                    new_dir, new_idx = get_new_direction(item.move_dir_idx)
                    item.move_dir = new_dir
                    item.move_dir_idx = new_idx
                    # 钳制到范围边界
                    half = item.defn.move_range / 2.0
                    item.fx = max(
                        item.spawn_origin[0] - half,
                        min(item.spawn_origin[0] + half, item.fx),
                    )
                    item.fy = max(
                        item.spawn_origin[1] - half,
                        min(item.spawn_origin[1] + half, item.fy),
                    )

            # ── 全场反弹（move_bounce=True，由未来 UniqueBouncingLuckyProp 使用）──
            if item.defn.move_bounce:
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

    # ── 空闲位置查找 ──

    def _find_valid_position(
        self,
        item_w: int,
        item_h: int,
        snake_body: list[tuple[int, int]],
        move_range: int = 0,
    ) -> Optional[tuple[int, int]]:
        """
        找一个 (item_w × item_h) 的空白矩形区域。
        条件：不碰蛇身、不碰其他道具、不超出网格边界。
        
        如果 move_range > 0，额外保证移动圆完全在地图内。
        """
        # 收集所有已被占据的格子
        occupied: set[tuple[int, int]] = set(snake_body)
        for item in self.active_items:
            for cell in item.occupied_cells:
                occupied.add(cell)

        # ── 计算安全生成范围 ──
        if move_range > 0:
            half = move_range / 2.0
            gx_min = max(0, math.ceil(half - item_w / 2.0))
            gx_max = min(
                GRID_WIDTH - item_w,
                int(GRID_WIDTH - half - item_w / 2.0 - 0.0001),
            )
            gy_min = max(0, math.ceil(half - item_h / 2.0))
            gy_max = min(
                GRID_HEIGHT - item_h,
                int(GRID_HEIGHT - half - item_h / 2.0 - 0.0001),
            )
        else:
            gx_min, gx_max = 0, GRID_WIDTH - item_w
            gy_min, gy_max = 0, GRID_HEIGHT - item_h

        # 安全检查：最小值不能大于最大值
        if gx_min > gx_max or gy_min > gy_max:
            return None

        max_attempts = 50
        for _ in range(max_attempts):
            gx = random.randint(gx_min, gx_max)
            gy = random.randint(gy_min, gy_max)

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

    def clear_all_items(self, exclude_ids: Optional[set[str]] = None):
        """
        清空场上所有道具（可选保留某些类型）。
        用于 LuckyClearBlock / UniqueBouncingLuckyProp 等清场效果。
        
        参数：
            exclude_ids: 保留的道具 ID 集合（不会被清除）
        """
        if exclude_ids:
            self.active_items = [
                item for item in self.active_items
                if item.item_id in exclude_ids
            ]
        else:
            self.active_items.clear()
