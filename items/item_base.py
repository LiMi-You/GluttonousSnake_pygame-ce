"""
items/item_base.py — 道具实例基类

ItemInstance 表示在游戏网格上"存在"的一个具体道具。
位置使用小数格坐标（fx, fy），grid_x/grid_y 为实时计算属性。
"""
from __future__ import annotations
from .item_defs import ItemDef


class ItemInstance:
    """地图上的一个具体道具实例"""

    def __init__(self, item_def: ItemDef, grid_x: int, grid_y: int):
        self.defn: ItemDef = item_def
        # ── 位置：小数格坐标（中心点），grid_x/grid_y 由此派生 ──
        self.fx: float = float(grid_x) + item_def.grid_w / 2.0
        self.fy: float = float(grid_y) + item_def.grid_h / 2.0
        self.picked: bool = False          # 是否已被拾取（防止重复触发）
        self.spawn_time: int = 0           # 生成时的 pygame ticks（由 ItemManager 设置）
        # ── 可移动道具状态 ──
        self.move_dir: tuple[float, float] = (0.0, 0.0)   # 当前移动方向单位向量
        self.move_dir_idx: int = -1                        # 方向索引（避免同向反弹）
        self.spawn_origin: tuple[float, float] = (self.fx, self.fy)  # 生成时的中心位置（用于范围判断）

    # ── 网格坐标（属性，由小数格坐标实时计算）──

    @property
    def grid_x(self) -> int:
        """道具占据区域的左上角网格 x"""
        return int(self.fx - self.defn.grid_w / 2.0)

    @property
    def grid_y(self) -> int:
        """道具占据区域的左上角网格 y"""
        return int(self.fy - self.defn.grid_h / 2.0)

    @property
    def item_id(self) -> str:
        return self.defn.item_id

    @property
    def occupied_cells(self) -> list[tuple[int, int]]:
        """返回该道具占据的所有网格坐标列表（由实时位置计算）"""
        cells = []
        gx = self.grid_x
        gy = self.grid_y
        for dx in range(self.defn.grid_w):
            for dy in range(self.defn.grid_h):
                cells.append((gx + dx, gy + dy))
        return cells

    def contains(self, grid_x: int, grid_y: int) -> bool:
        """判断一个网格坐标是否落在此道具的占据范围内"""
        return (self.grid_x <= grid_x < self.grid_x + self.defn.grid_w and
                self.grid_y <= grid_y < self.grid_y + self.defn.grid_h)

    def __repr__(self) -> str:
        return (f"<Item {self.defn.item_id} "
                f"f({self.fx:.1f},{self.fy:.1f}) g({self.grid_x},{self.grid_y})>")
