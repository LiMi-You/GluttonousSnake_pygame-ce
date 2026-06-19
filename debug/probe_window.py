"""
debug/probe_window.py — 独立探针窗口

使用 pygame.Window 创建独立的调试探针窗口。
支持位置记忆、鼠标滚轮滚动、F1 开关。
"""
from __future__ import annotations
import pygame
from .probe_core import DebugProbe
from .probe_panel import ProbePanel

# ── 窗口配置 ──
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Debug Probe"
DEFAULT_OFFSET_X = 0
DEFAULT_OFFSET_Y = 50


class ProbeWindow:
    """独立探针窗口"""

    def __init__(self, game_surface: pygame.Surface, probe: DebugProbe):
        self.probe = probe
        self.enabled = False

        # 默认位置：游戏窗口右侧（使用操作系统绝对坐标）
        game_x, game_y = pygame.display.get_window_position()
        game_w, game_h = game_surface.get_size()
        self._default_x = game_x + game_w + DEFAULT_OFFSET_X
        self._default_y = game_y

        # 记忆位置（初始为默认位置）
        self._saved_x = self._default_x
        self._saved_y = self._default_y

        # 窗口和面板
        self._window: pygame.Window | None = None
        self._panel: ProbePanel | None = None

        # 刷新控制
        self._update_interval = 100
        self._last_update = 0

    def toggle(self):
        if self.enabled:
            self._close()
        else:
            self._open()

    def _open(self):
        if self._window is not None:
            return

        self._window = pygame.Window(
            size=(WINDOW_WIDTH, WINDOW_HEIGHT),
            title=WINDOW_TITLE,
            resizable=True,
        )
        # 使用上次关闭时的位置，或默认位置
        self._window.position = (self._saved_x, self._saved_y)

        surface = self._window.get_surface()
        self._panel = ProbePanel(surface.get_width(), surface.get_height(), self.probe)
        self.enabled = True

    def _close(self):
        if self._window:
            # 保存当前位置
            try:
                self._saved_x, self._saved_y = self._window.position
            except Exception:
                pass
            self._window.destroy()
            self._window = None
            self._panel = None
        self.enabled = False

    def handle_event(self, event: pygame.event.Event):
        if not self.enabled or not self._window:
            return

        if event.type == pygame.WINDOWCLOSE:
            if hasattr(event, 'window') and event.window == self._window:
                self._close()

        elif event.type == pygame.MOUSEWHEEL:
            if self._panel and hasattr(event, 'window') and event.window == self._window:
                self._panel.scroll(event.y * 30)

        elif event.type == pygame.WINDOWRESIZED:
            if self._panel and hasattr(event, 'window') and event.window == self._window:
                surface = self._window.get_surface()
                if surface:
                    w, h = surface.get_size()
                    self._panel.resize(w, h)

    def update(self, current_time: int):
        if not self.enabled or not self._window:
            return

        if current_time - self._last_update < self._update_interval:
            return
        self._last_update = current_time

        surface = self._window.get_surface()
        if not surface:
            return

        surface.fill((18, 18, 24))

        if self._panel:
            self._panel.draw(surface)

        self._window.flip()
