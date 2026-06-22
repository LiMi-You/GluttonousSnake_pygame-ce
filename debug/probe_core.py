"""
debug/probe_core.py — 探针数据收集核心

职责：
1. 维护各模块的数据回调注册表
2. 每帧收集所有注册的数据快照
3. 记录碰撞事件历史（环形缓冲）
4. 暴露只读快照给 ProbePanel 消费
"""
from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class CollisionEvent:
    tick: int
    subject: str
    target: str
    pos: tuple[int, int]


class DebugProbe:
    """调试探针核心 — 数据收集与快照"""

    COLLISION_HISTORY_MAX = 30

    def __init__(self):
        self.enabled: bool = True
        self._collectors: dict[str, Callable[[], dict]] = {}
        self._snapshot: dict[str, Any] = {}
        self._collision_history: deque[CollisionEvent] = deque(
            maxlen=self.COLLISION_HISTORY_MAX
        )
        self._tick: int = 0

        # 性能计数
        self._frame_times: deque[float] = deque(maxlen=120)
        self._last_frame_time: float = time.perf_counter()

    # ── 注册 ──

    def register(self, key: str, collector: Callable[[], dict]):
        """注册一个数据收集回调。key 为分区名（如 'snake', 'npcs'）。"""
        self._collectors[key] = collector

    # ── 碰撞事件 ──

    def record_collision(self, subject: str, target: str, pos: tuple[int, int]):
        """记录一次碰撞事件"""
        self._collision_history.append(
            CollisionEvent(tick=self._tick, subject=subject, target=target, pos=pos)
        )

    # ── 帧驱动 ──

    def tick(self):
        """每帧调用一次，刷新性能计数和数据快照"""
        self._tick += 1

        now = time.perf_counter()
        self._frame_times.append(now - self._last_frame_time)
        self._last_frame_time = now

        # 收集所有注册模块的数据
        snapshot: dict[str, Any] = {}
        for key, collector in self._collectors.items():
            try:
                snapshot[key] = collector()
            except Exception as e:
                snapshot[key] = {"error": str(e)}
        self._snapshot = snapshot

    # ── 读取 ──

    def get_snapshot(self) -> dict[str, Any]:
        """返回当前帧的数据快照"""
        return self._snapshot

    def get_fps(self) -> float:
        """计算当前 FPS"""
        if len(self._frame_times) < 2:
            return 0.0
        avg = sum(self._frame_times) / len(self._frame_times)
        return 1.0 / avg if avg > 0 else 0.0

    def get_frame_ms(self) -> float:
        """最近一帧耗时（毫秒）"""
        if not self._frame_times:
            return 0.0
        return self._frame_times[-1] * 1000.0

    def get_collision_history(self) -> list[CollisionEvent]:
        """最近碰撞事件列表（最新在后）"""
        return list(self._collision_history)

    @property
    def tick_count(self) -> int:
        return self._tick
