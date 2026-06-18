"""
entities/npc/npc_types.py — NPC蛇类型定义

集中管理所有NPC蛇类型的数据配置。
每种类型定义了颜色、长度范围、掉落行为、拾取行为、导航策略等。
"""
from dataclasses import dataclass
from enum import Enum, auto


# ── 导航策略枚举 ────────────────────────────────────
class NavStrategy(Enum):
    RANDOM_WALK = auto()       # 随机漫步 + 障碍规避
    GREEDY_ITEM = auto()       # 贪心道具采集
    HYBRID = auto()            # 混合：大部分随机 + 偶尔贪心
    CHASE_PLAYER = auto()      # A*追击玩家
    WANDER = auto()            # 大范围游走 + 边界反弹


# ── 出生状态枚举 ────────────────────────────────────
class SpawnState(Enum):
    """NPC蛇的出生/生命周期状态"""
    UNFOLDING = auto()         # 渐进式展开中（身体正在从出生点拉长）
    ACTIVE = auto()            # 正常活动
    DEAD = auto()              # 已死亡，等待清理
    DESPAWNING = auto()        # 正在消失（播放死亡动画/掉落道具）


# ── NPC类型配置 ────────────────────────────────────
@dataclass
class NPCTypeDef:
    """NPC蛇类型定义（不可变配置）"""
    npc_id: str                              # 唯一标识符
    name: str                                # 显示名称
    color: tuple[int, int, int]              # 蛇身颜色 RGB
    min_length: int                          # 随机长度下限
    max_length: int                          # 随机长度上限
    has_drops: bool = False                  # 死亡时是否掉落道具
    drop_count: int = 0                      # 基础掉落数量
    can_pickup: bool = False                 # 是否能拾取道具
    pickup_chance: float = 0.0               # 拾取概率（0.0~1.0，每步检测）
    nav_strategy: NavStrategy = NavStrategy.RANDOM_WALK
    move_interval_ms: int = 150              # 移动间隔（毫秒），默认与玩家一致
    border_color: tuple[int, int, int] = (0, 0, 0)  # 边框颜色


# ── NPC类型注册表 ──────────────────────────────────
# 颜色值来源: 用户提供的十六进制色表

NPC_TYPE_DEFS: dict[str, NPCTypeDef] = {
    "standard": NPCTypeDef(
        npc_id="standard",
        name="标准蛇",
        color=(0x71, 0x48, 0xFF),        # #7148ff
        min_length=3,
        max_length=6,
        has_drops=False,
        can_pickup=False,
        nav_strategy=NavStrategy.RANDOM_WALK,
        border_color=(0x50, 0x30, 0xC0),
    ),
    "foraging": NPCTypeDef(
        npc_id="foraging",
        name="觅食蛇",
        color=(0xFE, 0x22, 0xFF),        # #fe22ff
        min_length=15,
        max_length=15,
        has_drops=True,
        drop_count=3,
        can_pickup=True,
        pickup_chance=0.6,
        nav_strategy=NavStrategy.GREEDY_ITEM,
        border_color=(0xC0, 0x10, 0xC0),
    ),
    "loot": NPCTypeDef(
        npc_id="loot",
        name="战利品蛇",
        color=(0x22, 0x23, 0x3E),        # #22233e
        min_length=25,
        max_length=40,
        has_drops=True,
        drop_count=6,
        can_pickup=True,
        pickup_chance=0.15,               # 偶尔拾取
        nav_strategy=NavStrategy.HYBRID,
        border_color=(0x40, 0x40, 0x60),
    ),
    "mythic": NPCTypeDef(
        npc_id="mythic",
        name="神话蛇",
        color=(0xBA, 0xFF, 0xFE),        # #bafffe
        min_length=35,
        max_length=50,
        has_drops=True,
        drop_count=10,                     # 极多掉落
        can_pickup=False,
        nav_strategy=NavStrategy.WANDER,
        border_color=(0x80, 0xDD, 0xDC),
    ),
    "hunter": NPCTypeDef(
        npc_id="hunter",
        name="猎手蛇",
        color=(0xFF, 0x1C, 0x50),        # #ff1c50
        min_length=25,
        max_length=25,
        has_drops=True,
        drop_count=5,
        can_pickup=False,
        nav_strategy=NavStrategy.CHASE_PLAYER,
        border_color=(0xD0, 0x10, 0x30),
    ),
}


def get_npc_type_def(npc_id: str) -> NPCTypeDef:
    """安全获取NPC类型定义"""
    if npc_id not in NPC_TYPE_DEFS:
        raise ValueError(f"未注册的NPC类型 ID: {npc_id}")
    return NPC_TYPE_DEFS[npc_id]


def get_all_npc_type_ids() -> list[str]:
    """返回所有已注册NPC类型 ID 列表"""
    return list(NPC_TYPE_DEFS.keys())
