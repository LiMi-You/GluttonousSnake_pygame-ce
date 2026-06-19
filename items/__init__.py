"""
items/ — 道具系统包

提供道具定义、实例管理、生成与碰撞检测等完整功能。
"""
from .item_defs import ItemDef, ITEM_DEFS, get_item_def, get_all_item_ids
from .item_base import ItemInstance
from .item_manager import ItemManager
from .buff_manager import BuffManager

__all__ = [
    "ItemDef",
    "ITEM_DEFS",
    "get_item_def",
    "get_all_item_ids",
    "ItemInstance",
    "ItemManager",
    "BuffManager",
]

