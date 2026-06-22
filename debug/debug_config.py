"""
debug/debug_config.py — 调试配置持久化

将调试面板的所有可调参数保存到 JSON 文件，
下次启动时自动恢复上次的值。
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any


CONFIG_PATH = "debug_config.json"


@dataclass
class PlayerConfig:
    """玩家控制配置"""
    move_interval: int = 130
    invincible: bool = False
    god_mode: bool = False
    auto_play: bool = False
    speed_multiplier: float = 1.0


@dataclass
class NpcConfig:
    """NPC 控制配置"""
    spawn_enabled: bool = True
    initial_spawn_count: int = 2
    spawn_interval_min: int = 8000
    spawn_interval_max: int = 15000
    max_npcs: int = 8
    frozen: bool = False
    speed_multiplier: float = 1.0
    spawn_pool: dict[str, int] = field(default_factory=lambda: {
        "standard": 40, "foraging": 25, "loot": 15, "mythic": 5, "hunter": 15,
    })


@dataclass
class ItemConfig:
    """道具生成配置"""
    spawn_interval: int = 2000
    max_on_screen: int = 100
    initial_spawn_count: int = 3
    move_base_speed: float = 0.03
    # 每类型权重覆盖 {item_id: weight}，空 dict 表示全部用默认值
    weight_overrides: dict[str, int] = field(default_factory=dict)
    # 每类型启用开关 {item_id: bool}，空 dict 表示全部启用
    enabled_overrides: dict[str, bool] = field(default_factory=dict)


@dataclass
class PhaseConfig:
    """难度阶段配置"""
    # 前期
    early_max_score: int = 100000
    early_categories: list[str] = field(default_factory=lambda: ["basic", "lucky"])
    # 中期
    mid_min_score: int = 100000
    mid_categories: list[str] = field(default_factory=lambda: ["basic", "lucky", "buff", "debuff", "obstacle"])
    # 后期
    late_min_length: int = 20
    late_categories: list[str] = field(default_factory=lambda: ["basic", "lucky", "buff", "debuff", "obstacle"])
    late_obstacle_mult: float = 1.5
    late_debuff_mult: float = 1.3


@dataclass
class WeightConfig:
    """权重公式系数"""
    length_obstacle_coeff: float = 0.05    # 障碍物蛇长系数
    length_debuff_coeff: float = 0.05      # 减益蛇长系数
    length_lucky_coeff: float = -0.02      # 幸运蛇长系数
    score_suppress_factor: float = 0.1     # 分数阈值前压制倍率


@dataclass
class BuffConfig:
    """Buff 持续时间配置"""
    speed_boost_duration: int = 5000
    slow_down_duration: int = 10000
    clear_mode_duration: int = 5000


@dataclass
class DisplayConfig:
    """显示配置"""
    show_grid: bool = True
    show_debug_probe: bool = True


@dataclass
class DebugConfig:
    """调试配置总入口"""
    player: PlayerConfig = field(default_factory=PlayerConfig)
    npc: NpcConfig = field(default_factory=NpcConfig)
    item: ItemConfig = field(default_factory=ItemConfig)
    phase: PhaseConfig = field(default_factory=PhaseConfig)
    weight: WeightConfig = field(default_factory=WeightConfig)
    buff: BuffConfig = field(default_factory=BuffConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)

    def save(self, path: str = CONFIG_PATH):
        """保存到 JSON 文件"""
        data = asdict(self)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str = CONFIG_PATH) -> 'DebugConfig':
        """从 JSON 文件加载，文件不存在则返回默认值"""
        if not os.path.exists(path):
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = cls()
            for section_name in ["player", "npc", "item", "phase", "weight", "buff", "display"]:
                if section_name in data:
                    section = getattr(config, section_name)
                    for k, v in data[section_name].items():
                        if hasattr(section, k):
                            setattr(section, k, v)
            return config
        except (json.JSONDecodeError, KeyError):
            return cls()
