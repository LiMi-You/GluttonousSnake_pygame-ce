"""
items/event_bus.py — 事件总线

管理游戏中的瞬时事件和状态锁。
主要用于清场等多事件同时触发的场景，确保时序正确。
"""


class EventBus:
    """
    事件总线 — 管理游戏状态锁和待处理事件。

    核心职责：
    1. 清场锁：防止清场期间生成新道具
    2. 待处理队列：蛇增长、分数等延迟执行的事件
    """

    def __init__(self):
        self.clearing: bool = False       # 清场锁：为True时禁止道具生成
        self.pending_growth: int = 0      # 待增长节数
        self.pending_score: int = 0       # 待加分数
        self._clearing_just_finished: bool = False  # 刚完成清场标记

    def reset(self):
        self.clearing = False
        self.pending_growth = 0
        self.pending_score = 0
        self._clearing_just_finished = False

    def start_clear(self):
        """开始清场"""
        self.clearing = True
        self._clearing_just_finished = False

    def finish_clear(self, score: int, growth: int):
        """完成清场，记录奖励"""
        self.clearing = False
        self.pending_score += score
        self.pending_growth += growth
        self._clearing_just_finished = True

    def can_spawn_items(self) -> bool:
        """检查是否可以生成新道具"""
        return not self.clearing

    def consume_growth(self) -> bool:
        """
        消耗一节待增长。
        返回True表示有待增长，False表示已增长完毕。
        """
        if self.pending_growth > 0:
            self.pending_growth -= 1
            return True
        return False

    def consume_score(self) -> int:
        """
        消耗待加分数。
        返回应加的分数值（一次性取完）。
        """
        score = self.pending_score
        self.pending_score = 0
        return score

    def was_clearing_just_finished(self) -> bool:
        """检查刚完成清场（用于触发分数动画）"""
        if self._clearing_just_finished:
            self._clearing_just_finished = False
            return True
        return False
