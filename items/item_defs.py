"""
items/item_defs.py — 道具定义表

集中管理所有道具类型的数据配置。
当前只实现基础食物（score_boost），后续扩展在此添加。
"""
from dataclasses import dataclass

# ── 道具分类常量 ────────────────────────────────────
CAT_BASIC    = "basic"      # 基础食物
CAT_LUCKY    = "lucky"      # 幸运/稀有类
CAT_BUFF     = "buff"       # 增益类（加速等）
CAT_DEBUFF   = "debuff"     # 减益类（减速等）
CAT_OBSTACLE = "obstacle"   # 障碍物类


@dataclass
class ItemDef:
    """道具类型定义（不可变配置）"""
    item_id: str                         # 唯一标识符
    name: str                            # 显示名称
    category: str = CAT_BASIC            # 分类标签
    grid_w: int = 1                      # 占格宽度（网格单位）
    grid_h: int = 1                      # 占格高度（网格单位）
    base_weight: int = 100               # 基础生成权重
    max_on_screen: int = 8               # 同时最大存在数量
    color: tuple[int, int, int] = (255, 255, 255)  # 颜色 RGB
    score_value: int = 1                 # 食用获得分数
    image_key: str = ""                  # 图片文件名（assets/images/ 下）
    # ── 可移动道具扩展 ──
    is_moving: bool = False              # 是否自动移动
    move_speed: int = 0                  # 移动基准速度（× 速度常量 = 每帧格数）
    move_range: int = 0                  # 移动范围（格子数，0=无限制/全场）
    move_bounce: bool = False            # 是否边界反弹（True=全场反弹, False=区域内随机转向）


# ── 道具定义注册表 ──────────────────────────────────
# 当前只注册基础食物，后续扩展在此添加条目

ITEM_DEFS: dict[str, ItemDef] = {
    "score_boost": ItemDef(
        item_id="score_boost",
        name="普通食物",
        category=CAT_BASIC,
        grid_w=1,
        grid_h=1,
        base_weight=100,
        max_on_screen=1,
        color=(255, 50, 50),
        score_value=1000,
        image_key="score_boost.png",
    ),
    "lucky_patrol_food": ItemDef(
        item_id="lucky_patrol_food",
        name="幸运食物",
        category=CAT_LUCKY,
        grid_w=1,
        grid_h=1,
        base_weight=15,
        max_on_screen=3,
        color=(255, 215, 0),
        score_value=5000,
        image_key="LuckyPatrolFoot.png",
        # ── 移动配置 ──
        is_moving=True,
        move_speed=1,           # 基准速度 1
        move_range=4,           # 4×4 格圆形区域内移动（half=2，边界安全）
        move_bounce=False,      # 范围内随机转向
    ),
}


def get_item_def(item_id: str) -> ItemDef:
    """安全获取道具定义"""
    if item_id not in ITEM_DEFS:
        raise ValueError(f"未注册的道具 ID: {item_id}")
    return ITEM_DEFS[item_id]


def get_all_item_ids() -> list[str]:
    """返回所有已注册道具 ID 列表"""
    return list(ITEM_DEFS.keys())
