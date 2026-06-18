"""
entities/npc/ — NPC蛇子系统

NPC蛇实体、类型配置、出生管理、碰撞管理、导航策略、NPC管理器。
"""
from .npc_base import NPCSnake
from .npc_types import (
    NPCTypeDef, SpawnState, NavStrategy,
    NPC_TYPE_DEFS, get_npc_type_def, get_all_npc_type_ids,
)
from .spawn_manager import SpawnManager
from .collision_manager import CollisionManager, CollisionType
from .npc_manager import NPCManager

__all__ = [
    "NPCSnake",
    "NPCTypeDef",
    "SpawnState",
    "NavStrategy",
    "NPC_TYPE_DEFS",
    "get_npc_type_def",
    "get_all_npc_type_ids",
    "SpawnManager",
    "CollisionManager",
    "CollisionType",
    "NPCManager",
]
