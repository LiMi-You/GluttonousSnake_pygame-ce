"""
items/item_defs.py — 道具定义表

集中管理所有道具类型的数据配置。
当前只实现基础食物（score_boost），后续扩展在此添加。
"""
from dataclasses import dataclass


@dataclass
class ItemDef:
    """道具类型定义（不可变配置）"""
    item_id: str                         # 唯一标识符
    name: str                            # 显示名称
    grid_w: int                          # 占格宽度（网格单位）
    grid_h: int                          # 占格高度（网格单位）
    base_weight: int                     # 基础生成权重
    max_on_screen: int                   # 同时最大存在数量
    color: tuple[int, int, int]          # 颜色 RGB
    score_value: int = 1                 # 食用获得分数
    image_key: str = ""                  # 图片文件名（assets/images/ 下）


# ── 道具定义注册表 ──────────────────────────────────
# 当前只注册基础食物，后续扩展在此添加条目

ITEM_DEFS: dict[str, ItemDef] = {
    "score_boost": ItemDef(
        item_id="score_boost",
        name="普通食物",
        grid_w=1,
        grid_h=1,
        base_weight=100,        # 唯一类型，权重占比 100%
        max_on_screen=8,
        color=(255, 50, 50),
        score_value=1000,
        image_key="score_boost.png",
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
