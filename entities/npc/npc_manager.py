"""
entities/npc/npc_manager.py — NPC管理器（总控）

核心职责：
1. 管理所有活跃NPC蛇的生命周期（创建、更新、死亡、清理）
2. 协调碰撞管理器、出生管理器、导航策略
3. 每帧驱动NPC的AI决策和移动
4. 处理NPC拾取道具和死亡掉落
"""
from __future__ import annotations
import random
import pygame
from typing import Optional, TYPE_CHECKING

from settings import GRID_WIDTH, GRID_HEIGHT
from .npc_base import NPCSnake
from .npc_types import (
    NPCTypeDef, SpawnState, NavStrategy,
    NPC_TYPE_DEFS, get_npc_type_def,
)
from .spawn_manager import SpawnManager
from .collision_manager import CollisionManager, CollisionType
from .navigation import create_strategy, NavContext, NavigationStrategy

if TYPE_CHECKING:
    from items.item_manager import ItemManager


class NPCManager:
    """NPC管理器 — GameScreen 通过此类与NPC子系统交互"""

    def __init__(self, item_manager: Optional['ItemManager'] = None, event_bus=None):
        self.npcs: list[NPCSnake] = []
        self.spawn_mgr = SpawnManager()
        self.collision_mgr = CollisionManager()

        # 道具管理器引用（用于NPC拾取和死亡掉落）
        self.item_manager = item_manager

        # 事件总线引用（用于清场锁）
        self.event_bus = event_bus

        # ── 出生配置（实例变量，支持运行时修改）──
        self.spawn_enabled: bool = True           # NPC生成开关
        self.initial_spawn_count: int = 2         # 游戏开始时生成的NPC数量
        self.spawn_interval_min: int = 8000       # 最小出生间隔（毫秒）
        self.spawn_interval_max: int = 15000      # 最大出生间隔（毫秒）
        self.max_npcs: int = 8                    # 场上最大NPC数
        self.initial_spawn_types: list[str] = ["standard"]  # 初始生成的NPC类型

        # 周期性生成的NPC类型及其权重（可运行时调整）
        self.periodic_spawn_pool: dict[str, int] = {
            "standard": 40,
            "foraging": 25,
            "loot": 15,
            "mythic": 5,
            "hunter": 15,
        }

        # 出生计时器
        self._spawn_timer: int = 0
        self._next_spawn_interval: int = self._random_spawn_interval()

        # 为每种NPC类型缓存导航策略实例
        self._strategies: dict[str, NavigationStrategy] = {}

        # 已初始化标记
        self._initialized = False

        # 运行时控制
        self.frozen: bool = False                 # 冻结所有NPC移动
        self.speed_multiplier: float = 1.0        # 全局速度倍率

    # ── 生命周期 ──

    def reset(self):
        """游戏重置"""
        self.npcs.clear()
        self._spawn_timer = 0
        self._next_spawn_interval = self._random_spawn_interval()
        self._strategies.clear()
        self._initialized = False

    def init_spawn(self, player_body: list[tuple[int, int]]):
        """游戏开始时生成初始NPC"""
        if self._initialized:
            return
        self._initialized = True

        if not self.spawn_enabled:
            return

        for _ in range(self.initial_spawn_count):
            npc_type_id = random.choice(self.initial_spawn_types)
            self._try_spawn_npc(npc_type_id, player_body)

    # ── 帧更新 ──

    def update(
        self,
        player_body: list[tuple[int, int]],
        active_items: list,
        delta_ms: int,
        obstacles: Optional[set[tuple[int, int]]] = None,
    ):
        """
        每帧调用。

        参数：
            player_body:  玩家蛇身坐标列表
            active_items: 场上道具列表（ItemInstance）
            delta_ms:     帧间时间差（毫秒）
            obstacles:    障碍物占据的格子集合
        """
        # 1. 重建全局碰撞占据图
        self.collision_mgr.rebuild(player_body, self.npcs, obstacles)

        # 2. 周期性出生
        if self.spawn_enabled:
            self._spawn_timer += delta_ms
            if self._spawn_timer >= self._next_spawn_interval:
                self._spawn_timer = 0
                self._next_spawn_interval = self._random_spawn_interval()
                if len(self.npcs) < self.max_npcs:
                    npc_type_id = self._weighted_random_type()
                    if npc_type_id:
                        self._try_spawn_npc(npc_type_id, player_body)

        # 3. 更新每个NPC
        player_head = player_body[0] if player_body else None

        for npc in self.npcs:
            if not npc.is_alive:
                continue

            if self.frozen:
                continue

            # 累加独立计时器
            npc._move_accumulator += delta_ms
            interval = int(npc.move_interval_ms / self.speed_multiplier)

            while npc._move_accumulator >= interval:
                npc._move_accumulator -= interval
                self._step_npc(npc, player_body, active_items, player_head)

                if not npc.is_alive:
                    break

        # 4. 清理死亡NPC
        self._cleanup_dead()

    # ── NPC单步逻辑 ──

    def _step_npc(
        self,
        npc: NPCSnake,
        player_body: list[tuple[int, int]],
        active_items: list,
        player_head: Optional[tuple[int, int]],
    ):
        """执行一个NPC的一步移动"""
        # A. 获取AI方向
        direction = self._get_ai_direction(npc, player_head, active_items)

        # B. 设置方向
        npc.set_direction(*direction)

        # C. 预判碰撞
        self_tag = f"npc:{npc.npc_type.npc_id}"
        collision = self.collision_mgr.check_move(
            npc.head, npc.body, npc.next_direction,
            exclude_tail=not npc.is_unfolding,  # 展开中不排除尾部
            self_tag=self_tag,
        )

        if collision == CollisionType.SAFE:
            # D. 安全：执行移动
            old_tail = npc.body[-1] if not npc.is_unfolding else None
            npc.move()

            # E. 检测道具（仅具有拾取能力的NPC）
            if npc.npc_type.can_pickup and npc.is_active:
                self._check_npc_item_pickup(npc, active_items)

        elif collision == CollisionType.HIT_SELF:
            # 撞自身（不常见，但做兜底）
            npc.kill()

        else:
            # 撞墙 / 撞玩家身 / 撞其他NPC身 → 死亡
            npc.kill()

    # ── AI方向获取 ──

    def _get_ai_direction(
        self,
        npc: NPCSnake,
        player_head: Optional[tuple[int, int]],
        active_items: list,
    ) -> tuple[int, int]:
        """获取NPC的AI导航方向"""
        npc_id = npc.npc_type.npc_id

        # 缓存策略实例
        if npc_id not in self._strategies:
            self._strategies[npc_id] = create_strategy(npc.npc_type.nav_strategy)

        strategy = self._strategies[npc_id]

        ctx = NavContext(
            snake=npc,
            collision_mgr=self.collision_mgr,
            player_head=player_head,
            items=active_items,
            grid_width=GRID_WIDTH,
            grid_height=GRID_HEIGHT,
        )
        return strategy.next_direction(ctx)

    # ── NPC拾取道具 ──

    def _check_npc_item_pickup(self, npc: NPCSnake, active_items: list):
        """检测NPC蛇头是否拾取了道具"""
        if not self.item_manager:
            return
        head = npc.head
        for item in active_items:
            if item.picked:
                continue
            if item.contains(head[0], head[1]):
                npc.just_ate = True
                self.item_manager.remove_item(item)
                break

    # ── 出生逻辑 ──

    def _try_spawn_npc(
        self, npc_type_id: str, player_body: list[tuple[int, int]],
    ) -> Optional[NPCSnake]:
        """尝试生成一个NPC"""
        if len(self.npcs) >= self.max_npcs:
            return None

        try:
            npc_type = get_npc_type_def(npc_type_id)
        except ValueError:
            return None

        npc_bodies = [npc.body for npc in self.npcs if npc.is_alive]
        npc = self.spawn_mgr.try_spawn(npc_type, player_body, npc_bodies)
        if npc:
            self.npcs.append(npc)
        return npc

    # ── 死亡掉落 ──

    # 高掉落量阈值：超过此值的NPC掉落会混入稀有道具
    HIGH_DROP_THRESHOLD = 5

    def _handle_death_drops(self, npc: NPCSnake):
        """
        NPC死亡时掉落道具。

        掉落规则：
        - has_drops=False 的NPC不掉落
        - 低掉落量（≤5）：全部掉落 score_boost
        - 高掉落量（≥6）：每隔1个混入 lucky_patrol_food
        - 掉落位置沿蛇身均匀分布（循环取模），不重复
        - 掉落位置自动验证空闲（由 ItemManager._spawn_one 处理）
        """
        if not npc.npc_type.has_drops or not self.item_manager:
            return

        count = npc.npc_type.drop_count
        if count <= 0 or not npc.body:
            return

        # 构建占用集：玩家 + 其他存活NPC的身体
        occupied: set[tuple[int, int]] = set()
        # 注意：当前NPC即将被移除，不加入占用集
        for other in self.npcs:
            if other is not npc and other.is_alive:
                for cell in other.body:
                    occupied.add(cell)

        # 过滤出界内位置
        valid_body = [(x, y) for x, y in npc.body
                      if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT]
        if not valid_body:
            return

        # 沿蛇身均匀取掉落位置（避免重复）
        body_len = len(valid_body)
        used_positions: set[tuple[int, int]] = set()

        for i in range(count):
            # 沿蛇身均匀分布
            idx = int(i * body_len / count) % body_len
            pos = valid_body[idx]

            # 避免同一位置重复掉落
            if pos in used_positions:
                # 尝试相邻位置
                for offset in range(1, body_len):
                    alt_idx = (idx + offset) % body_len
                    alt_pos = valid_body[alt_idx]
                    if alt_pos not in used_positions:
                        pos = alt_pos
                        break

            used_positions.add(pos)

            # 选择掉落道具类型
            if count > self.HIGH_DROP_THRESHOLD and i % 2 == 1:
                item_id = "lucky_patrol_food"
            else:
                item_id = "score_boost"

            self.item_manager._spawn_one(item_id, forced_pos=pos, occupied_cells=occupied)

    # ── 清理 ──

    def _cleanup_dead(self):
        """清理死亡NPC，触发掉落"""
        alive = []
        for npc in self.npcs:
            if npc.spawn_state == SpawnState.DEAD:
                self._handle_death_drops(npc)
            else:
                alive.append(npc)
        self.npcs = alive

    # ── 渲染 ──

    def draw(self, screen: pygame.Surface):
        """绘制所有活跃NPC蛇"""
        for npc in self.npcs:
            if npc.is_alive:
                npc.draw(screen)

    # ── 工具 ──

    def _random_spawn_interval(self) -> int:
        return random.randint(self.spawn_interval_min, self.spawn_interval_max)

    def _weighted_random_type(self) -> Optional[str]:
        """按权重随机选择NPC类型"""
        pool = self.periodic_spawn_pool
        total = sum(pool.values())
        if total == 0:
            return None
        r = random.randint(1, total)
        cumulative = 0
        for npc_id, weight in pool.items():
            cumulative += weight
            if r <= cumulative:
                return npc_id
        return None

    @property
    def alive_count(self) -> int:
        return sum(1 for n in self.npcs if n.is_alive)

    @property
    def total_count(self) -> int:
        return len(self.npcs)

    # ── 调试控制接口 ──

    def debug_spawn(self, npc_type_id: str, player_body: list[tuple[int, int]]) -> bool:
        """手动生成指定类型的NPC（调试用）"""
        if len(self.npcs) >= self.max_npcs:
            return False
        npc = self._try_spawn_npc(npc_type_id, player_body)
        return npc is not None

    def debug_kill_all(self):
        """杀死所有NPC（调试用）"""
        for npc in self.npcs:
            if npc.is_alive:
                npc.kill()
