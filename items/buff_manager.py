"""
items/buff_manager.py — Buff/Debuff 管理器

管理玩家身上的时效性状态（加速、减速、清场等）。
支持：添加、更新（倒计时）、过期移除、查询当前状态。
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Buff:
    """单个 Buff 实例"""
    buff_id: str
    duration_ms: int
    remaining_ms: int
    speed_mult: float
    clear_mode: bool = False  # 清场模式：可撞击NPC/障碍物/道具


class BuffManager:
    """
    Buff 管理器 — 追踪玩家身上的所有活跃 buff。

    速度类 buff 规则：
    - 同 ID buff 重复拾取 → 刷新持续时间（不叠加系数）
    - 加速/减速互斥 → 后拾取的覆盖先拾取的（取最后生效）
    """

    def __init__(self):
        self.active_buffs: list[Buff] = []

    def reset(self):
        self.active_buffs.clear()

    def add_buff(self, buff_id: str, duration_ms: int, speed_mult: float = 1.0,
                 clear_mode: bool = False):
        if speed_mult != 1.0:
            self.active_buffs = [
                b for b in self.active_buffs
                if b.speed_mult == 1.0
            ]

        existing = next((b for b in self.active_buffs if b.buff_id == buff_id), None)
        if existing:
            existing.remaining_ms = duration_ms
        else:
            self.active_buffs.append(
                Buff(
                    buff_id=buff_id,
                    duration_ms=duration_ms,
                    remaining_ms=duration_ms,
                    speed_mult=speed_mult,
                    clear_mode=clear_mode,
                )
            )

    def update(self, dt_ms: int):
        for buff in self.active_buffs:
            buff.remaining_ms -= dt_ms
        self.active_buffs = [b for b in self.active_buffs if b.remaining_ms > 0]

    def get_speed_multiplier(self) -> float:
        for buff in self.active_buffs:
            if buff.speed_mult != 1.0:
                return buff.speed_mult
        return 1.0

    def has_clear_mode(self) -> bool:
        """检查是否处于清场模式"""
        return any(b.clear_mode for b in self.active_buffs)

    def has_buff(self, buff_id: str) -> bool:
        return any(b.buff_id == buff_id for b in self.active_buffs)

    def get_active_buffs_info(self) -> list[dict]:
        return [
            {
                "id": b.buff_id,
                "remaining_ms": b.remaining_ms,
                "duration_ms": b.duration_ms,
                "speed_mult": b.speed_mult,
                "clear_mode": b.clear_mode,
            }
            for b in self.active_buffs
        ]
