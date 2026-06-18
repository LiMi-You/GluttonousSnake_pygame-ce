"""
entities/npc/collision_manager.py — 碰撞管理器

核心职责：
1. 每帧重建全局占据图（玩家 + NPC + 障碍物）
2. 提供单步碰撞预判（撞墙 / 撞玩家身 / 撞NPC身 / 头对头）
3. 为导航系统提供"某方向是否安全"的快速查询
"""
from __future__ import annotations
from enum import Enum, auto
from typing import Optional

from settings import GRID_WIDTH, GRID_HEIGHT


class CollisionType(Enum):
    """碰撞类型"""
    SAFE = auto()                # 安全
    HIT_WALL = auto()            # 撞墙
    HIT_SELF = auto()            # 撞自身
    HIT_PLAYER_BODY = auto()     # 撞玩家身体
    HIT_NPC_BODY = auto()        # 撞NPC身体
    HIT_HEAD_TO_HEAD = auto()    # 头对头碰撞


class CollisionManager:
    """
    碰撞管理器 — 每帧调用 rebuild() 更新占据图，
    然后通过 check_cell / check_move 进行碰撞预判。
    """

    def __init__(self):
        # 占据图: (gx, gy) → "player" | "npc:{npc_id}" | "wall"
        self._occupancy: dict[tuple[int, int], str] = {}

    # ── 每帧重建 ──

    def rebuild(
        self,
        player_body: list[tuple[int, int]],
        npc_snakes: list,  # list of NPCSnake
        obstacles: Optional[set[tuple[int, int]]] = None,
    ):
        """
        每帧开始时调用，重建全局占据图。
        参数 npc_snakes 为 NPCSnake 实例列表。
        """
        self._occupancy.clear()

        # 玩家蛇身
        for cell in player_body:
            if self._in_bounds(cell):
                self._occupancy[cell] = "player"

        # NPC蛇身
        for npc in npc_snakes:
            if not npc.is_alive:
                continue
            tag = f"npc:{npc.npc_type.npc_id}"
            for cell in npc.body:
                if self._in_bounds(cell):
                    self._occupancy[cell] = tag

        # 障碍物
        if obstacles:
            for cell in obstacles:
                if self._in_bounds(cell):
                    self._occupancy[cell] = "obstacle"

    # ── 快速查询 ──

    def is_occupied(self, gx: int, gy: int) -> bool:
        """坐标是否被占据（含越界）"""
        if not self._in_bounds((gx, gy)):
            return True  # 越界视为被占据（撞墙）
        return (gx, gy) in self._occupancy

    def is_free(self, gx: int, gy: int) -> bool:
        """坐标是否空闲（在界内且未被占据）"""
        return (self._in_bounds((gx, gy)) and
                (gx, gy) not in self._occupancy)

    def get_occupant(self, gx: int, gy: int) -> Optional[str]:
        """获取占据者标签"""
        if not self._in_bounds((gx, gy)):
            return "wall"
        return self._occupancy.get((gx, gy))

    # ── 单步碰撞预判 ──

    def check_move(
        self,
        head: tuple[int, int],
        body: list[tuple[int, int]],
        direction: tuple[int, int],
        *,
        exclude_tail: bool = True,
        self_tag: Optional[str] = None,
    ) -> CollisionType:
        """
        预判沿 direction 移动一步后的碰撞类型。

        参数：
            head:         当前蛇头坐标
            body:         当前蛇身（用于排除自身）
            direction:    移动方向
            exclude_tail: 是否在判断时排除自身尾部（正常移动时尾部会释放）
            self_tag:     自身在占据图中的标签（如 "player" 或 "npc:standard"）

        返回 CollisionType。
        """
        new_head = (head[0] + direction[0], head[1] + direction[1])

        # 撞墙
        if not self._in_bounds(new_head):
            return CollisionType.HIT_WALL

        # 撞自身（排除尾部）
        check_body = body[1:] if exclude_tail else body[1:-1]
        if new_head in check_body:
            return CollisionType.HIT_SELF

        # 撞占据图中的其他实体
        occupant = self._occupancy.get(new_head)
        if occupant is None:
            return CollisionType.SAFE
        if self_tag and occupant == self_tag:
            # 自身在占据图中的标记（可能因为不排除尾部导致）
            return CollisionType.SAFE

        if occupant == "player":
            return CollisionType.HIT_PLAYER_BODY
        if occupant and occupant.startswith("npc:"):
            return CollisionType.HIT_NPC_BODY
        if occupant == "obstacle":
            return CollisionType.HIT_WALL  # 障碍物等同于撞墙

        return CollisionType.SAFE

    def check_cell(
        self,
        gx: int, gy: int,
        *,
        self_body: Optional[list[tuple[int, int]]] = None,
        exclude_tail: bool = True,
    ) -> CollisionType:
        """
        检查指定网格坐标的碰撞情况。
        """
        if not self._in_bounds((gx, gy)):
            return CollisionType.HIT_WALL

        occupant = self._occupancy.get((gx, gy))
        if occupant is None:
            return CollisionType.SAFE

        # 排除自身
        if self_body and (gx, gy) in self_body:
            if exclude_tail and (gx, gy) == self_body[-1]:
                return CollisionType.SAFE
            if (gx, gy) == self_body[0]:
                return CollisionType.SAFE

        if occupant == "player":
            return CollisionType.HIT_PLAYER_BODY
        if occupant and occupant.startswith("npc:"):
            return CollisionType.HIT_NPC_BODY

        return CollisionType.SAFE

    # ── 安全方向列表 ──

    def get_safe_directions(
        self,
        head: tuple[int, int],
        body: list[tuple[int, int]],
        current_dir: tuple[int, int],
        *,
        self_tag: Optional[str] = None,
    ) -> list[tuple[int, int]]:
        """
        返回所有安全的移动方向列表（排除会导致碰撞的方向）。
        按优先级排列：当前方向 > 左右偏转 > 反向。
        """
        all_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        safe = []

        for d in all_dirs:
            # 跳过反向
            if d == (-current_dir[0], -current_dir[1]):
                continue
            result = self.check_move(head, body, d, self_tag=self_tag)
            if result == CollisionType.SAFE:
                safe.append(d)

        # 如果安全列表为空，加入反向作为最后手段
        if not safe:
            reverse = (-current_dir[0], -current_dir[1])
            safe.append(reverse)

        return safe

    # ── 工具 ──

    @staticmethod
    def _in_bounds(pos: tuple[int, int]) -> bool:
        gx, gy = pos
        return 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT

    def debug_dump(self) -> str:
        """调试：打印占据图概况"""
        player_cells = sum(1 for v in self._occupancy.values() if v == "player")
        npc_cells = sum(1 for v in self._occupancy.values() if v.startswith("npc:"))
        return (f"CollisionMap: {len(self._occupancy)} occupied "
                f"(player={player_cells}, npc={npc_cells})")
