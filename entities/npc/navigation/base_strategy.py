"""
entities/npc/navigation/base_strategy.py — 导航策略抽象基类

所有NPC导航策略必须实现此接口。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from entities.npc.collision_manager import CollisionManager
    from entities.npc.npc_base import NPCSnake
    from items.item_base import ItemInstance


@dataclass
class NavContext:
    """导航决策上下文（每步传入策略）"""
    snake: 'NPCSnake'                                        # 当前NPC蛇
    collision_mgr: 'CollisionManager'                        # 碰撞管理器
    player_head: Optional[tuple[int, int]] = None            # 玩家蛇头位置
    items: list['ItemInstance'] = field(default_factory=list)  # 场上道具列表
    grid_width: int = 29
    grid_height: int = 25


class NavigationStrategy(ABC):
    """导航策略抽象基类"""

    @abstractmethod
    def next_direction(self, ctx: NavContext) -> tuple[int, int]:
        """
        根据游戏上下文计算下一步移动方向。

        参数：
            ctx: 导航上下文，包含蛇状态、碰撞地图、目标信息等

        返回：
            下一步的 (dx, dy) 方向向量
        """
        ...

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """策略名称（用于调试）"""
        ...
