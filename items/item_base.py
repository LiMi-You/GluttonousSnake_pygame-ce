"""
items/item_base.py — 道具实例基类

ItemInstance 表示在游戏网格上"存在"的一个具体道具。
"""
from __future__ import annotations
from .item_defs import ItemDef


class ItemInstance:
    """地图上的一个具体道具实例"""

    def __init__(self, item_def: ItemDef, grid_x: int, grid_y: int):
        self.defn: ItemDef = item_def
        self.grid_x: int = grid_x          # 占据区域的左上角网格 x
        self.grid_y: int = grid_y          # 占据区域的左上角网格 y
        self.picked: bool = False          # 是否已被拾取（防止重复触发）
        self.spawn_time: int = 0           # 生成时的 pygame ticks（由 ItemManager 设置）

    @property
    def item_id(self) -> str:
        return self.defn.item_id

    @property
    def occupied_cells(self) -> list[tuple[int, int]]:
        """返回该道具占据的所有网格坐标列表"""
        cells = []
        for dx in range(self.defn.grid_w):
            for dy in range(self.defn.grid_h):
                cells.append((self.grid_x + dx, self.grid_y + dy))
        return cells

    def contains(self, grid_x: int, grid_y: int) -> bool:
        """判断一个网格坐标是否落在此道具的占据范围内"""
        return (self.grid_x <= grid_x < self.grid_x + self.defn.grid_w and
                self.grid_y <= grid_y < self.grid_y + self.defn.grid_h)

    def __repr__(self) -> str:
        return f"<Item {self.defn.item_id} @({self.grid_x},{self.grid_y})>"
