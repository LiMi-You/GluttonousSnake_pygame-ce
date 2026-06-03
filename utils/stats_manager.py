"""
utils/stats_manager.py — 游戏统计管理器

所有可量化的游戏数据集中在此管理。
GameScreen 负责写入，未来的 UI/音效/结算模块通过只读接口查询。
"""
import pygame


class StatsManager:
    """游戏统计管理 — 单一数据源"""

    def __init__(self):
        self.reset()

    def reset(self):
        """新一局重置所有数据"""
        self.score: int = 0
        self.snake_length: int = 3
        self.items_collected: dict[str, int] = {}
        self.combo: int = 0
        self.max_combo: int = 0
        self._combo_deadline: int = 0       # 连击窗口过期时间戳
        self._start_time: int = 0           # pygame.time.get_ticks()

    # ── 写入接口（GameScreen 调用） ──

    def start_timer(self):
        """游戏开始时记录时间"""
        self._start_time = pygame.time.get_ticks()

    def add_score(self, base_points: int):
        """
        加分，自动应用蛇长倍率。
        倍率公式: 1.0 + (snake_length - 3) * 0.1
        蛇长 3 → ×1.0, 蛇长 8 → ×1.5, 蛇长 13 → ×2.0
        """
        length_mult = 1.0 + max(0, (self.snake_length - 3)) * 0.1
        self.score += int(base_points * length_mult)

    def on_item_collected(self, item_id: str):
        """
        记录一次道具收集，管理连击。
        连击规则：2 秒内连续吃到道具 → combo 递增，超时则重置为 1。
        """
        self.items_collected[item_id] = self.items_collected.get(item_id, 0) + 1

        now = pygame.time.get_ticks()
        if now < self._combo_deadline:
            self.combo += 1                  # 在窗口内 → 连击延续
        else:
            self.combo = 1                   # 超时 → 重新开始

        if self.combo > self.max_combo:
            self.max_combo = self.combo

        # 刷新窗口：下次吃到需在 2 秒内
        self._combo_deadline = now + 2000

    def set_snake_length(self, length: int):
        """蛇移动后同步当前蛇长"""
        self.snake_length = length

    # ── 只读查询接口（UI / 音效 / 结算调用） ──

    def get_score(self) -> int:
        return self.score

    def get_snake_length(self) -> int:
        return self.snake_length

    def get_combo(self) -> int:
        return self.combo

    def get_max_combo(self) -> int:
        return self.max_combo

    def get_item_count(self, item_id: str) -> int:
        """查询某种道具本局已收集次数"""
        return self.items_collected.get(item_id, 0)

    def get_play_time_ms(self) -> int:
        """已游玩毫秒数"""
        if self._start_time == 0:
            return 0
        return pygame.time.get_ticks() - self._start_time

    def get_all_stats(self) -> dict:
        """一次性返回所有数据，供结算/存档使用"""
        return {
            "score": self.score,
            "snake_length": self.snake_length,
            "combo": self.combo,
            "max_combo": self.max_combo,
            "items_collected": dict(self.items_collected),
            "play_time_ms": self.get_play_time_ms(),
        }
