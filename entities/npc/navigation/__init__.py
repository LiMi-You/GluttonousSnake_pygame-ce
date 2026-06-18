"""
entities/npc/navigation/ — NPC导航子系统

提供可插拔的导航策略：
- RandomWalkStrategy  — 随机漫步（StandardSnake）
- GreedyItemStrategy  — 贪心道具（ForagingSnake）
- ChasePlayerStrategy — BFS追击玩家（HunterSnake）
- WanderStrategy      — 大范围游走（MythicSnake）
- HybridStrategy      — 混合模式（LootSnake）

ObstacleAvoidance 为共享组件，被各策略组合使用。
"""
from .base_strategy import NavigationStrategy, NavContext
from .obstacle_avoidance import ObstacleAvoidance
from .random_walk import RandomWalkStrategy
from .greedy_item import GreedyItemStrategy
from .chase_player import ChasePlayerStrategy
from .wander import WanderStrategy
from .hybrid import HybridStrategy
from ..npc_types import NavStrategy


def create_strategy(nav_type: NavStrategy) -> NavigationStrategy:
    """根据 NavStrategy 枚举创建对应的策略实例"""
    _mapping = {
        NavStrategy.RANDOM_WALK: RandomWalkStrategy,
        NavStrategy.GREEDY_ITEM: GreedyItemStrategy,
        NavStrategy.CHASE_PLAYER: ChasePlayerStrategy,
        NavStrategy.WANDER: WanderStrategy,
        NavStrategy.HYBRID: HybridStrategy,
    }
    cls = _mapping.get(nav_type)
    if cls is None:
        raise ValueError(f"未知的导航策略: {nav_type}")
    return cls()


__all__ = [
    "NavigationStrategy", "NavContext",
    "ObstacleAvoidance",
    "RandomWalkStrategy",
    "GreedyItemStrategy",
    "ChasePlayerStrategy",
    "WanderStrategy",
    "HybridStrategy",
    "create_strategy",
]
